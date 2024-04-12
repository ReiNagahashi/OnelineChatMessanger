import server

server_address = '0.0.0.0'
server_port_udp = 9001
server_port_tcp = 9002

server = server.Server(server_address, server_port_udp, server_port_tcp)

server.listen()