import socket
import select
import sys
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def create_bytes_data(command, parameters):
    data = {
        "command": command,
        "parameters": parameters
    }

    return json.dumps(data).encode('utf-8')



def close_socket_with_error():
    print('Error occured! Socket Closed...')
    sock.close()
    sys.exit(1)



# 実際には入力させるけど、テスト中はハードコーディングしておく
# server_ip = input("Type in the server's ip address to connect to: ")
server_ip = ''
# server_port = int(input("Type in the server's port number to connect to: "))
server_port = 9001


server_address = (server_ip, server_port)

address = ''
port = 9050

sock.bind((address, port))

# ユーザー名の入力
while True:
    user_name = input("What's your name?")
    data = create_bytes_data("user_name", {'user_name': user_name})
    try:
        sent = sock.sendto(data, server_address)
        print(f"Sent your name, wait for response")
        # Welcome! というレスポンスが来たら成功
        response, server = sock.recvfrom(4096)
        json_response = json.loads(response)
        # エラーがなければメッセージ入力に進める。何らかのエラーがあったら再度入力からやり直す
        print(json_response["message"])
        if json_response["no_error"] == True:
            break
    # 致命的なエラーの場合はソケットを閉じる関数を実行
    except:
        close_socket_with_error()

sock.setblocking(0) #ソケットをノンブロッキングモードに設定

logged_in = True

# タイムアウト=クライアントがリレーシステムから削除され、サーバーから「出ていけ」というレスポンスが来て、そのままソケットを閉じる処理をする

# プロンプトを表示
print("Type messages: ", end='')
sys.stdout.flush()  # stdoutをフラッシュして、プロンプトがすぐに表示されるようにする

# メッセージの入力
while logged_in:
    # 入力待ちとソケットからのデータまちをselectで同時に行う 
    # select関数の引数においたイテラブルな値を設定したタイムの間待つ。今回の場合readableの値がsockの場合はサーバからのレスポンス、sys.stdinの場合はユーザの入力。それぞれを設定したタイムだけ待つ。これらがどちらもタイムアウトしたらパスする
    readable, writable, exceptional = select.select([sock, sys.stdin], [], [], 5.0)
    if not (readable or writable or exceptional):
        # タイムアウトしても何もしない。しかし実際にはサーバ側でlogged_inがFalseになるようなレスポンスを渡す
        pass
    else:
        for s in readable:
            # 自身が送ったメッセージを含めてクライアントのメッセージが届いている場合
            if s is sock:
                response, server = sock.recvfrom(4096)
                json_response = json.loads(response)
                if  json_response["is_expired"]:
                    print("Time expired: Socket closed...")
                    logged_in = False

                print(json_response["message"])

                # else:
                #     # 別のクライアントのメッセージが表示される
                #     print(response[1])
            # 入力データが存在する場合
            elif s is sys.stdin:
                msg = sys.stdin.readline().strip()
                data = create_bytes_data('message', {'message': msg})

                sock.sendto(data, server_address)


sock.close()