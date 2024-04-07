import server
import socket

server_address = '0.0.0.0'
server_port = 9001
# ソケットの作成
server = server.Server(socket.AF_INET, socket.SOCK_DGRAM)
# アドレス紐付け
server.bind((server_address, server_port))
# 接続待ち
server.listen()