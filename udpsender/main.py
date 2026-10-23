import socket
import sys
def main():
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as conn:
        conn.connect(("localhost",42069))
        print("My local address and port:", conn.getsockname())
        print("Remote address and port:", conn.getpeername())
        while True:
            line=input(">")
            if line=="":
                print("closing the UDP Sender")
                break
            try:
                conn.send((line+'\n').encode("utf-8"))
            except OSError as exc:
                        print(f"Error sending UDP datagram: {exc}", file=sys.stderr)

            except KeyboardInterrupt:
                print("\nThe UDP sender shutdown",file=sys.stderr)
            
            except OSError as exc:
                print(f"Socket error: {exc}", file=sys.stderr)

if __name__=="__main__":
     main()


    