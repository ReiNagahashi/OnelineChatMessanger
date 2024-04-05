# ユーザ名を
import socket
import json
from collections import defaultdict

response = {
    'no_error': True,
    'message': '',
    'is_expired': False
}

# (ip_address, port_number): (user_name->string, chatted_last_time->string?)
# 時刻はm単位で登録する
# online_users = {}
# (ip_address, port_number): [時刻の文字列要素1, 時刻の文字列要素2, ...]
# messages = defaultdict(list)
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


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = '0.0.0.0'
server_port = 9001
print('starting up on port {}'.format(server_port))

sock.bind((server_address, server_port))



while True:
    print('\nwaiting to receive message')
    data, address = sock.recvfrom(4096)
    
    json_data = json.loads(data)

    if json_data['command'] == 'user_name': 
        if data_size_validation(json_data['parameters'], [255]):
            response['message'] = "Welcome to our message service"
            # 登録ユーザーを格納する辞書に保存, メッセージは空白で初期化
            # online_users[address] = (json_data['parameters']['user_name'])
    elif json_data['command'] == 'message':
        if data_size_validation(json_data['parameters'], [4096]):
            response['message'] = "Your message is accepted:)"

    sent = sock.sendto(json.dumps(response).encode('utf-8'), address)


