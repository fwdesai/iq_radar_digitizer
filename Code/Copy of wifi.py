import socket
import time

FILE = 'data.txt'

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s_addr = ('192.168.3.28', 12345)

time.sleep(2)
message = 'SEND DATA'
client_socket.sendto(message.encode(), s_addr)

with open(FILE, 'w', buffering=1024) as f:
    while True:
        data, addr = client_socket.recvfrom(8)
        if (data.decode() == 'FINISHED'):
            f.flush()
            break
        f.write(str(data.decode()) + '\n')
