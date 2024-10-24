import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

class AuctionClient:
    def __init__(self):
        self.host = None
        self.port = None
        self.username = None
        self.balance = 1000
        self.won_items = []
        self.conn = None
        self.root = None
        self.current_item = "无"
        self.pending_bid = None

    def connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.conn.connect((self.host, self.port))
            self.conn.send(self.username.encode())
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.start()
            self.initial_window.destroy()  # 关闭启动界面
            self.start_auction_interface()  # 打开拍卖界面
        except Exception as e:
            messagebox.showerror("连接错误", f"无法连接到服务器: {e}")

    def receive_messages(self):
        while True:
            try:
                message = self.conn.recv(1024).decode()
                if message:
                    print(f"接收到的消息: {message}")
                    
                    if message.startswith("ITEM"):
                        self.current_item = message[5:]
                        self.root.after(0, self.update_current_item)
                    elif message.startswith("WINNER"):
                        item_won = message.split()[1]
                        self.won_items.append(item_won)
                        self.root.after(0, self.update_won_items_display)
                    elif message.startswith("交易成功"):
                        parts = message.split()
                        if len(parts) > 1:
                            amount = int(parts[1])
                            self.balance -= amount
                            self.balance_label.config(text=f"当前余额: {self.balance}")
                            print(f"交易成功: {amount} 元已从账户中扣除，当前余额为: {self.balance} 元。")
                        self.pending_bid = None
                    else:
                        self.root.after(0, self.update_message_area, message)
                else:
                    break
            except Exception as e:
                print(f"接收数据时发生错误：{e}") 
                messagebox.showerror("连接错误", f"接收数据时发生错误：{e}")
                self.conn.close()
                break

    def place_bid(self):
        bid = self.bid_entry.get()
        if bid.upper() == 'EXIT':
            self.conn.send("EXIT".encode())
            self.root.quit()
            return
        try:
            bid_amount = int(bid)
            if bid_amount > self.balance:
                messagebox.showwarning("无效出价", "您的出价超过当前余额。")
            else:
                self.conn.send(f"BID {bid_amount}".encode())
                self.pending_bid = bid_amount
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字。")

    def update_message_area(self, message):
        self.message_area.config(state=tk.NORMAL)
        self.message_area.insert(tk.END, f"服务器: {message}\n")
        self.message_area.see(tk.END)
        self.message_area.config(state=tk.DISABLED)

    def update_won_items_display(self):
        self.won_items_area.config(state=tk.NORMAL)
        self.won_items_area.delete(1.0, tk.END)
        for item in self.won_items:
            self.won_items_area.insert(tk.END, f"{item}\n")
        self.won_items_area.see(tk.END)
        self.won_items_area.config(state=tk.DISABLED)

    def update_current_item(self):
        self.current_item_label.config(text=f"当前拍卖商品: {self.current_item}")

    def create_startup_window(self):
        self.initial_window = tk.Tk()
        self.initial_window.title("拍卖客户端 - 启动界面")

        tk.Label(self.initial_window, text="IP 地址:").grid(row=0, column=0)
        self.ip_entry = tk.Entry(self.initial_window)
        self.ip_entry.grid(row=0, column=1)

        tk.Label(self.initial_window, text="端口号:").grid(row=1, column=0)
        self.port_entry = tk.Entry(self.initial_window)
        self.port_entry.grid(row=1, column=1)

        tk.Label(self.initial_window, text="用户名:").grid(row=2, column=0)
        self.username_entry = tk.Entry(self.initial_window)
        self.username_entry.grid(row=2, column=1)

        tk.Button(self.initial_window, text="连接", command=self.start_connection).grid(row=3, columnspan=2)

        self.initial_window.mainloop()

    def start_connection(self):
        self.host = self.ip_entry.get()
        self.port = int(self.port_entry.get())
        self.username = self.username_entry.get()
        self.connect()

    def start_auction_interface(self):
        self.root = tk.Tk()
        self.root.title("拍卖客户端")

        tk.Label(self.root, text="当前余额:").grid(row=0, column=0)
        self.balance_label = tk.Label(self.root, text=f"当前余额: {self.balance}")
        self.balance_label.grid(row=0, column=1)

        self.current_item_label = tk.Label(self.root, text=f"当前拍卖商品: {self.current_item}")
        self.current_item_label.grid(row=1, columnspan=2)

        tk.Label(self.root, text="输入您的出价:").grid(row=2, column=0)
        self.bid_entry = tk.Entry(self.root)
        self.bid_entry.grid(row=2, column=1)

        tk.Button(self.root, text="出价", command=self.place_bid).grid(row=2, column=2)

        self.message_area = scrolledtext.ScrolledText(self.root, width=40, height=10, state=tk.DISABLED)
        self.message_area.grid(row=3, columnspan=3)

        tk.Label(self.root, text="已赢得商品:").grid(row=4, column=0)
        self.won_items_area = scrolledtext.ScrolledText(self.root, width=40, height=5, state=tk.DISABLED)
        self.won_items_area.grid(row=5, columnspan=3)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        if messagebox.askokcancel("退出", "您确定要退出吗？"):
            self.conn.send("EXIT".encode())
            self.root.quit()

    def run(self):
        self.create_startup_window()

if __name__ == '__main__':
    client = AuctionClient()
    client.run()
