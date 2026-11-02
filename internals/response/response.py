from enum import Enum
from internals.requests.request import Request
from pydantic import BaseModel
from io import BytesIO
from http import HTTPStatus

class StatusCode(Enum):
    OK=200 
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR=500

class HandlerError(BaseModel):
    status_code:StatusCode
    message:str

class WriterState(Enum):
    INITIALIZED="initialized"
    WRITING_STATUS_LINE="writen_response_line"
    PARSING_HEADERS = "writing_headers"
    PARSING_BODY="writing-body"
    DONE="done"

class Writer():
    def __init__(self,writer:BytesIO,http_version:str,state:WriterState):
        writer:BytesIO
        http_version:str="1.1"
        state:WriterState=WriterState.INITIALIZED
    
    def write_status_line(self,Status:StatusCode):
        status_line=(
            f"HTTP/{self.http_version} "
            f"{Status.value} "
            f"{Status.value}"
        )

        self.state=WriterState.writen

def serve_response(Request:Request,response_buffer:BytesIO)->tuple[str,str]:
    status_line = (
        f"HTTP/{Request.request_line.http_version} "
        f"{StatusCode.OK.value} "
        f"{StatusCode.OK.name}"
    )
    body=response_buffer.getvalue()
    content_type = "text/plain"
    response_headers = (
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}"
    )
    response = (status_line.encode("utf-8")
                        + b"\r\n"
                        + response_headers.encode("utf-8")
                        + b"\r\n"
                        + b"\r\n"
                        + body
                        )
    return response

def app_handler(w:BytesIO,request:Request)->HandlerError|None:
    path=request.request_line.request_target
    if path == "/yourproblem":
        return HandlerError(
            status_code=StatusCode.BAD_REQUEST,
            message="Your problem is not my problem\n"
        )
    if path == "/myproblem":
        return HandlerError(
            status_code=StatusCode.INTERNAL_SERVER_ERROR,
            message="Woopsie, my bad\n"
        )
    body="All good frfr\n"
    w.write(body.encode('utf-8'))
    return None

#Need to make write_error to write complete error http_response
def write_error(error:HandlerError,http_version)->BytesIO:
    body=error.message.encode("utf-8")
    status = HTTPStatus(error.status_code.value)
    error_response_line=(
        f"HTTP/{http_version} "
        f"{status.value} "
        f"{status.phrase}"
    )
    
    content_type="text/plain"
    response_headers=(
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}"
    )
    error_response=response = (
                                error_response_line.encode("utf-8")
                                + b"\r\n"
                                + response_headers.encode("utf-8")
                                + b"\r\n"
                                + b"\r\n"
                                + body
                                )
    w=BytesIO()
    w.write(error_response)
    return w











#  HTTP-message   = start-line CRLF
#                   *( field-line CRLF )
#                   CRLF
#                   [ message-body ]
# status-line = HTTP-version SP status-code SP [ reason-phrase ]
# For example:

# HTTP/1.1 200 OK

# Or perhaps:

# HTTP/1.1 404 Not Found