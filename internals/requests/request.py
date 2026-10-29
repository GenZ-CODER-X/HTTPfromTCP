from pydantic import BaseModel,Field,PrivateAttr
from enum import Enum
import re
from internals.headers import headers
from typing import BinaryIO
import json

class RequestLine(BaseModel):
    method:str
    request_target:str
    http_version:str

#The most important is to maintain state machine each and everytime 
class RequestState(Enum):
    INITIALIZED="initialized"
    PARSING_HEADERS = "parsing_headers"
    PARSING_BODY="parsing-body"
    DONE="done"

class Request(BaseModel):
    request_line:RequestLine |None=None
    state:RequestState=RequestState.INITIALIZED
    headers_dict:headers.Headers=Field(
        default_factory=headers.Headers
    )
    # body: bytes = b""
    _body_reader:BinaryIO | None = PrivateAttr(default=None)

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
            # self.state=RequestState.PARSING_BODY
            self.state = RequestState.DONE
            data_remaining=data[consumed:]

            return consumed
        return 0
        # if self.state == RequestState.PARSING_BODY:
        #     content_length = self.headers_dict.get_key("Content-Length")

        #     # As of now, no Content-Length means no body.
        #     if content_length is None:
        #         self.state=RequestState.DONE
        #         return 0

        #     try:
        #         expected_length = int(content_length)
        #     except ValueError as exc:
        #         raise ValueError("Invalid Content-Length") from exc

        #     if expected_length < 0:
        #         raise ValueError("Invalid Content-Length")

        #     self.body += data

        #     if len(self.body) > expected_length:
        #         raise ValueError("Body exceeds Content-Length")

        #     if len(self.body) == expected_length:
        #         self.state = RequestState.DONE

        #     # All available bytes have been added to the body.
        #     return len(data)
        # return 0


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

def request_from_reader(reader,chunk_size:int=8)->tuple[Request,str]:
    count=0
    request=Request()
    buffer=bytearray()
    # Socket makefile readers support read1(); retain compatibility
    # with reader objects that only provide read().
    read_chunk = getattr(reader, "read1", reader.read)
    while request.state!=RequestState.DONE:
        chunk=read_chunk(chunk_size)
        if not chunk:
            raise ValueError("Unexpected EOF before request was complete")
        if isinstance(chunk,str):
            chunk=chunk.encode('utf-8')
        buffer.extend(chunk)
        consumed=request.parse(bytes(buffer))
        if consumed>0:
            del buffer[:consumed]
    request._body_reader=reader
    return request,buffer

    # raw_request = reader.read()
    # request_line = parser_request_line(raw_request)
    # return Request(request_line=request_line)

    
def body_parser(request:Request,buffer,chunk_size=65536):
    content_length = request.headers_dict.headers.get("content-length")
    if content_length is None:
        return None
    remaining_length=int(content_length)
    print(remaining_length)
    file=open("body_file","w+b")
    try:
        if buffer:
            if len(buffer) > remaining_length:
                raise ValueError("Body exceeds Content-Length")
            file.write(buffer)
            remaining_length -= len(buffer)
            print(remaining_length)
            
        while remaining_length > 0:
            chunk = request._body_reader.read(
                    min(chunk_size, remaining_length)
                )
            if not chunk:
                print("Incomplete Body")
                raise EOFError("Incomplete request body")
            remaining_length -= len(chunk)
            file.write(chunk)
        file.seek(0)
        return file
    except Exception:
        print(Exception)
        file.close()
        raise ValueError("Error has occured on getting the body")
    
def handle_req(client,request:Request):
    # req_line="201"+request.request_line.method+request.request_line.request_target+request.request_line.http_version
    # headers=json.dumps(request.headers_dict)
    # data_sending=f"\nReceived_req"
    # response=f"{req_line}\n{headers}\n"
    response = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/plain\r\n"
        b"\r\n"
        b"Hello World!\n"
    )

    try:
        client.sendall(response)
    finally:
        client.close()

            




