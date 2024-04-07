import socket
import select
import sys
import json

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

    
    def send_message(self):
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
                        msg = sys.stdin.readline().strip()
                        data = self.create_bytes_data('message', {'message': msg})

                        self.sock.sendto(data, self.server_address)

    def socket_close(self):
        self.sock.close()