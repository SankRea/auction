import socket

HOST = '116.198.198.29'
PORT = 5200

def test_connection():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            s.sendall("测试连接".encode('utf-8'))
            response = s.recv(1024)
            print("收到响应:", response.decode('utf-8'))
        except ConnectionRefusedError:
            print("连接失败: 服务器未启动或端口未开放")
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == "__main__":
    test_connection()
