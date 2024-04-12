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
        if 3 <= len(command_list) <= 4 and command_list[0] == 'CREATE' and command_list[1] == 'CHATROOM':
            password = ""
            if len(command_list) == 4:
                password = command_list[-1]                        

            self.create_chatroom(command_list[2], password)
            # サーバにもルーム名とパスワードを送信→ここで送る必要があるのか？TCPで安全に確実に送れるようにするべきことだと思うよ
            data = self.create_bytes_data('create_chatroom', {})
        else:
        # メッセージの送信
            data = self.create_bytes_data('message', {'message': msg})

        self.sock.sendto(data, self.server_address)


    def create_chatroom(self, room_name, password):        
        # TCPソケットの作成
        tcp_sock = tcp.TCP(socket.AF_INET, socket.SOCK_STREAM)
        # TCP通信ようのサーバのアドレス、ポートの設定→取り敢えずポート番号をハードコーディング
        tcp_sock.set_remote_address((self.server_address[0], 9002))
        # サーバと接続
        tcp_sock.connect()

        # まずリクエストを送信
        try:
            # ヘッダーを作成
            header = tcp_sock.protocol_header(len(room_name.encode('utf-8')), 1, 0, len(password.encode('utf-8')))
            # ヘッダーの送信
            tcp_sock.send(header)
            # ボディの送信
            tcp_sock.send((room_name + " " + password).encode('utf-8'))

        except socket.error as err:
            tcp_sock.close_socket_with_error(err)
        
        finally:
            print("Succeeded!!")
            tcp_sock.close_socket_with_error("")



    def socket_close(self):
        self.sock.close()