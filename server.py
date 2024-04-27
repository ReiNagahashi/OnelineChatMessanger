import socket
import json
from collections import defaultdict
import time
import select
import tcp
import random


class Server:
    response = {
        'no_error': True,
        'message': '',
        'is_expired': False
    }
    # この値を過ぎてしまうと、ユーザはonline_usersから削除されてクライアント側でソケットが自動で閉じられる
    valid_duration = 10000 #sec
    # (ip_address, port_number): [時刻の文字列要素1, 時刻の文字列要素2, ...]
    messages = defaultdict(list)
    # key: (ip_address, port_number), value: (ユーザー名, 最後のメッセージの時間)
    online_users = {}
    # 登録してあるチャットルーム → key: ルーム名 value: password
    chat_rooms = {}
    tokens = set()
    # key: (ip_address, port_number), value: トークン 各ユーザーは複数のルームを持つことがあるので、配列を値としてもつ
    host_users = defaultdict(list)
    # 各チャットルームにオンラインで参加しているユーザーのリスト→オフラインになったらリストから削除される
    # 各チャットルーム内でのメッセージはここの各キーの値にあるアドレスのユーザーたちのみで共有されるようにする
    # key: room_name value: [(ip_address, port_number), ]
    current_join_users = defaultdict(list)


    def __init__(self, address, udp_port, tcp_port):
        self.server_address = address
        self.udp_port = udp_port
        self.tcp_port = tcp_port

        # UDPソケットの初期化
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((self.server_address, self.udp_port))
        self.udp_socket.setblocking(0) #ソケットをノンブロッキングモードに設定

        # TCPソケットの初期化
        self.tcp_obj = tcp.TCP(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket = self.tcp_obj.sock

        self.tcp_obj.set_remote_address((self.server_address, self.tcp_port))
        self.tcp_obj.bind()
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

# ルームに参加しているユーザーのメッセージには追加でルーム名がデータの中に入っている。それをもとに、サーバではそのルームに入っているユーザーにだけメッセージが送られるようにする
    def udp_handle(self, data, client_address):
        current_time = time.time()
        json_data = json.loads(data)

        # ユーザー名の登録
        if json_data['command'] == 'user_name': 
            if self.data_size_validation(json_data['parameters'], [255]):
                self.response['message'] = "Welcome to our message service"
                # 登録ユーザーを格納する辞書に保存, メッセージは空白で初期化
                self.online_users[client_address] = [json_data['parameters']['user_name'], 0.0]
        elif json_data['command'] == 'message':
            if self.data_size_validation(json_data['parameters'], [4096]):
                self.response['message'] = f"{self.online_users[client_address][0]}: {json_data['parameters']['message']}"
                # メッセージ送信 各ルーム名ごとにそのルーム内のクライアントだけがメッセージが共有できるようにする
                # ルーム名がわかると思うので、それをキーにして、ディクショから値を取ってきて、その値ごとにsend_response関数を実行する
                if len(json_data['parameters']['room_name']) > 0:
                    for client_address in self.current_join_users[json_data['parameters']['room_name']]:
                        self.send_response(client_address)
                    return


        # チャットルーム作成コマンド
        elif json_data['command'] == 'create_chatroom':
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
        # ヘッダーを受け取る
        header = client_socket.recv(32)
        print(header)

        # 長さはヘッダから抽出され、別々の変数に格納されます。
        roomname_length = int.from_bytes(header[:1], "big")
        operation_length = int.from_bytes(header[1:2], "big")
        state_length = int.from_bytes(header[2:3], "big")
        operation_payload_length = int.from_bytes(header[3:], "big")

        if roomname_length == 0:
            raise Exception('No room name received')
        
        # ボディのデコード utf-8は文字列データにのみ使える。つまり、operation_codeのような数値をデータにしているものはutf-8したら変な結果になってしまう(空文字列とか)
        room_name = client_socket.recv(roomname_length).decode('utf-8')
        operation_code = int.from_bytes(client_socket.recv(operation_length), "big")
        state_code = int.from_bytes(client_socket.recv(state_length), "big")
        operation_payload = client_socket.recv(operation_payload_length).decode('utf-8')

        print("WWWWWWWWWWWWWWWWW")
        print(operation_code)
        print(state_code)

        # クライアントからのチャットルーム作成のリクエストの場合→operation code = 1
        # クライアントにステータスコード"Success"を送る
        if operation_code == 1:
            print("-----OPERATION CODE == 1-----")
            # チャットルームの登録→パスワードがあるかもチェック
            self.chat_rooms[room_name] = ""
            print(operation_payload.split(" ")[1])
            # パスワードが存在する場合はroom_nameと紐付けてchat_roomsにvalueとして保存する
            if len(operation_payload.split(" ")) == 2:
                self.chat_rooms[room_name] = operation_payload.split(" ")[1]
            print("current chat room: ", self.chat_rooms)
            msg = "Request for creating chatroom recieved!"
            # リクエストを無事受け取ったことをステータスコードをペイロードに入れた上でクライアントにレスポンス
            header = self.tcp_obj.protocol_header(roomname_length, operation_length, state_length, len(msg.encode('utf-8')))
            # ボディデータの作成
            state_code_response = state_code + 1
            state_code_response_byte = state_code_response.to_bytes(1, "big")
            # ヘッダーの送信
            client_socket.send(header)
            # ボディの送信
            client_socket.send(room_name.encode('utf-8'))
            client_socket.send(operation_code.to_bytes(1, "big"))
            client_socket.send(state_code_response_byte)
            client_socket.send(msg.encode('utf-8'))
            print("-----Response sent successfully!-----")
            
            # チャットルーム作成処理 4文字のランダムなアルファベット, 数字を組み合わせた文字列を作成し、それをトークンとしてペイロードにする
            token = self.create_token()
            # トークンをホストユーザーの(ip,port)と紐付ける
            self.host_users[client_address].append(token)
            state_code_created_room = state_code_response + 1
            state_code_created_room_byte = state_code_created_room.to_bytes(1, "big")
            
            header = self.tcp_obj.protocol_header(roomname_length, operation_length, len(state_code_response_byte), len(token.encode('utf-8')))

            # ヘッダーの送信
            client_socket.send(header)
            # ボディの送信
            client_socket.send(room_name.encode('utf-8'))
            client_socket.send(operation_code.to_bytes(1, "big"))
            client_socket.send(state_code_created_room_byte)
            client_socket.send(token.encode('utf-8'))
            

        # クライアントからのチャットルーム参加のリクエストの場合→operation code = 2
        elif operation_code == 2:
            print("-----OPERATION CODE == 2-----")
            print(f"State code = {state_code}")
            # チャットルーム参加のリクエストで、クライアントがチャットルーム名を送ってきた→チャットルーム・パスワードの有無を確認して、それに応じてクライアントにパスワードを要求
            # パスワードがなかった場合、クライアントからの再度のリクエスト抜きにして、current_room_usersに追加して、「ようこそ！」みたいなメッセージをペイロードに含める
            if state_code == 0:
                # クライアントからきたチャットルーム名が存在するチャットルーム名なのかを検証
                room_is_valid = room_name in self.chat_rooms
                # room_nameのルームがパスワード必要なのかのブール値
                psw_is_required = len(self.chat_rooms[room_name]) > 0
                payload_list = [room_is_valid, psw_is_required]
                # リストとして返す必要があるので、JSON形式にする
                payload_list_json = json.dumps(payload_list)
                # リクエストを無事受け取ったことをステータスコードをペイロードに入れた上でクライアントにレスポンス
                header = self.tcp_obj.protocol_header(roomname_length, operation_length, state_length, len(payload_list_json.encode('utf-8')))
                # ボディデータの作成
                state_code_response_byte = state_code.to_bytes(1, "big")
                # ヘッダーの送信
                client_socket.send(header)
                # ボディの送信
                client_socket.send(room_name.encode('utf-8'))
                client_socket.send(operation_code.to_bytes(1, "big"))
                client_socket.send(state_code_response_byte)
                client_socket.send(payload_list_json.encode('utf-8'))
                print("-----Response sent successfully!-----")


            # パスワードが存在する場合は余分に1回データをクライアントとやり取りする必要がある
            elif state_code == 1:
                # パスワードのバリデーション→正しいかどうかをブール値を文字列で表現してペイロードに入れる
                password_is_valid = True
                if self.chat_rooms[room_name] != operation_payload:
                    password_is_valid = False
                    
                password_is_valid_json = json.dumps(password_is_valid)

                # リクエストを無事受け取ったことをステータスコードをペイロードに入れた上でクライアントにレスポンス
                header = self.tcp_obj.protocol_header(roomname_length, operation_length, state_length, len(password_is_valid_json.encode('utf-8')))
                # ヘッダーの送信
                client_socket.send(header)
                # ボディの送信
                client_socket.send(room_name.encode('utf-8'))
                client_socket.send(operation_code.to_bytes(1, "big"))
                client_socket.send(state_code.to_bytes(1, "big"))
                client_socket.send(password_is_valid_json.encode('utf-8'))
                print("-----Password Validation done-----")
                # パスワードが正しかったらチャットルームにそのクライアントを入れる
                if password_is_valid:
                    self.current_join_users[room_name].append(client_address)




    def create_token(self):
        alphabets_numbers = "123456789abcdefghijklmnopqrstuvwxyz"
        token = ""
        while True:
            token = "".join(random.choices(alphabets_numbers, k=6))
            if token in self.tokens:
                continue
            self.tokens.add(token)
            break
        
        return token


