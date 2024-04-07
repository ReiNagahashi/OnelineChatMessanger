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

    # key: (ip_address, port_number), value: (ユーザー名, 最後のメッセージの時間)
    online_users = {}
    # (ip_address, port_number): [時刻の文字列要素1, 時刻の文字列要素2, ...]
    messages = defaultdict(list)


    def __init__(self, address_family, socket_type):
        self.sock = socket.socket(address_family, socket_type)
    

    def bind(self, address):
        self.sock.bind(address)
        self.sock.setblocking(0) #ソケットをノンブロッキングモードに設定
    

    def send_response(self, address):
        _ = self.sock.sendto(json.dumps(self.response).encode('utf-8'), address)


    def listen(self):
        while True:
            print('\nwaiting to receive message')

            readable, writable, exceptional = select.select([self.sock], [], [], 5.0)
            if not (readable or writable or exceptional):
                pass
            else:
                data, address = self.sock.recvfrom(4096)

                current_time = time.time()
                
                json_data = json.loads(data)

                if json_data['command'] == 'user_name': 
                    if self.data_size_validation(json_data['parameters'], [255]):
                        self.response['message'] = "Welcome to our message service"
                        # 登録ユーザーを格納する辞書に保存, メッセージは空白で初期化
                        self.online_users[address] = [json_data['parameters']['user_name'], 0.0]
                elif json_data['command'] == 'message':
                    if self.data_size_validation(json_data['parameters'], [4096]):
                        self.response['message'] = f"{self.online_users[address][0]}: {json_data['parameters']['message']}"
                self.online_users[address][1] = current_time

                self.send_response(address)

            self.check_expired_users()


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

        print("check_expired_users func is completed!")
        print(self.online_users)


