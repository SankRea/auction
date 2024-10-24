import json
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, StringVar, messagebox
from tkinter import ttk
import os
import sys

class AuctionServer:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.clients = {}
        self.auction_items = self.load_items('auction_items.json')
        self.current_item = None
        self.current_bid = 10
        self.current_winner = None
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
        username = conn.recv(1024).decode()
        self.clients[username] = {'conn': conn, 'balance': 1000, 'won_items': []}

        self.update_client_list()
        
        while True:
            message = conn.recv(1024).decode()
            if message == 'EXIT':
                del self.clients[username]
                conn.close()
                print(f"客户端断开连接: {addr}")
                self.update_client_list()
                break
            elif message.startswith('BID'):
                self.process_bid(username, message)

    def process_bid(self, username, message):
        try:
            bid_amount = int(message.split()[1])
            if bid_amount > self.current_bid and bid_amount <= self.clients[username]['balance']:
                self.current_bid = bid_amount
                self.current_winner = username
                print(f"{username} 出价 {bid_amount}. 当前最高出价者: {self.current_winner}")
                self.notify_clients(f"{username} 是当前的最高出价者，出价 {bid_amount}。")
                self.notify_clients(f"ITEM {self.current_item}")
                self.update_gui()
            else:
                self.clients[username]['conn'].send("出价过低或余额不足。".encode())
        except ValueError:
            self.clients[username]['conn'].send("出价格式无效。".encode())

    def notify_clients(self, message):
        for client in self.clients.values():
            client['conn'].send(message.encode())

    def start_auction(self, category, item):
        self.current_item = item
        self.current_bid = 10
        self.current_winner = None
        self.notify_clients(f"拍卖开始: '{self.current_item}' 起拍价为 {self.current_bid}。")
        print(f"拍卖开始: '{self.current_item}' 起拍价为 {self.current_bid}。")
        self.update_gui()

    def complete_transaction(self):
        if self.current_winner:
            winner = self.current_winner
            item = self.current_item
            final_price = self.current_bid
            
            if self.clients[winner]['balance'] >= final_price:
                self.clients[winner]['balance'] -= final_price
                self.clients[winner]['won_items'].append(item)
                print(f"{winner} 赢得了商品 '{item}'，成交价为 {final_price}。")
                self.clients[winner]['conn'].send(f"WINNER {item}".encode())
                self.clients[winner]['conn'].send(f"交易成功 {final_price}".encode())
                self.clients[winner]['conn'].send(" ".encode())
                self.notify_clients(f"{winner} 赢得了商品 '{item}'，成交价为 {final_price}。")
            else:
                self.notify_clients(f"{winner} 余额不足，无法完成交易。")
                print(f"{winner} 余额不足，当前余额为 {self.clients[winner]['balance']}")
        else:
            self.notify_clients(f"商品 '{self.current_item}' 无人竞拍。")

    def update_gui(self):
        if self.gui:
            self.gui.update_auction_info(self.current_item, self.current_bid, self.current_winner)

    def update_client_list(self):
        if self.gui:
            self.gui.update_client_list(list(self.clients.keys()))

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
        self.geometry("600x400")
        self.configure(bg="#f0f0f0")

        self.category_var = StringVar(self)
        self.item_var = StringVar(self)

        self.category_label = tk.Label(self, text="选择商品大类", bg="#f0f0f0")
        self.category_label.grid(row=0, column=0, padx=5, pady=5)
        self.category_menu = ttk.Combobox(self, textvariable=self.category_var, state="readonly")
        self.category_menu.grid(row=0, column=1, padx=5, pady=5)
        self.category_menu.bind("<<ComboboxSelected>>", self.load_items)

        self.item_label = tk.Label(self, text="选择商品", bg="#f0f0f0")
        self.item_label.grid(row=1, column=0, padx=5, pady=5)
        self.item_menu = ttk.Combobox(self, textvariable=self.item_var, state="readonly")
        self.item_menu.grid(row=1, column=1, padx=5, pady=5)

        self.auction_info = scrolledtext.ScrolledText(self, state='disabled', width=40, height=10)
        self.auction_info.grid(row=2, column=0, columnspan=2, padx=5, pady=10)

        self.client_label = tk.Label(self, text="在线客户:", bg="#f0f0f0")
        self.client_label.grid(row=0, column=2, padx=5, pady=5)
        self.client_list = tk.Listbox(self, width=20, height=15)
        self.client_list.grid(row=1, column=2, rowspan=2, padx=5, pady=5)

        self.start_button = tk.Button(self, text="开始拍卖", command=self.start_auction)
        self.start_button.grid(row=3, column=0, padx=5, pady=5)

        self.transaction_button = tk.Button(self, text="交易", command=self.complete_transaction)
        self.transaction_button.grid(row=3, column=1, padx=5, pady=5)

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

        tk.Button(self, text="提交", command=self.submit).pack(pady=20)

        self.on_submit = on_submit

    def submit(self):
        host = self.host_var.get()
        port = self.port_var.get()

        # 输入验证
        if not host or not port:
            messagebox.showwarning("输入错误", "IP 地址和端口不能为空。")
            return

        try:
            port = int(port)
            if not (1 <= port <= 65535):
                raise ValueError("端口必须在 1 到 65535 之间。")
        except ValueError as e:
            messagebox.showerror("输入错误", str(e))
            return

        threading.Thread(target=self.on_submit, args=(host, port)).start()
        self.destroy()


def start_auction_server(host, port):
    auction_server = AuctionServer(host, port)
    auction_gui = AuctionServerGUI(auction_server)
    threading.Thread(target=auction_server.run, daemon=True).start()
    auction_gui.mainloop()


if __name__ == '__main__':
    startup_window = StartupWindow(start_auction_server)
    startup_window.mainloop()
