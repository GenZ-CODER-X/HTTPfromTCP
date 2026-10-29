from enum import Enum
from internals.requests.request import Request

class StatusCode(Enum):
    OK = 200
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500

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








#  HTTP-message   = start-line CRLF
#                   *( field-line CRLF )
#                   CRLF
#                   [ message-body ]
# status-line = HTTP-version SP status-code SP [ reason-phrase ]
# For example:

# HTTP/1.1 200 OK

# Or perhaps:

# HTTP/1.1 404 Not Found