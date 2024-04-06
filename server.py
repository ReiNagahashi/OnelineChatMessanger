import socket
import json
from collections import defaultdict
import time
import select

response = {
    'no_error': True,
    'message': '',
    'is_expired': False
}

# (ip_address, port_number): (user_name->string, chatted_last_time->float)

# この値を過ぎてしまうと、ユーザはonline_usersから削除されてクライアント側でソケットが自動で閉じられる
valid_duration = 10 #sec

# [0]:ユーザー名、[1]:最後のメッセージの時間
online_users = {}
# (ip_address, port_number): [時刻の文字列要素1, 時刻の文字列要素2, ...]
messages = defaultdict(list)
# 第一引数："parameters"のディクショナリ, 第二引数：parametersの各要素の制限メモリを持ったリスト
def data_size_validation(parameters, limits):
    # ユーザー名は255bytes, 'message'であれば4096bytesを最大にしてバリデーションをする
    param_sizes = parameters.values()
    for param_size, limit in zip(param_sizes, limits):
        # バイトサイズで比較するために、バイト型に変更
        if len(param_size.encode('utf-8')) > limit:
            response['no_error'] = False
            response['message'] = "Error: One of parameters exceeds the limitation! Try again."
            return False

    response['no_error'] = True
    print("Data size validation Succeeded!!")
    return True

def check_expired_users():
    print(online_users)
    # pythonではディクショナリデータをそのままイテレートした上で削除処理をしたらランタイムエラーになる→リストでコピーを作る必要がある
    for key, values in list(online_users.items()):
        last_time = values[1]
        if time.time() - last_time > valid_duration:
            del online_users[key]
    print("check_expired_users func is completed!")
    print(online_users)


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = '0.0.0.0'
server_port = 9001
print('starting up on port {}'.format(server_port))

sock.bind((server_address, server_port))


# どのクライアントからもメッセージがない場合は、n秒をタイムアウト期限に設定して、n秒経ったらonline_usersから削除する関数を実行する
# クライアントからメッセージがあった場合でも、最後の処理で削除処理をする

while True:
    print('\nwaiting to receive message')

    readable, writable, exceptional = select.select([sock], [], [], 5.0)
    if not (readable or writable or exceptional):
        pass
    else:
        data, address = sock.recvfrom(4096)

        current_time = time.time()
        
        json_data = json.loads(data)

        if json_data['command'] == 'user_name': 
            if data_size_validation(json_data['parameters'], [255]):
                response['message'] = "Welcome to our message service"
                # 登録ユーザーを格納する辞書に保存, メッセージは空白で初期化
                online_users[address] = [json_data['parameters']['user_name'], 0.0]
        elif json_data['command'] == 'message':
            if data_size_validation(json_data['parameters'], [4096]):
                response['message'] = f"{online_users[address][0]}: {json_data['parameters']['message']}"
        online_users[address][1] = current_time

        sent = sock.sendto(json.dumps(response).encode('utf-8'), address)
        
    check_expired_users()


