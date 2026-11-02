from enum import Enum
from internals.requests.request import Request
from pydantic import BaseModel
from io import BytesIO

class StatusCode(Enum):
    200 ="OK"
    400="BAD_REQUEST "
    500="INTERNAL_SERVER_ERROR"

class HandleError(BaseModel):
    status_code:StatusCode
    message:str

def serve_response(Request:Request)->tuple[str,str]:
    status_line = (
        f"HTTP/{Request.request_line.http_version} "
        f"{StatusCode.OK.value} "
        f"{StatusCode.OK.name}"
    )
    body=b"Here is your response"
    content_type = "text/plain"
    response_headers = (
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}"
    )
    return status_line,response_headers

def app_handler(w:BytesIO,request:Request)->HandleError|None:
    path=request.request_line.request_target
    if path=="/yourproblem":
        error=write_error(StatusCode(200))
        return error
    if path == "/myproblem":
        error=write_error(StatusCode(400))
        return HandleError(
            status_code=500,
            message="Woopsie, my bad\n"
        )
    w.writelines(b"All good frfr\n")
    return None

def write_error(status_code:StatusCode,)->BytesIO:
    HandleError(status_code.name,status_code.value)
    w=BytesIO()
    w.write(HandleError.message)
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