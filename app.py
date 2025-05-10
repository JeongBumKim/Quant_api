from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
from datetime import datetime
import requests

app = Flask(__name__)
DB_PATH = "btc_trades.db"

# 🔹 API들
def get_current_btc_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        return float(requests.get(url).json()['price'])
    except:
        return None

def get_usd_to_krw():
    try:
        return requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()['rates']['KRW']
    except:
        return None

# 🔹 과거 시세 차트용 (기간: days)
def get_historical_data_krw(days):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}"
        res = requests.get(url).json()
        prices = res["prices"]
        rate = get_usd_to_krw()
        labels = [datetime.fromtimestamp(p[0] / 1000).strftime("%m-%d") for p in prices]
        data = [int(p[1] * rate) for p in prices]
        return labels, data
    except:
        return [], []

# 🔹 DB 초기화
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS btc_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            price_per_btc REAL NOT NULL,
            datetime TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# 🔹 거래 저장
def save_trade(amount):
    price = get_current_btc_price()
    if price is None:
        return False
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO btc_trades (amount, price_per_btc, datetime) VALUES (?, ?, ?)",
                   (amount, price, now))
    conn.commit()
    conn.close()
    return True

# 🔹 수익 계산
def calculate_profit():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT amount, price_per_btc FROM btc_trades")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    total_btc = sum(row[0] for row in rows)
    total_usd = sum(row[0] * row[1] for row in rows)
    average_price = total_usd / total_btc

    current_price = get_current_btc_price()
    rate = get_usd_to_krw()

    if current_price is None or rate is None:
        return None

    current_total_krw = current_price * total_btc * rate
    invested_total_krw = total_usd * rate
    profit = current_total_krw - invested_total_krw
    profit_rate = (profit / invested_total_krw) * 100

    return {
        'total_btc': total_btc,
        'average_price': average_price,
        'current_price': current_price,
        'rate': rate,
        'current_total_krw': current_total_krw,
        'invested_total_krw': invested_total_krw,
        'profit_krw': profit,
        'profit_rate': profit_rate
    }

# 🔹 메인 페이지
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        save_trade(amount)
        return redirect('/')

    current_price = get_current_btc_price()
    rate = get_usd_to_krw()
    price_krw = int(current_price * rate) if current_price and rate else None
    profit_info = calculate_profit()
    trade_history = get_trade_history()

    return render_template("index.html",
                           current_price=current_price,
                           rate=rate,
                           price_krw=price_krw,
                           profit=profit_info,
                           trade_history=trade_history)


# 🔹 AJAX 요청용 시세 데이터 API
@app.route('/get_data')
def get_data():
    days = request.args.get('days', default='7')
    labels, data = get_historical_data_krw(days)
    return jsonify({'labels': labels, 'data': data})

# 🔹 거래 이력 조회
def get_trade_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT datetime, amount, price_per_btc FROM btc_trades ORDER BY datetime DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# 🔹 index 라우트 수정


# 🔹 실행
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
