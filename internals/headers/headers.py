from pydantic import BaseModel,Field
from enum import Enum

class ParserState(Enum):
    INITIALIZED="initialized"
    DONE="done"

class Headers(BaseModel):
    headers:dict[str,str]= Field(default_factory=dict)
    state:ParserState=ParserState.INITIALIZED

    def parser(self,data)->int:
        if self.state==ParserState.DONE:
            return 0
        consumed,parsed_headers=head_parser(data)
        if consumed==0:
            return 0
        self.headers=parsed_headers
        self.state=ParserState.DONE
        return consumed

def head_parser(data)->tuple[int,dict[str,str]]:
    # An empty line means there are no headers.
    if data.startswith(b"\r\n"):
        return 2, {}
    header_end=data.find(b"\r\n\r\n")
    if header_end==-1:
        return 0,{}
    raw_data=data[:header_end]
    header_lines=raw_data.split(b"\r\n")
    parsed_header={}
    for header_line in header_lines:
        # header_key_index=header.find(':')
        # header_key=header[:header_key_index]
        # header_value=header[header_key_index+1:].split()
        # headers.headers[header_key]=header_value
        key_bytes,seperator,value_bytes=header_line.partition(b":")
        if not seperator:
            raise ValueError("Invalid header: missing colon")
        key=key_bytes.decode("ascii")
        value=value_bytes.decode("ascii").strip(" \t")
        if not key or key != key.strip() or any(c.isspace() for c in key):
            raise ValueError("Invalid header name")
        parsed_header[key]=value
    consumed=header_end+4
    return consumed,parsed_header

def req_from_reader(reader,chunk_size:int=8)->Headers:
    header=Headers()
    buffer=bytearray()
    while header.state!=ParserState.DONE:
        chunk=reader.read(chunk_size)
        if not chunk:
            raise ValueError("Unexpected EOF before request line was complete")
        if isinstance(chunk,str):
            chunk=chunk.encode('utf-8')
        buffer.extend(chunk)
        consumed=header.parser(bytes(buffer))
        if consumed>0:
            del buffer[:consumed]
    return header









