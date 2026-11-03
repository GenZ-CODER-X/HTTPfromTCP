from enum import Enum
from internals.requests.request import Request
from pydantic import BaseModel
from io import BytesIO
from http import HTTPStatus
from internals.headers.headers import Headers

class StatusCode(Enum):
    OK=200 
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR=500

class HandlerError(BaseModel):
    status_code:StatusCode
    message:str

class WriterState(Enum):
    INITIALIZED="initialized"
    STATUS_LINE_WRITTEN="written_status_line"
    HEADERS_WRITTEN = "written_headers"
    WRITING_BODY_CHUNKS="writing_body_chunks"
    DONE="done"

class Writer():
    def __init__(self,writer:BytesIO,http_version:str):
        self.writer = writer
        self.http_version = http_version
        self.state = WriterState.INITIALIZED
    
    def write_status_line(self,status_code:StatusCode)->None:
        if self.state != WriterState.INITIALIZED:
            raise RuntimeError("Status line must be written first")
        status = HTTPStatus(status_code.value)
        status_line=(
            f"HTTP/{self.http_version} "
            f"{status.value} "
            f"{status.phrase}"
        )
        self.writer.write((status_line + "\r\n").encode("utf-8"))
        self.state=WriterState.STATUS_LINE_WRITTEN

    def write_headers_line(self,headers:Headers)->None:
        if self.state != WriterState.STATUS_LINE_WRITTEN:
            raise RuntimeError("Write status line before headers")
        headers_list=[]
        for key,value in headers.headers.items():
            header = f"{key}: {value}\r\n"
            self.writer.write(header.encode("utf-8"))
        self.writer.write(b"\r\n")
        self.state=WriterState.HEADERS_WRITTEN
    
    def write_chunked_body(self,p:bytes)->int:
        if self.state not in( WriterState.HEADERS_WRITTEN,
                             WriterState.WRITING_BODY_CHUNKS):
            raise RuntimeError("Write headers before body")
        if not p:
            raise ValueError("Use write_chunked_body_done() for termination")
        hex_size = format(len(p),"x").encode("ascii")
        self.writer.write(hex_size + b"\r\n")
        written = self.writer.write(p)
        self.writer.write(b"\r\n")
        self.state = WriterState.WRITING_BODY_CHUNKS
        return written
    
    def write_chunked_body_done(self)->int:
        if self.state not in (
            WriterState.STATUS_LINE_WRITTEN,
            WriterState.WRITING_BODY_CHUNKS
        ):
            raise RuntimeError("Cannot finish chunked body in current state")
        terminator=b"0\r\n\r\n"
        written = self.writer.write(terminator)
        self.state=WriterState.DONE
        return written
def app_handler(writer:Writer,request:Request)->None:
    path=request.request_line.request_target
    if path == "/yourproblem":
        status = StatusCode.BAD_REQUEST
        body = b"""<html>
  <head>
    <title>400 Bad Request</title>
  </head>
  <body>
    <h1>Bad Request</h1>
    <p>Your request honestly kinda sucked.</p>
  </body>
</html>"""

    if path == "/myproblem":
        status = StatusCode.INTERNAL_SERVER_ERROR
        body = b"""<html>
  <head>
    <title>500 Internal Server Error</title>
  </head>
  <body>
    <h1>Internal Server Error</h1>
    <p>Okay, you know what? This one is on me.</p>
  </body>
</html>"""
    else:
        status = StatusCode.OK
        body = b"""<html>
  <head>
    <title>200 OK</title>
  </head>
  <body>
    <h1>Success!</h1>
    <p>Your request was an absolute banger.</p>
  </body>
</html>"""
    headers = Headers()
    headers.headers["Content-Type"] = "text/html"
    headers.headers["Transfer-Encoding"] = "chunked"
    writer.write_status_line(status)
    writer.write_headers_line(headers)
    # Split HTML body into smaller chunks
    chunk_size = 32
    for i in range(0, len(body), chunk_size):
        chunk = body[i:i + chunk_size]
        writer.write_chunked_body(chunk)
    
    writer.write_chunked_body_done()


#  HTTP-message   = start-line CRLF
#                   *( field-line CRLF )
#                   CRLF
#                   [ message-body ]
# status-line = HTTP-version SP status-code SP [ reason-phrase ]
# For example:

# HTTP/1.1 200 OK

# Or perhaps:

# HTTP/1.1 404 Not Found