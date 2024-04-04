import socket
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = '0.0.0.0'
server_port = 9001
print('starting up on port {}'.format(server_port))

sock.bind((server_address, server_port))

while True:
    print('\nwaiting to receive message')
    data, address = sock.recvfrom(4096)
    json_data = json.loads(data)
    print(f"Received data: {json_data} from {address}")
    if data:
        response = b"Received your message!"
        sent = sock.sendto(response, address)


