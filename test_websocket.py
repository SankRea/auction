import socket

HOST = '14.145.48.186'  # 服务器 IP
PORT = 5003              # 服务器端口

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    try:
        s.connect((HOST, PORT))
        s.sendall(b"Test connection")  # 只使用 ASCII 字符
        response = s.recv(1024)
        print("收到响应:", response.decode())
    except ConnectionRefusedError:
        print("连接失败: 服务器未启动或端口未开放")
    except Exception as e:
        print(f"发生错误: {e}")
