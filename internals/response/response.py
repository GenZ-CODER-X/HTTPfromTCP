from enum import Enum
from internals.requests.request import Request


class StatusCode(Enum):
    OK = 200
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500

def serve_response(Request:Request)->tuple[str,str]:
    status_line_arr=[f"HTTP/{Request.request_line.http_version}",str(StatusCode.OK.value),StatusCode.OK.name]
    print(Request.headers_dict)
    status_line=" ".join(status_line_arr)
    header_keys=["Content-Type","Content-Length"]
    response_headers=[]
    for key in header_keys:
        value=Request.headers_dict.get_key(key)
        print(value)
        response_headers.append(f"{key}: {value}")
    response_headers="\r\n".join(response_headers)
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