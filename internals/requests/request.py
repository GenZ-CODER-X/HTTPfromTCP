from pydantic import BaseModel,Field
from enum import Enum
import re
from internals.headers import headers

class RequestLine(BaseModel):
    method:str
    request_target:str
    http_version:str

class RequestState(Enum):
    INITIALIZED="initialized"
    PARSING_HEADERS = "parsing_headers"
    DONE="done"

class Request(BaseModel):
    request_line:RequestLine |None=None
    state:RequestState=RequestState.INITIALIZED
    headers_dict:headers.Headers=Field(
        default_factory=headers.Headers
    )

    def parse(self,data:bytes)->int:
        total_bytes_parsed = 0
        while self.state != RequestState.DONE:
            consumed = self.parse_single(
                data[total_bytes_parsed:]
            )

            if consumed == 0:
                break

            total_bytes_parsed += consumed

        return total_bytes_parsed
        # total_bytes_parsed=0
        # if self.state== ParserState.DONE and self.headers.state==ParserState.DONE:
        #     return 0
        # consumed,request_line=parser_request_line(data)

        # if consumed==0:
        #     return 0
        # self.request_line=request_line
        # self.state=ParserState.DONE
        # return consumed
    def parse_single(self, data: bytes) -> int:
        if self.state == RequestState.INITIALIZED:
            consumed, request_line = parser_request_line(data)

            if consumed == 0:
                return 0

            self.request_line = request_line
            self.state = RequestState.PARSING_HEADERS
            return consumed

        if self.state == RequestState.PARSING_HEADERS:
            consumed = self.headers_dict.parser(data)

            if consumed == 0:
                return 0

            self.state = RequestState.DONE
            return consumed

        return 0

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
    
    method,target,version=parts_request_line

    request_line_validator(method,version)

    Req_line=RequestLine(
        method=method,
        request_target=target,
        http_version="1.1")
    
    return line_end+2,Req_line

def request_line_validator(method:str,version:str)->None:
    if not re.fullmatch(r"[A-Z]+", method):
        raise ValueError("Not a valid HTTP method")

    if version != "HTTP/1.1":
        raise ValueError("Not a valid HTTP version")

def request_from_reader(reader,chunk_size:int=8)->Request:
    request=Request()
    buffer=bytearray()
    # Socket makefile readers support read1(); retain compatibility
    # with reader objects that only provide read().
    read_chunk = getattr(reader, "read1", reader.read)
    while request.state!=RequestState.DONE:
        chunk=read_chunk(chunk_size)
        print(chunk)
        if not chunk:
            raise ValueError("Unexpected EOF before request line was complete")
        if isinstance(chunk,str):
            chunk=chunk.encode('utf-8')
        buffer.extend(chunk)
        consumed=request.parse(bytes(buffer))
        if consumed>0:
            del buffer[:consumed]
    print(request.request_line)
    print(chunk)
    return request

    # raw_request = reader.read()
    # request_line = parser_request_line(raw_request)
    # return Request(request_line=request_line)

    





