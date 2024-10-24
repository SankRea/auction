import json
import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext


class AuctionServer:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.clients = {}
        self.auction_items = self.load_items('auction_items.json')
        self.current_item = None
        self.current_bid = 10  # 起拍价统一为10
        self.current_winner = None
        self.gui = None

    def load_items(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)

    def handle_client(self, conn, addr):
        print(f"Client connected: {addr}")
        username = conn.recv(1024).decode()
        self.clients[username] = {'conn': conn, 'balance': 1000, 'won_items': []}

        while True:
            message = conn.recv(1024).decode()
            if message == 'EXIT':
                del self.clients[username]
                conn.close()
                print(f"Client disconnected: {addr}")
                break
            elif message.startswith('BID'):
                self.process_bid(username, message)

    def process_bid(self, username, message):
        try:
            bid_amount = int(message.split()[1])
            if bid_amount > self.current_bid and bid_amount <= self.clients[username]['balance']:
                self.current_bid = bid_amount
                self.current_winner = username
                self.clients[username]['balance'] -= bid_amount
                print(f"{username} placed a bid of {bid_amount}. Current winner: {self.current_winner}")
                self.notify_clients(f"{username} is the current highest bidder with {bid_amount}.")
                self.update_gui()
            else:
                self.clients[username]['conn'].send("Bid too low or insufficient balance.".encode())
        except ValueError:
            self.clients[username]['conn'].send("Invalid bid format.".encode())

    def notify_clients(self, message):
        for client in self.clients.values():
            client['conn'].send(message.encode())

    def start_auction(self):
        category = list(self.auction_items.keys())[0]  # 选择第一个类别
        item = self.auction_items[category][0]  # 选择类别中的第一个商品
        self.current_item = item
        self.notify_clients(f"Auction started for '{self.current_item}' at {self.current_bid}.")
        print(f"Auction started for '{self.current_item}' at {self.current_bid}.")
        self.update_gui()

    def update_gui(self):
        if self.gui:
            self.gui.update_auction_info(self.current_item, self.current_bid, self.current_winner)

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print("Server is listening...")
            self.start_auction()
            while True:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr)).start()

    def set_gui(self, gui):
        self.gui = gui


class AuctionServerGUI(tk.Tk):
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.title("Auction Server")
        self.geometry("400x300")

        self.auction_info = scrolledtext.ScrolledText(self, state='disabled', width=40, height=10)
        self.auction_info.pack(pady=10)

        self.start_button = tk.Button(self, text="Start Auction", command=self.start_auction)
        self.start_button.pack(pady=5)

        self.server.set_gui(self)

    def start_auction(self):
        self.server.start_auction()

    def update_auction_info(self, item, bid, winner):
        self.auction_info.configure(state='normal')
        self.auction_info.insert(tk.END, f"Auction for '{item}' started at {bid}. Current winner: {winner}\n")
        self.auction_info.configure(state='disabled')
        self.auction_info.yview(tk.END)

if __name__ == '__main__':
    auction_server = AuctionServer()
    auction_gui = AuctionServerGUI(auction_server)
    threading.Thread(target=auction_server.run, daemon=True).start()
    auction_gui.mainloop()
