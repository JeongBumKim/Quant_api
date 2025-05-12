from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
from datetime import datetime
import requests

from db_check import *
class BitcoinApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.DB_PATH = "btc_trades.db"
        self.init_db()
        self.register_routes()

    # 🔹 DB 초기화
    def init_db(self):
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS btc_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                price_per_btc REAL NOT NULL,
                datetime TEXT NOT NULL,
                money REAL NOT NULL
                
            )
        ''')
        conn.commit()
        conn.close()

    # 🔹 현재 BTC 가격
    def get_current_btc_price(self):
        try:
            url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
            return float(requests.get(url).json()['price'])
        except:
            return None

    # 🔹 USD→KRW 환율
    def get_usd_to_krw(self):
        try:
            return requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()['rates']['KRW']
        except:
            return None

    # 🔹 시세 히스토리
    def get_historical_data_krw(self, days):
        try:
            url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}"
            res = requests.get(url).json()
            prices = res["prices"]
            rate = self.get_usd_to_krw()
            labels = [datetime.fromtimestamp(p[0] / 1000).strftime("%m-%d") for p in prices]
            data = [int(p[1] * rate) for p in prices]
            return labels, data
        except:
            return [], []

    # 🔹 거래 저장
    def save_trade(self, amount):
        price = self.get_current_btc_price()
        if price is None:
            return False
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO btc_trades (amount, price_per_btc, datetime) VALUES (?, ?, ?)",
                       (amount, price, now))
        conn.commit()
        conn.close()
        return True

    # 🔹 거래 이력 조회
    def get_trade_history(self):
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT datetime, amount, price_per_btc FROM btc_trades ORDER BY datetime DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    # 🔹 수익 계산
    def calculate_profit(self):
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT amount, price_per_btc FROM btc_trades")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None
        
        rate = self.get_usd_to_krw()

        total_btc = get_summary()['total_btc']
        total_usd = sum(row[0] * row[1] for row in rows)
        average_price = get_summary()['average_buy_price'] * rate
        

        current_price = self.get_current_btc_price() 
        

        if current_price is None or rate is None:
            return None

        current_total_krw = current_price * total_btc * rate
        invested_total_krw = average_price * total_btc
        profit = current_total_krw - invested_total_krw
        profit_rate = (profit / invested_total_krw) * 100
        total_money = get_summary()['money'] *rate
        print(total_money)
        total_asset  = total_money + total_btc * average_price

        return {
            'total_btc': total_btc,
            'average_price': average_price,
            'current_price': current_price,
            'rate': rate,
            'current_total_krw': current_total_krw,
            'invested_total_krw': invested_total_krw,
            'profit_krw': profit,
            'profit_rate': profit_rate,
            'total_asset': total_asset,
            'total_money' : total_money
        }

    # 🔹 라우팅 등록
    def register_routes(self):
        @self.app.route('/', methods=['GET', 'POST'])
        def index():
            if request.method == 'POST':

                amount = float(request.form['amount'])
                      
                action = request.form['action']  # "buy" 또는 "sell"
                if action == 'buy':
                   coin_controler(amount,self.get_current_btc_price(),1)
                else:
                   coin_controler(amount,self.get_current_btc_price(),0)

                return redirect('/')

            current_price = self.get_current_btc_price()
            rate = self.get_usd_to_krw()
            price_krw = int(current_price * rate) if current_price and rate else None
            profit_info = self.calculate_profit()
            trade_history = self.get_trade_history()

            return render_template("index.html",
                                   current_price=current_price,
                                   rate=rate,
                                   price_krw=price_krw,
                                   profit=profit_info,
                                   trade_history=trade_history)

        @self.app.route('/get_data')
        def get_data():
            days = request.args.get('days', default='7')
            labels, data = self.get_historical_data_krw(days)
            return jsonify({'labels': labels, 'data': data})

    # 🔹 실행
    def run(self):
        self.app.run(debug=True)

# 🔹 앱 실행
if __name__ == '__main__':
    app = BitcoinApp()
    app.run()
