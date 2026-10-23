from pydantic import BaseModel

class RequestLine(BaseModel):
    method:str
    request_target:str
    http_version:str

class Request(BaseModel):
    request_line:RequestLine

def request_from_reader(request:str)->Request:
    Req=Request()
    Req.request_line=parser_request_line(request)
    print(Req.request_line)

def parser_request_line(request:str)->RequestLine:
    parts_request=request.split("\n")
    if not parts_request:
        raise ValueError("Invalid request line:expected 3 components")
    parts_request_line=parts_request[0].split()
    if len(parts_request_line)!=3:
        raise ValueError("Invalid request line:expected 3 components")
    Req_line=RequestLine(
        method=parts_request_line[0],
        request_target=parts_request_line[1],
        http_version=parts_request_line[2])
    request_line_validator(Req_line)
    return Req_line

def request_line_validator(Req_line:RequestLine):
    valid_methods=["GET", "POST", "PUT", "PATCH", "DELETE"]
    valid_versions = ["HTTP/1.1", "HTTP/2", "HTTP/3"]
    if Req_line.method not in valid_methods:
        raise ValueError("Not a valid HTTP method")
    if Req_line.http_version not in valid_versions:
        raise ValueError("Not a valid HTTP version")

def request_from_reader(reader) -> Request:
    raw_request = reader.read()
    request_line = parser_request_line(raw_request)
    return Request(request_line=request_line)
    





