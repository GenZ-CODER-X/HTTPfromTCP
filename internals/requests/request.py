from pydantic import BaseModel
from enum import Enum
import re

class RequestLine(BaseModel):
    method:str
    request_target:str
    http_version:str

class ParserState(Enum):
    INITIALIZED="intialized"
    DONE="done"

class Request(BaseModel):
    request_line:RequestLine |None=None
    state:ParserState=ParserState.INITIALIZED

    def parse(self,data:bytes)->int:
        if self.state== ParserState.DONE:
            return 0
        consumed,request_line=parser_request_line(data)

        if consumed==0:
            return 0
        self.request_line=request_line
        self.state=ParserState.DONE

        return consumed

def parser_request_line(data:bytes)->tuple[int,RequestLine|None]:
    line_end=data.find(b"\r\n")
    if line_end==-1:
        return 0,None
    
    raw_line=data[:line_end]
    try:
        line=raw_line.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("Request line must contain ASCII bytes") from exc
    
    parts_request_line=line.split(" ")
    if len(parts_request_line)!=3 or any(not part for part in parts_request_line):
        raise ValueError("Invalid request line:expected 3 components")
    
    Req_line=RequestLine(
        method=parts_request_line[0],
        request_target=parts_request_line[1],
        http_version=1.1)
    request_line_validator(Req_line.method,Req_line.http_version)
    return line_end+2,Req_line

def request_line_validator(method:str,version:str)->None:
    if not re.fullmatch(r"[A-Z]+", method):
        raise ValueError("Not a valid HTTP method")

    if version != "HTTP/1.1":
        raise ValueError("Not a valid HTTP version")

def request_from_reader(reader)->Request:
    request=Request()
    buffer=bytearray()
    chunk_size=8
    while request.state!=ParserState.DONE:
        chunk=reader.read(chunk_size)
        if not chunk:
            raise ValueError("Unexpected EOF before request line was complete")
        if isinstance(chunk,str):
            chunk=chunk.encode('utf-8')
        buffer.extend(chunk)
        consumed=request.parse(bytes(buffer))
        if consumed>0:
            del buffer[:consumed]
    return request

    # raw_request = reader.read()
    # request_line = parser_request_line(raw_request)
    # return Request(request_line=request_line)

    





