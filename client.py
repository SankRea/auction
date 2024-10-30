import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

class AuctionClient:
    def __init__(self):
        self.host = '116.198.198.29'
        self.port = 5200
        self.username = None
        self.balance = 1000
        self.won_items = []
        self.conn = None
        self.root = None
        self.current_item = "无"
        self.pending_bid = None

    def send_message(self, message):
        if isinstance(message, str):
            message_bytes = message.encode()
        elif isinstance(message, bytes):
            message_bytes = message
        else:
            raise ValueError("Message must be a string or bytes")

        message_length = len(message_bytes)
        length_prefix = message_length.to_bytes(4, byteorder='big')
        self.conn.send(length_prefix + message_bytes)


    def connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.conn.connect((self.host, self.port))
            print(f"发送消息: {self.username},{self.balance}")
            self.send_message(f"{self.username},{self.balance}".encode())
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.start()
            self.initial_window.destroy()
            self.start_auction_interface()
        except Exception as e:
            messagebox.showerror("连接错误", f"无法连接到服务器: {e}")

    def receive_messages(self):
        while True:
            try:
                
                length_prefix = self.conn.recv(4)
                if not length_prefix:
                    break 

                
                message_length = int.from_bytes(length_prefix, byteorder='big')

                
                message = self.conn.recv(message_length).decode()
                if message:
                    print(f"接收到的消息: {message}")
                    self.send_balance()
                    if message.startswith("ITEM"):
                        self.current_item = message.split("'")[1]
                        self.root.after(0, self.update_current_item)
                    elif message.startswith("WINNER"):
                        item_won = message.split()[1]
                        self.won_items.append(item_won)
                        self.root.after(0, self.update_won_items_display)
                    elif message.startswith("SUCCEED"):
                        print(f"接收到交易成功消息: {message}")
                        parts = message.split()
                        if len(parts) > 1:
                            amount = int(parts[1])
                            self.balance -= amount
                            self.balance_label.config(text=f"当前余额: {self.balance}")
                            print(f"交易成功: {amount} 元已从账户中扣除，当前余额为: {self.balance} 元。")
                        self.current_item = "无"
                        self.root.after(0, self.update_current_item)
                        self.pending_bid = None
                    elif message == "END_OF_AUCTION":
                        self.current_item = "无"
                        self.root.after(0, self.update_current_item)
                    else:
                        self.root.after(0, self.update_message_area, message)
                else:
                    break
            except Exception as e:
                print(f"接收数据时发生错误：{e}")
                messagebox.showerror("连接错误", f"接收数据时发生错误：{e}")
                self.conn.close()
                break

    def send_balance(self):
        self.send_message(f"BALANCE {self.balance}")

    def place_bid(self):
        bid = self.bid_entry.get()
        if bid.upper() == 'EXIT':
            self.send_message("EXIT")
            self.root.quit()
            return
        try:
            bid_amount = int(bid)
            if bid_amount > self.balance:
                messagebox.showwarning("无效出价", "您的出价超过当前余额。")
            else:
                self.send_message(f"BID {bid_amount}")
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
        self.initial_window.withdraw()
        messagebox.showinfo("提示", "本软件由折木制作，如有任何出现BUG的情况，算你倒霉")
        self.initial_window.title("拍卖客户端 - 启动界面")
        self.initial_window.geometry("400x300")
        self.initial_window.config(bg="#f0f0f0")

        tk.Label(self.initial_window, text="IP 地址:", bg="#f0f0f0", font=("Arial", 12)).grid(row=0, column=0, pady=5)
        self.ip_entry = tk.Entry(self.initial_window, font=("Arial", 12))
        self.ip_entry.insert(0, self.host)
        self.ip_entry.grid(row=0, column=1, pady=5)

        tk.Label(self.initial_window, text="端口号:", bg="#f0f0f0", font=("Arial", 12)).grid(row=1, column=0, pady=5)
        self.port_entry = tk.Entry(self.initial_window, font=("Arial", 12))
        self.port_entry.insert(0, str(self.port))
        self.port_entry.grid(row=1, column=1, pady=5)

        tk.Label(self.initial_window, text="用户名:", bg="#f0f0f0", font=("Arial", 12)).grid(row=2, column=0, pady=5)
        self.username_entry = tk.Entry(self.initial_window, font=("Arial", 12))
        self.username_entry.grid(row=2, column=1, pady=5)

        tk.Label(self.initial_window, text="起始资金:", bg="#f0f0f0", font=("Arial", 12)).grid(row=3, column=0, pady=5)
        self.balance_entry = tk.Entry(self.initial_window, font=("Arial", 12))
        self.balance_entry.insert(0, str(self.balance))
        self.balance_entry.grid(row=3, column=1, pady=5)

        tk.Button(self.initial_window, text="LINK START", command=self.start_connection, font=("Arial", 12)).grid(row=4, columnspan=2, pady=10)

        self.initial_window.deiconify()
        self.initial_window.mainloop()

    def start_connection(self):
        self.host = self.ip_entry.get() or self.host
        self.port = int(self.port_entry.get() or self.port)
        self.username = self.username_entry.get().strip()
        balance_input = self.balance_entry.get().strip()
        if not self.username:
            messagebox.showerror("输入错误", "用户名不能为空。")
            return
        try:
            self.balance = int(balance_input) if balance_input else self.balance
            self.connect()
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的起始资金。")
    def start_auction_interface(self):
        self.root = tk.Tk()
        self.root.title("拍卖客户端")
        self.root.geometry("600x500")
        self.root.config(bg="#e0e0e0")

        tk.Label(self.root, text="当前余额:", bg="#e0e0e0", font=("Arial", 12)).grid(row=0, column=0, pady=5)
        self.balance_label = tk.Label(self.root, text=f"当前余额: {self.balance}", bg="#e0e0e0", font=("Arial", 12))
        self.balance_label.grid(row=0, column=1, pady=5)

        self.current_item_label = tk.Label(self.root, text=f"当前拍卖商品: {self.current_item}", bg="#e0e0e0", font=("Arial", 12))
        self.current_item_label.grid(row=1, columnspan=2, pady=5)

        tk.Label(self.root, text="输入您的出价:", bg="#e0e0e0", font=("Arial", 12)).grid(row=2, column=0, pady=5)
        self.bid_entry = tk.Entry(self.root, font=("Arial", 12))
        self.bid_entry.grid(row=2, column=1, pady=5)

        tk.Button(self.root, text="出价", command=self.place_bid, font=("Arial", 12)).grid(row=2, column=2, pady=5)

        self.message_area = scrolledtext.ScrolledText(self.root, width=50, height=10, state=tk.DISABLED, font=("Arial", 12))
        self.message_area.grid(row=3, columnspan=3, pady=5)

        tk.Label(self.root, text="已赢得商品:", bg="#e0e0e0", font=("Arial", 12)).grid(row=4, column=0, pady=5)
        self.won_items_area = scrolledtext.ScrolledText(self.root, width=50, height=5, state=tk.DISABLED, font=("Arial", 12))
        self.won_items_area.grid(row=5, columnspan=3, pady=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        if messagebox.askokcancel("退出", "您确定要退出吗？"):
            self.send_message("EXIT".encode())
            self.root.quit()

    def run(self):
        self.create_startup_window()

if __name__ == "__main__":
    client = AuctionClient()
    client.run()
