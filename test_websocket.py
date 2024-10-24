import asyncio
import websockets
import json

async def auction_client():
    uri = "ws://localhost:8765"  # 拍卖员WebSocket服务器的地址
    async with websockets.connect(uri) as websocket:
        # 发送用户名以标识用户
        username = input("请输入您的用户名: ")
        
        while True:
            # 发送出价信息（示例，您可以根据实际需要修改）
            bid = input("请输入您的出价（或输入 'exit' 退出）: ")
            if bid.lower() == 'exit':
                break
            
            # 创建出价信息的JSON数据
            message = json.dumps({"username": username, "bid": float(bid)})
            await websocket.send(message)

            # 等待并打印服务器的响应
            try:
                response = await websocket.recv()
                response_data = json.loads(response)
                if 'highest_bidder' in response_data:
                    print(f"当前最高出价者: {response_data['highest_bidder']} 出价: {response_data['highest_bid']}")
                elif 'error' in response_data:
                    print(response_data['error'])
            except websockets.ConnectionClosed:
                print("与服务器的连接已关闭。")
                break

if __name__ == "__main__":
    asyncio.run(auction_client())
