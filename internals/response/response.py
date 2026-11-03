from enum import Enum
from internals.requests.request import Request
from pydantic import BaseModel
from io import BytesIO
from http import HTTPStatus
from internals.headers.headers import Headers
import hashlib
from pathlib import Path

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
    WRITING_TRAILERS="writing_trailers"
    DONE="done"

class Writer():
    def __init__(self,writer:BytesIO,http_version:str):
        self.writer = writer
        self.http_version = http_version
        self.body_length = int
        self.state = WriterState.INITIALIZED
    def _write_header_fields(self, headers: Headers) -> None:
        for key, value in headers.headers.items():
            header = f"{key}: {value}\r\n"
            self.writer.write(header.encode("utf-8"))
        
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

    def write_headers_line(self, headers: Headers) -> None:
        if self.state != WriterState.STATUS_LINE_WRITTEN:
            raise RuntimeError("Write status line before headers")

        self._write_header_fields(headers)
        self.writer.write(b"\r\n")

        self.state = WriterState.HEADERS_WRITTEN
    
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
        written = self.writer.write(b"0\r\n")
        self.state=WriterState.WRITING_TRAILERS
        return written
    
    def write_trailers(self, trailers: Headers) -> None:
        if self.state != WriterState.WRITING_TRAILERS:
            raise RuntimeError("Chunked body must finish before trailers")

        self._write_header_fields(trailers)
        self.writer.write(b"\r\n")
        self.state = WriterState.DONE
    
def app_handler(writer:Writer,request:Request)->None:
    path=request.request_line.request_target
    headers = Headers()
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

    elif path == "/myproblem":
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
    elif path == "/video":
        status = StatusCode.OK
        headers.headers["Content-Type"] = "video/mp4"
        headers.headers["Transfer-Encoding"] = "chunked"
        headers.headers["Trailer"] = (
            "X-Content-SHA256, X-Content-Length"
        )
        writer.write_status_line(status)
        writer.write_headers_line(headers)
        video_path = Path("assets/vim.mp4")
        hasher = hashlib.sha256()
        body_length = 0
        with video_path.open("rb") as video:
            while True:
                chunk = video.read(64 * 1024)
                if not chunk:
                    break
                writer.write_chunked_body(chunk)
                hasher.update(chunk)
                body_length += len(chunk)
        writer.write_chunked_body_done()

        trailers = Headers()
        trailers.headers["X-Content-SHA256"] = hasher.hexdigest()
        trailers.headers["X-Content-Length"] = str(body_length)

        writer.write_trailers(trailers)

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
        headers.headers["Content-Type"] = "text/html"
        headers.headers["Transfer-Encoding"] = "chunked"
        headers.headers["Trailer" ]= "X-Content-SHA256, X-Content-Length"
        writer.write_status_line(status)
        writer.write_headers_line(headers)
        # Split HTML body into smaller chunks
        chunk_size = 32
        hasher = hashlib.sha256()
        body_length=0
        for i in range(0, len(body), chunk_size):
            chunk = body[i:i + chunk_size]
            writer.write_chunked_body(chunk)
            hasher.update(chunk)
            body_length += len(chunk)
        hash_value = hasher.hexdigest()
        writer.write_chunked_body_done()
        trailers = Headers()
        trailers.headers["X-Content-SHA256"]= hash_value
        trailers.headers["X-Content-Length"]= str(body_length)
        writer.write_trailers(trailers)

#  HTTP-message   = start-line CRLF
#                   *( field-line CRLF )
#                   CRLF
#                   [ message-body ]
# status-line = HTTP-version SP status-code SP [ reason-phrase ]
# For example:

# HTTP/1.1 200 OK

# Or perhaps:

# HTTP/1.1 404 Not Found