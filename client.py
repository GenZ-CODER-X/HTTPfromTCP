import socket

def client():
    with socket.socket() as c:
        c.connect(("localhost",42069))
        while True:
            message=input("Enter the message: (\nquit to exit)")
            if message=="/quit":
                print("Client side conn is stopped")
                break
            c.sendall((message + "\n").encode("utf-8"))
if __name__=="__main__":
    client()