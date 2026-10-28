import socket
from internals.requests.request import request_from_reader,body_parser
import time

def get_lines_channel(conn:socket.socket):
    current_line=""
    while True:
        data=conn.recv(8)
        # print(data)
        # print(type(data))
        if not data:
            break
        text=data.decode('utf-8')
        parts=text.split('\n')
        for part in parts[:-1]:
            current_line+=part
            yield current_line
            current_line=''
        current_line+=parts[-1]
    if current_line:
        yield current_line

def server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #This allows me to use TCP back to back from same address
        s.bind(('localhost',42069))
        s.listen(1)
        print("Waiting for connection")
        try:
            while True:
                conn,addr=s.accept()
                print("Connection acquired from",addr)
                try:
                    with conn:
                        with conn.makefile('rb') as reader:
                            request_return=request_from_reader(reader,chunk_size=65536)
                            request=request_return[0]
                            buffer=request_return[1]
                            print("Request line:")
                            print(f"- Method: {request.request_line.method}")
                            print(f"- Target: {request.request_line.request_target}")
                            print(f"- Version: {request.request_line.http_version}")
                            print("Headers:")
                            for key, value in request.headers_dict.headers.items():
                                print(f"- {key}: {value}")
                            # print("Body size:", len(request.body), "bytes")
                            # print("Body preview:", request.body[:80].decode("utf-8", errors="replace"))
                            body_file = body_parser(request, buffer)
                            print("read the body_file")
                            if body_file is not None:
                                try:
                                    print(body_file.read())  # Returns bytes
                                finally:
                                    body_file.close()
                finally:
                    print("Connection is closed")
        except KeyboardInterrupt:
            print("Server Shutdown")

if __name__=="__main__":
    server()