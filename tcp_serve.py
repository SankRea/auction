import socket

HOST = '0.0.0.0'  # 监听所有可用的接口，包括公网 IP
PORT = 8080       # 监听的端口

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"服务器正在运行，监听 {HOST}:{PORT}...")
        
        while True:
            try:
                conn, addr = server_socket.accept()
                with conn:
                    print(f"连接来自: {addr}")
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break
                        print(f"收到消息: {data.decode()}")
                        conn.sendall("消息已接收".encode('utf-8'))  # 使用 encode 转换字符串为字节
            except Exception as e:
                print(f"发生错误: {e}")

if __name__ == "__main__":
    start_server()