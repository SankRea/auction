import json
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, StringVar, messagebox
from tkinter import ttk
import os
import sys
import struct

class AuctionServer:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.clients = {}
        self.auction_items = self.load_items('auction_items.json')
        self.current_item = None
        self.current_bid = 10
        self.current_winner = None
        self.items_status = {}
        self.gui = None

    def load_items(self, filename):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        
        filepath = os.path.join(base_path, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def handle_client(self, conn, addr):
        print(f"客户端连接: {addr}")
        
        try:
            message = self.receive_message(conn)
            print(f"接收到的初始消息: {message}")
            username, balance_str = message.split(',')
            balance = int(balance_str) 
            self.clients[username] = {'conn': conn, 'balance': balance, 'won_items': []}
            self.update_client_list()
            while True:
                message = self.receive_message(conn)
                print(f"接收到的消息: {message}")
                if message == 'EXIT':
                    print(f"处理退出请求: {username}")
                    del self.clients[username]
                    conn.close()
                    print(f"客户端断开连接: {addr}")
                    self.update_client_list()
                    break
                elif message.startswith('BID'):
                    self.process_bid(username, message)
                elif message.startswith('BALANCE'):
                    try:
                        balance = int(message.split()[1])
                        self.clients[username]['balance'] = balance
                        self.update_client_list()
                    except (IndexError, ValueError) as e:
                        print(f"处理余额更新时发生错误: {e}")
                        conn.send("ERROR: 余额格式不正确".encode())
                else:
                    print(f"接收到未知命令: {message}")
                    conn.send("ERROR: 未知命令".encode())
        except Exception as e:
            print(f"处理客户端 {addr} 时发生错误: {e}")
            conn.send("ERROR: 处理请求时发生错误".encode())
        finally:
            if conn:
                conn.close()

    def start_auction(self, category, item):
        self.current_item = item
        self.current_bid = 10
        self.current_winner = None
        self.items_status[item] = {'item_sold': False, 'current_bid': self.current_bid}
        self.notify_clients(f"ITEM: '{self.current_item}' 起拍价为 {self.current_bid}。")
        self.notify_clients(f"拍卖开始: '{self.current_item}' 起拍价为 {self.current_bid}。")
        print(f"拍卖开始: '{self.current_item}' 起拍价为 {self.current_bid}。")
        self.update_gui()

    def process_bid(self, username, message):
        if self.current_item is None:
            self.send_message(self.clients[username]['conn'], "当前没有进行中的拍卖，无法出价。")
            return

        item_status = self.items_status[self.current_item]

        if item_status['item_sold']:
            self.send_message(self.clients[username]['conn'], "该商品已成交，无法出价。")
            return

        try:
            bid_amount = int(message.split()[1])
            if bid_amount > item_status['current_bid'] and bid_amount <= self.clients[username]['balance']:
                item_status['current_bid'] = bid_amount
                self.current_winner = username 
                print(f"{username} 出价 {bid_amount}. 当前最高出价者: {self.current_winner}")
                self.notify_clients(f"{username} 是当前的最高出价者")
                self.update_gui() 
            else:
                self.send_message(self.clients[username]['conn'], "出价过低或余额不足。")
        except ValueError:
            self.send_message(self.clients[username]['conn'], "出价格式无效。")

    def complete_transaction(self):
        if self.current_winner:
            winner = self.current_winner
            item = self.current_item
            final_price = self.items_status[item]['current_bid']
            
            if self.clients[winner]['balance'] >= final_price:
                self.clients[winner]['balance'] -= final_price
                self.clients[winner]['won_items'].append(item)
                print(f"{winner} 赢得了商品 '{item}'")
                self.send_message(self.clients[winner]['conn'], f"WINNER {item}")
                self.send_message(self.clients[winner]['conn'], f"SUCCEED {final_price} ")
                print(f"交易成功: {item}，成交价: {final_price} 元，{winner} 的新余额: {self.clients[winner]['balance']} 元。")
                self.notify_clients(f"赢家{winner} 赢得了商品 '{item}'")
                self.notify_clients("END_OF_AUCTION")
                self.items_status[item]['item_sold'] = True
                self.gui.update_transaction_info(item, final_price)
            else:
                self.notify_clients(f"{winner} 余额不足，无法完成交易。")
                print(f"{winner} 余额不足，当前余额为 {self.clients[winner]['balance']}")
        else:
            self.notify_clients(f"商品 '{self.current_item}' 无人竞拍。")
        
        self.current_winner = None
        self.current_item = None
        self.current_bid = 10

    def notify_clients(self, message):
        for client in self.clients.values():
            self.send_message(client['conn'], message)

    def send_message(self, conn, message):
        message_bytes = message.encode('utf-8')
        message_length = struct.pack('>I', len(message_bytes)) 
        conn.sendall(message_length + message_bytes)

    def receive_message(self, conn):
        length_bytes = conn.recv(4)
        if not length_bytes:
            return None
        message_length = struct.unpack('>I', length_bytes)[0]
        message_bytes = conn.recv(message_length)
        return message_bytes.decode('utf-8')

    def update_gui(self):
        if self.gui:
            self.gui.update_auction_info(self.current_item, self.current_bid, self.current_winner)

    def update_client_list(self):
        if self.gui:
            client_info = [f"{username}: {client['balance']}" for username, client in self.clients.items()]
            self.gui.update_client_list(client_info)

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print("服务器正在监听...")
            while True:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr)).start()

    def set_gui(self, gui):
        self.gui = gui





class AuctionServerGUI(tk.Tk):
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.title("拍卖服务器")
        self.geometry("800x600") 
        self.configure(bg="#eaeaea")

        self.category_var = StringVar(self)
        self.item_var = StringVar(self)

        self.category_label = tk.Label(self, text="选择商品大类", bg="#eaeaea", font=("Arial", 12))
        self.category_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.category_menu = ttk.Combobox(self, textvariable=self.category_var, state="readonly", font=("Arial", 12))
        self.category_menu.grid(row=0, column=1, padx=10, pady=10)
        self.category_menu.bind("<<ComboboxSelected>>", self.load_items)

        self.item_label = tk.Label(self, text="选择商品", bg="#eaeaea", font=("Arial", 12))
        self.item_label.grid(row=1, column=0, padx=10, pady=10)
        
        self.item_menu = ttk.Combobox(self, textvariable=self.item_var, state="readonly", font=("Arial", 12))
        self.item_menu.grid(row=1, column=1, padx=10, pady=10)

        self.auction_info = scrolledtext.ScrolledText(self, state='disabled', width=50, height=15, font=("Arial", 10))
        self.auction_info.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

        self.transaction_info = scrolledtext.ScrolledText(self, state='disabled', width=30, height=10, font=("Arial", 10))
        self.transaction_info.grid(row=2, column=2, padx=10, pady=10)

        self.completed_transactions_info = scrolledtext.ScrolledText(self, state='disabled', width=30, height=10, font=("Arial", 10))
        self.completed_transactions_info.grid(row=3, column=2, padx=10, pady=10)

        self.client_label = tk.Label(self, text="在线客户:", bg="#eaeaea", font=("Arial", 12))
        self.client_label.grid(row=0, column=2, padx=10, pady=10)
        
        self.client_list = tk.Listbox(self, width=30, height=15, font=("Arial", 12))
        self.client_list.grid(row=1, column=2, rowspan=2, padx=10, pady=10)

        self.start_button = tk.Button(self, text="开始拍卖", command=self.start_auction, font=("Arial", 12), bg="#4CAF50", fg="white")
        self.start_button.grid(row=3, column=0, padx=10, pady=10)

        self.transaction_button = tk.Button(self, text="交易", command=self.complete_transaction, font=("Arial", 12), bg="#008CBA", fg="white")
        self.transaction_button.grid(row=3, column=1, padx=10, pady=10)

        self.server.set_gui(self)
        self.load_categories()

    def load_categories(self):
        categories = list(self.server.auction_items.keys())
        self.category_menu['values'] = categories
        self.category_var.set("")
        self.item_var.set("")
        self.item_menu['values'] = []

    def load_items(self, event=None):
        category = self.category_var.get()
        if category:
            items = self.server.auction_items[category]
            self.item_var.set("")
            self.item_menu['values'] = items
            if items:
                self.item_menu.current(0)

    def start_auction(self):
        category = self.category_var.get()
        item = self.item_var.get()
        if category and item:
            self.server.start_auction(category, item)

    def complete_transaction(self):
        self.server.complete_transaction()

    def update_auction_info(self, item, bid, winner):
        self.auction_info.configure(state='normal')
        self.auction_info.insert(tk.END, f"拍卖商品: '{item}'，起拍价: {bid}。当前最高出价者: {winner}\n")
        self.auction_info.configure(state='disabled')
        self.auction_info.yview(tk.END)

    def update_client_list(self, clients):
        self.client_list.delete(0, tk.END)
        for client in clients:
            self.client_list.insert(tk.END, client)

    def update_transaction_info(self, item, price):
        self.transaction_info.configure(state='normal')
        self.transaction_info.insert(tk.END, f"成交商品: '{item}'，成交价格: {price} 元\n")
        self.transaction_info.configure(state='disabled')
        self.transaction_info.yview(tk.END)

        self.completed_transactions_info.configure(state='normal')
        self.completed_transactions_info.insert(tk.END, f"已成交商品: '{item}'，成交价格: {price} 元\n")
        self.completed_transactions_info.configure(state='disabled')
        self.completed_transactions_info.yview(tk.END)


class StartupWindow(tk.Tk):
    def __init__(self, on_submit):
        super().__init__()
        self.title("启动设置")
        self.geometry("300x200")
        self.configure(bg="#f0f0f0")
        self.resizable(False, False)

        self.host_var = StringVar(self)
        self.port_var = StringVar(self)

        tk.Label(self, text="服务器 IP 地址", bg="#f0f0f0").pack(pady=5)
        tk.Entry(self, textvariable=self.host_var, width=30).pack(pady=5)

        tk.Label(self, text="服务器 端口", bg="#f0f0f0").pack(pady=5)
        port_entry = tk.Entry(self, textvariable=self.port_var, width=30)
        port_entry.pack(pady=5)

        self.host_var.set('172.16.0.3')
        self.port_var.set('5200')

        tk.Button(self, text="启动服务器", command=self.submit).pack(pady=20)

        self.on_submit = on_submit

    def submit(self):
        host = self.host_var.get() or '172.16.0.3'
        port = self.port_var.get() or '5200'
        if port.isdigit():
            port = int(port)
            self.destroy()
            self.on_submit(host, port)
        else:
            messagebox.showerror("错误", "端口号必须为数字！")


if __name__ == "__main__":
    def start_server(host, port):
        server = AuctionServer(host, port)
        auction_gui = AuctionServerGUI(server)
        threading.Thread(target=server.run, daemon=True).start()
        auction_gui.mainloop()

    StartupWindow(start_server).mainloop()
