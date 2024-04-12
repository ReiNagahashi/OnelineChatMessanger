import socket
import json
from collections import defaultdict
import time
import select


class Server:
    response = {
        'no_error': True,
        'message': '',
        'is_expired': False
    }
    # この値を過ぎてしまうと、ユーザはonline_usersから削除されてクライアント側でソケットが自動で閉じられる
    valid_duration = 10 #sec
    # (ip_address, port_number): [時刻の文字列要素1, 時刻の文字列要素2, ...]
    messages = defaultdict(list)
    # key: (ip_address, port_number), value: (ユーザー名, 最後のメッセージの時間)
    online_users = {}

    def __init__(self, address, udp_port, tcp_port):
        self.server_address = address
        self.udp_port = udp_port
        self.tcp_port = tcp_port

        # UDPソケットの初期化
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((self.server_address, self.udp_port))
        self.udp_socket.setblocking(0) #ソケットをノンブロッキングモードに設定


        # TCPソケットの初期化
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind((self.server_address, self.tcp_port))
        self.tcp_socket.listen()
        self.tcp_socket.setblocking(0) #ソケットをノンブロッキングモードに設定


    def listen(self):
        while True:
            readable, _, _ = select.select([self.udp_socket, self.tcp_socket], [], [], 180.0)
            # UDP, TCPの両方をノンブロッキングで並行して通信する
            if not readable:
                self.check_expired_users()
            for sock in readable:
                if sock == self.udp_socket:
                    data, address = self.udp_socket.recvfrom(4096)
                    self.udp_handle(data, address)
                elif sock == self.tcp_socket:
                    client_socket, addr = self.tcp_socket.accept()
                    print("TCP request received!!")
                    self.tcp_handle(client_socket, addr)


    def udp_handle(self, data, client_address):
        current_time = time.time()
        json_data = json.loads(data)

        # ユーザー名の登録
        if json_data['command'] == 'user_name': 
            if self.data_size_validation(json_data['parameters'], [255]):
                self.response['message'] = "Welcome to our message service"
                # 登録ユーザーを格納する辞書に保存, メッセージは空白で初期化
                self.online_users[client_address] = [json_data['parameters']['user_name'], 0.0]
        # メッセージ送信
        elif json_data['command'] == 'message':
            if self.data_size_validation(json_data['parameters'], [4096]):
                self.response['message'] = f"{self.online_users[client_address][0]}: {json_data['parameters']['message']}"
        # チャットルーム作成コマンド
        elif json_data['command'] == 'create_chatroom':

            print("Request for creating chatroom received!!!")
            self.response['message'] = "Start creating chatroom..."
        self.online_users[client_address][1] = current_time

        self.send_response(client_address)


    def send_response(self, address):
        _ = self.udp_socket.sendto(json.dumps(self.response).encode('utf-8'), address)


    # 第一引数："parameters"のディクショナリ, 第二引数：parametersの各要素の制限メモリを持ったリスト
    def data_size_validation(self, parameters, limits):
        # ユーザー名は255bytes, 'message'であれば4096bytesを最大にしてバリデーションをする
        param_sizes = parameters.values()
        for param_size, limit in zip(param_sizes, limits):
            # バイトサイズで比較するために、バイト型に変更
            if len(param_size.encode('utf-8')) > limit:
                self.response['no_error'] = False
                self.response['message'] = "Error: One of parameters exceeds the limitation! Try again."
                return False

        self.response['no_error'] = True
        print("Data size validation Succeeded!!")
        return True

    def check_expired_users(self):
        print(self.online_users)
        # pythonではディクショナリデータをそのままイテレートした上で削除処理をしたらランタイムエラーになる→リストでコピーを作る必要がある
        for key, values in list(self.online_users.items()):
            last_time = values[1]
            if time.time() - last_time > self.valid_duration:
                # クライアントにソケットを閉じるようにレスポンス
                self.response['is_expired'] = True
                self.response['message'] = "You haven't send message for a while. Close your socket..."
                # keyはアドレス
                self.send_response(key)
                del self.online_users[key]
                self.response['is_expired'] = False

        print("check_expired_users func is completed!")
        print(self.online_users)


    def tcp_handle(self, client_socket, client_address):
        print(f"Client socket: {client_socket}, Client Address: {client_address}")
