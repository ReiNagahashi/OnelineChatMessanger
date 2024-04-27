import socket
import sys

class TCP:
    def __init__(self, address_family, socket_type):
        self.sock = socket.socket(address_family, socket_type)
        

    def set_remote_address(self, remote_address):
        self.remote_address = remote_address


    def bind(self):
        self.sock.bind(self.remote_address)

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

    def validate_header(self, header):
        # 長さはヘッダから抽出され、別々の変数に格納されます。
        roomname_length = int.from_bytes(header[:1], "big")
        # operation_length = int.from_bytes(header[1:2], "big")
        # state_length = int.from_bytes(header[2:3], "big")
        operation_payload_length = int.from_bytes(header[3:], "big")


        if roomname_length == 0:
            raise Exception('No room name received')

        if operation_payload_length == 0:
            raise Exception('No username received')

        

    # ヘッダーは32バイトです
    # ヘッダーの内容：
        # RoomNameSize（1 バイト
        # Operation（1 バイト）→1: チャットルームの作成 2: チャットルームへの参加
            # これに応じてtcpクラス内の処理を変える
        # State（1 バイト）: 0: サーバの初期化 1: リクエストの応答2: リクエスト完了
            # これに応じてエラーを吐いたりする
        # OperationPayloadSize（29 バイト）→クライアント、サーバがやり取りするために使うデータ
        # バイトデータのレングスを引数として持ってくる。それをバイト値にして連結した上で返す
    def protocol_header(self, roomname_length, operation_length, state_length, data_length):
        return roomname_length.to_bytes(1, 'big') + operation_length.to_bytes(1, 'big') + \
    state_length.to_bytes(1, 'big') + data_length.to_bytes(29, 'big')


                


    



