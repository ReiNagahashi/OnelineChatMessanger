import client
import socket
import sys

# ソケットを作成
client = client.Client(socket.AF_INET, socket.SOCK_DGRAM)

# サーバアドレスの設定
# テストのためにとりあえずハードコーディングしておく
# server_ip = input("Type in the server's ip address to connect to: ")
server_ip = ''
# server_port = int(input("Type in the server's port number to connect to: "))
server_port = 9001

server_address = (server_ip, server_port)
client.set_server_address(server_address)

# バインド
address = ''
port = 9050
client.bind((address, port))

# ユーザー名の入力
client.send_username()

# メッセージの入力用のプロンプト
# プロンプトを表示
print("Type messages: ", end='')
sys.stdout.flush()  # stdoutをフラッシュして、プロンプトがすぐに表示されるようにする

# メッセージの入力
client.send_message()

# ソケットを閉じる
client.socket_close()