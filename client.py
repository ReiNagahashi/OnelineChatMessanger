import socket
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_ip = input("Type in the server's ip address to connect to: ")
server_port = int(input("Type in the server's port number to connect to: "))

server_address = (server_ip, server_port)

address = ''
port = 9050

user_name = input("What's your name?")
msg = input("Enter your message: ")

data = {"user_name": user_name, "message": msg}
bytes_data = json.dumps(data).encode('utf-8')

sock.bind((address, port))


try:
    print('sending {!r}'.format(bytes_data))
    sent = sock.sendto(bytes_data, server_address)
    response, server = sock.recvfrom(4096)
    print(f"received {response} from {server}")
finally:
    print('closing socket')
    sock.close()