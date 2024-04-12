import socket
import sys

class TCP:
    def __init__(self, address_family, socket_type):
        self.sock = socket.socket(address_family, socket_type)


    def bind(self, address):
        self.sock.bind(address)


    def set_remote_address(self, remote_address):
        self.remote_address = remote_address


    def connect(self):
        print("TCP Socket connecting to remote...")
        try:
            self.sock.connect(self.remote_address)
        except socket.error as err:
            self.close_socket_with_error(err)
    

    def close_socket_with_error(self, err):
        if err:
            print(f'Error occured! {err}')
        self.sock.close()
        sys.exit(1)


# ヘッダーは32バイトです。RoomNameSize（1 バイト） | Operation（1 バイト）→1: チャットルームの作成 2: チャットルームへの参加 | State（1 バイト）: 0: サーバの初期化~2: リクエスト完了 | OperationPayloadSize（29 バイト）→クライアント、サーバがやり取りするために使うデータ
    def protocol_header(self, roomname_length, operation, state, data_length):

        return roomname_length.to_bytes(1, 'big') + operation.to_bytes(1, 'big') + \
    state.to_bytes(1, 'big') + data_length.to_bytes(29, 'big')



    def listen(self):
        self.sock.listen(1)
        print("Waiting connection from client...")
        while True:
            # connection, destination_address = self.sock.accept()
            _, remote_address = self.sock.accept()
            print('Connection from', remote_address)
            # try:
            #     print('connection from', destination_address)
            #     header = connection.recv(8)
            #     roomname_length = int.from_bytes(header[:1], "big")
            #     password_length = int.from_bytes(header[4:8], "big")


                


    



