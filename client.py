# CREATE CHATROOM
# JOIN CHATROOM
import socket
import select
import sys
import json
import tcp

class Client:
    logged_in = True
    server_address = None

    def __init__(self, address_family, socket_type):
        self.sock = socket.socket(address_family, socket_type)
        self.user_name = ""
        # ホストユーザーとして登録したトークンがルーム名をキーにして格納
        self.rooms = {}
        self.current_room = ""
    

    def bind(self, address):
        self.sock.bind(address)


    def set_server_address(self, server_address):
        self.server_address = server_address

    @staticmethod
    def create_bytes_data(command, parameters):
        data = {
            "command": command,
            "parameters": parameters
        }

        return json.dumps(data).encode('utf-8')
    

    def close_socket_with_error(self, err):
        print(f'Error occured! {err}')
        self.sock.close()
        sys.exit(1)

    
    def send_username(self):
        while True:
            user_name = input("What's your name?")
            self.user_name = user_name

            data = self.create_bytes_data("user_name", {'user_name': user_name})
            try:
                _ = self.sock.sendto(data, self.server_address)
                print(f"Sent your name, wait for response")

                response, _ = self.sock.recvfrom(4096)
                json_response = json.loads(response)
                # エラーがなければメッセージ入力に進める。何らかのエラーがあったら再度入力からやり直す
                print(json_response["message"])

                if json_response["no_error"] == True:
                    return
            # 致命的なエラーの場合はソケットを閉じる関数を実行
            except Exception as e:
                self.close_socket_with_error(e)

    def listen(self):
        # ソケットをノンブロッキングモードに設定
        self.sock.setblocking(0) #ソケットをノンブロッキングモードに設定

        while self.logged_in:
            # 入力待ちとソケットからのデータまちをselectで同時に行う 
            # select関数の引数においたイテラブルな値を設定したタイムの間待つ。今回の場合readableの値がsockの場合はサーバからのレスポンス、sys.stdinの場合はユーザの入力。それぞれを設定したタイムだけ待つ。これらがどちらもタイムアウトしたらパスする
            readable, writable, exceptional = select.select([self.sock, sys.stdin], [], [], 5.0)
            if not (readable or writable or exceptional):
                # タイムアウトしても何もしない。しかし実際にはサーバ側でlogged_inがFalseになるようなレスポンスを渡す
                pass
            else:
                for s in readable:
                    # 自身が送ったメッセージを含めてクライアントのメッセージが届いている場合
                    if s is self.sock:
                        response, _ = self.sock.recvfrom(4096)
                        json_response = json.loads(response)
                        if  json_response["is_expired"]:
                            print("Time expired: Socket closed...")
                            self.logged_in = False

                        print(json_response["message"])

                    # 入力データが存在する場合
                    elif s is sys.stdin:
                        self.send_message()
    
    def send_message(self):
        msg = sys.stdin.readline().strip()
        command_list = msg.split(" ")
        # チャットルームの作成処理
        if len(command_list) == 2 and command_list[0] == 'c' and command_list[1] == 'c':
            # ルーム名の設定
            msg_room_name = input("Type a name of chatroom: ")
            # パスワードの有無
            msg_psw_is_required = input("Does it require a password?: ").lower()
            if msg_psw_is_required != 'yes' and msg_psw_is_required != 'no':
                self.close_socket_with_error('Invalid input')
            psw_is_required = msg_psw_is_required == 'yes'
            password = ""
            if psw_is_required:
                password = input("Type a password: ")
            # tcpソケットを作成してサーバに接続する
            tcp_obj = self.tcp_handle()
            # チャットルームの作成→送信ようソケット、ルームメイ、パスワードを渡す
            self.create_chatroom(tcp_obj, msg_room_name, password)

        if len(command_list) == 2 and command_list[0] == 'j' and command_list[1] == 'c':
            # ルーム名の設定
            msg_room_name = input("Type a name of chatroom: ")
            # tcpソケットを作成してサーバに接続する
            tcp_obj = self.tcp_handle()
            # completedがTrueの時、パスワードは不要だったことを表し、参加処理も終わっている
            completed = self.join_chatroom(tcp_obj, msg_room_name, 0, "")
            if not completed:
                password = input("Password: ")
                tcp_obj = self.tcp_handle()
                _ = self.join_chatroom(tcp_obj, msg_room_name, 1, password)

        else:
        # メッセージの送信
            data = self.create_bytes_data('message', {'message': msg, 'room_name': self.current_room})
            self.sock.sendto(data, self.server_address)

    # tcpソケットを作成してサーバに接続する
    def tcp_handle(self):
        # TCPソケットの作成
        tcp_obj = tcp.TCP(socket.AF_INET, socket.SOCK_STREAM)
        # TCP通信ようのサーバのアドレス、ポートの設定→取り敢えずポート番号をハードコーディング
        tcp_obj.set_remote_address((self.server_address[0], 9002))
        # サーバと接続
        tcp_obj.connect()

        return tcp_obj


    def join_chatroom(self, tcp_obj, room_name, state, password):
        tcp_socket = tcp_obj.sock
        # まずリクエストを送信
        try:
            if state == 0:
                # データの作成 
                operation_code = 2
                operation_code_byte = operation_code.to_bytes(1, "big")
                state_code = 0
                state_code_byte = state_code.to_bytes(1, "big")
                # ヘッダーを作成 ope = 2, state = 0
                header = tcp_obj.protocol_header(len(room_name.encode('utf-8')), len(operation_code_byte), len(state_code_byte), 0)

                # ヘッダーの送信
                tcp_socket.send(header)
                # データの送信
                tcp_socket.send(room_name.encode('utf-8'))
                tcp_socket.send(operation_code_byte)
                tcp_socket.send(state_code_byte)
                print("Request sent successfully!")

            # パスワードをサーバに送信
            else:
                # データの作成 
                operation_code = 2
                operation_code_byte = operation_code.to_bytes(1, "big")
                state_code = 1
                state_code_byte = state_code.to_bytes(1, "big")
                body = password

                # ヘッダーを作成 ope = 2, state = 1
                header = tcp_obj.protocol_header(len(room_name.encode('utf-8')), len(operation_code_byte), len(state_code_byte), len(body.encode('utf-8')))
                # ヘッダーの送信
                tcp_socket.send(header)
                # データの送信
                tcp_socket.send(room_name.encode('utf-8'))
                tcp_socket.send(operation_code_byte)
                tcp_socket.send(state_code_byte)
                tcp_socket.send(body.encode('utf-8'))
                print("Request with password sent successfully!")

            # リクエスト送信直後にレスポンスを受け取るためにリッスンする
            return self.tcp_handle_from_server(tcp_obj)

        except socket.error as err:
            tcp_obj.close_socket_with_error(err)


    # パスワードはペイロードの中に含まれるようにする→つまり作成のリクエストでヘッダーにはユーザー名とパスワードの情報のみ
    def create_chatroom(self, tcp_obj, room_name, password):        
        tcp_socket = tcp_obj.sock
        # まずリクエストを送信
        try:
            # データの作成 
            operation_code = 1
            operation_code_byte = operation_code.to_bytes(1, "big")
            state_code = 0
            state_code_byte = state_code.to_bytes(1, "big")
            body = ""
            if len(password):
                body = self.user_name + " " + password
            else: body = self.user_name

            # ヘッダーを作成 ope = 1, state = 0
            header = tcp_obj.protocol_header(len(room_name.encode('utf-8')), len(operation_code_byte), len(state_code_byte), len(body.encode('utf-8')))
            # ヘッダーの送信
            tcp_socket.send(header)
            # データの送信
            tcp_socket.send(room_name.encode('utf-8'))
            tcp_socket.send(operation_code_byte)
            tcp_socket.send(state_code_byte)
            tcp_socket.send(body.encode('utf-8'))
            print("Request sent successfully!")
            # リクエスト送信直後にレスポンスを受け取るためにリッスンする
            self.tcp_handle_from_server(tcp_obj)


        except socket.error as err:
            tcp_obj.close_socket_with_error(err)


    def tcp_handle_from_server(self, tcp_obj):
        tcp_sock = tcp_obj.sock
        print("-----Receiving data from server...-----")
        # ヘッダーを受け取る
        header = tcp_sock.recv(32)

        # 長さはヘッダから抽出され、別々の変数に格納されます。
        roomname_length = int.from_bytes(header[:1], "big")
        operation_length = int.from_bytes(header[1:2], "big")
        state_length = int.from_bytes(header[2:3], "big")
        operation_payload_length = int.from_bytes(header[3:], "big")


        if roomname_length == 0:
            raise Exception('No room name received')

        if operation_payload_length == 0:
            raise Exception('No response messages received')
        
        # ボディのデコード utf-8は文字列データにのみ使える。つまり、operation_codeのような数値をデータにしているものはutf-8したら変な結果になってしまう(空文字列とか)
        room_name = tcp_sock.recv(roomname_length).decode('utf-8')
        operation_code = int.from_bytes(tcp_sock.recv(operation_length), "big")
        state_code = int.from_bytes(tcp_sock.recv(state_length), "big")
        operation_payload = tcp_sock.recv(operation_payload_length).decode('utf-8')

        # クライアントからのチャットルーム作成のリクエストの場合→operation code = 1
        # クライアントにステータスコード"Success"を送る
        if operation_code == 1:
            # ステータスコードが１の場合は、メッセージを受け取り、再度サーバー側から処理終了して通知が来るのを待つ
            if state_code == 1:
                print(operation_payload)
                self.tcp_handle_from_server(tcp_obj)
                return
            # 以下はステータスコードが２の場合の処理。ペイロードはトークンなので、トークンをクライアント側で登録する
            self.rooms[room_name] = operation_payload

        # 参加するリクエストに対するレスポンスへの処理
        elif operation_code == 2:
            # ステータスコードが0の場合はチャットルーム名、パスワードの有無を確認してその結果が返ってくる
            if state_code == 0:
                # ペイロードはリストなのでjson形式からリストに直してあげる、[0]=妥当なチャットルームであるかどうか[1]=パスワードが必要であるかどうかがブール地で帰ってきている
                payload_list = json.loads(operation_payload)
                if payload_list[0] == False:
                    tcp_obj.close_socket_with_error("Invalid room name...")

                return payload_list[1] == False
            if state_code == 1:
                # パスワードが正しかった場合、このままサーバーからトークンをもらってUDP通信をする。その上でtcpソケットは閉じる
                password_is_valid = json.loads(operation_payload)

                if not password_is_valid:
                    tcp_obj.close_socket_with_error("You typed invalid password...")

                # ルーム名を表示させ、そのクライアントのcurrent_room を更新する
                print(f"#########Room name: {room_name}#########")
                self.current_room = room_name
                # トークンを使ってルームに入る →とりあえずトークンなしでその部屋の中でチャットできるようにしたい。
                # それができてから、そのルーム名の配列に入っているクライアントのみがメッセージを受け取るようにする
                # tcpソケットを閉じる
        print("TCP socket close...")
        tcp_obj.sock.close()

