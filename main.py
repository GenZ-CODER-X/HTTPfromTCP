import socket


def get_lines_channel(conn:socket.socket):
    current_line=""
    while True:
        data=conn.recv(8)
        print(data)
        print(type(data))
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
    with socket.socket() as s:
        s.bind(('localhost',42069))
        s.listen(1)
        print("Waiting for connection")
        try:
            while True:
                conn,addr=s.accept()
                print("Connection acquired from",addr)
                try:
                    with conn:
                        for part_lines in (conn):
                            print(part_lines)
                finally:
                    print("Connection is closed")
        except KeyboardInterrupt:
            print("Server Shutdown")

if __name__=="__main__":
    server()