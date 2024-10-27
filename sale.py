import tkinter as tk
from tkinter import messagebox
import json
import random

class AuctionApp:
    def __init__(self, root, items):
        self.root = root
        self.root.title("拍卖软件")

        self.current_price = 0
        self.highest_bidder = ""
        self.items = items
        self.current_item = self.get_random_item()

        self.countdown_time = 30
        self.countdown_active = False

        self.item_label = tk.Label(root, text=f"当前商品: {self.current_item}")
        self.item_label.pack()

        self.bid_label = tk.Label(root, text="当前价格: 0")
        self.bid_label.pack()

        self.timer_label = tk.Label(root, text=f"剩余时间: {self.countdown_time}s")
        self.timer_label.pack()

        self.bid_entry = tk.Entry(root)
        self.bid_entry.pack()

        self.bid_button = tk.Button(root, text="出价", command=self.place_bid)
        self.bid_button.pack()

        self.increment_buttons()

        self.winner_label = tk.Label(root, text="")
        self.winner_label.pack()

        self.start_countdown()

    def get_random_item(self):
        """从商品分类中随机获取一个商品"""
        category = random.choice(list(self.items.keys()))
        return random.choice(self.items[category])

    def increment_buttons(self):
        """创建加价快捷按钮 +1, +2, +3"""
        for i in range(1, 4):
            btn = tk.Button(self.root, text=f"+{i}", command=lambda i=i: self.increment_bid(i))
            btn.pack(side=tk.LEFT)

    def increment_bid(self, amount):
        """增加出价"""
        self.current_price += amount
        self.reset_countdown()
        self.update_bid()

    def place_bid(self):
        """处理出价逻辑"""
        try:
            bid = int(self.bid_entry.get())
            if bid > self.current_price:
                self.current_price = bid
                self.highest_bidder = f"出价者: {self.bid_entry.get()}"
                self.reset_countdown()
                self.update_bid()
            else:
                messagebox.showwarning("出价失败", "出价必须高于当前价格！")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的价格！")

    def update_bid(self):
        """更新当前出价和最高出价者"""
        self.bid_label.config(text=f"当前价格: {self.current_price}")
        self.winner_label.config(text=self.highest_bidder)

    def start_countdown(self):
        """启动倒计时"""
        self.countdown_active = True
        self.update_timer()

    def reset_countdown(self):
        """重置倒计时为30秒"""
        self.countdown_time = 30
        if not self.countdown_active:
            self.start_countdown()

    def update_timer(self):
        """更新倒计时并检查时间是否到"""
        if self.countdown_time > 0:
            self.timer_label.config(text=f"剩余时间: {self.countdown_time}s")
            self.countdown_time -= 1
            self.root.after(1000, self.update_timer)
        else:
            self.timer_label.config(text="时间到！")
            self.end_auction()

    def end_auction(self):
        """拍卖结束的逻辑"""
        if self.current_price > 0:
            messagebox.showinfo("拍卖结束", f"商品 {self.current_item} 被 {self.highest_bidder} 以 {self.current_price} 价格拍得。")
        else:
            messagebox.showinfo("拍卖结束", f"商品 {self.current_item} 未有人出价。")
        
        self.current_item = self.get_random_item()
        self.item_label.config(text=f"当前商品: {self.current_item}")

        self.current_price = 0
        self.highest_bidder = ""
        self.bid_label.config(text="当前价格: 0")
        self.winner_label.config(text="")
        
        self.reset_countdown()

def load_items_from_json(file_path):
    """从JSON文件中加载商品数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            items = json.load(file)
        return items
    except Exception as e:
        messagebox.showerror("加载失败", f"无法加载商品数据: {e}")
        return {}

if __name__ == "__main__":
    items = load_items_from_json('auction_items.json')
    
    if items:
        root = tk.Tk()
        app = AuctionApp(root, items)
        root.mainloop()
    else:
        print("未加载到商品数据，无法启动拍卖程序。")
