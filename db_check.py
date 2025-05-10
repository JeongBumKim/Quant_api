import sqlite3
from datetime import datetime
import requests

DB_PATH = "btc_trades.db"

def add_summary_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS btc_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_btc REAL NOT NULL,
            average_buy_price REAL NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# 현재 BTC 시세 (USD)
def get_current_btc_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        response = requests.get(url)
        return float(response.json()['price'])
    except:
        print("❌ 비트코인 시세 조회 실패")
        return None

# 현재 환율 (USD → KRW)
def get_usd_to_krw():
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        return response.json()['rates']['KRW']
    except:
        print("❌ 환율 조회 실패")
        return None

# DB에서 전체 거래 내역 조회 및 수익 계산
def calculate_profit_krw():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT amount, price_per_btc FROM btc_trades")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("⚠️ 거래 내역이 없습니다.")
        return

    # 누적 매입 금액 및 수량 계산
    total_btc = sum(row[0] for row in rows)
    total_usd = sum(row[0] * row[1] for row in rows)
    average_price = total_usd / total_btc

    current_price = get_current_btc_price()
    usd_to_krw = get_usd_to_krw()

    if current_price is None or usd_to_krw is None:
        return

    current_total_krw = current_price * total_btc * usd_to_krw
    invested_total_krw = total_usd * usd_to_krw
    profit_krw = current_total_krw - invested_total_krw
    profit_rate = (profit_krw / invested_total_krw) * 100

    print("📊 현재 수익 분석 결과")
    print(f"📦 총 보유 수량: {total_btc:.5f} BTC")
    print(f"💸 평균 매입가: ${average_price:,.2f}")
    print(f"📈 현재 시세: ${current_price:,.2f} / ₩{current_price * usd_to_krw:,.0f}")
    print(f"📊 평가손익: {'+' if profit_krw >=0 else ''}₩{profit_krw:,.0f}")
    print(f"📊 수익률: {'+' if profit_rate >=0 else ''}{profit_rate:.2f}%")

    return average_price

def get_summary():
    """
    btc_summary 테이블에서 가장 최근의 요약 정보를 조회합니다.

    :return: 딕셔너리 형태의 요약 정보 (없으면 None)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT total_btc, average_buy_price, updated_at
        FROM btc_summary
        ORDER BY updated_at DESC
        LIMIT 1
    ''')
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'total_btc': row[0],
            'average_buy_price': row[1],
            'updated_at': row[2]
        }
    else:
        return None
    
def insert_summary(total_btc, average_buy_price):
    """
    btc_summary 테이블에 코인 총 보유량과 평균 매수 가격을 저장합니다.

    :param total_btc: 총 보유 코인 개수 (float)
    :param average_buy_price: 평균 매수 가격 (float)
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO btc_summary (total_btc, average_buy_price, updated_at)
        VALUES (?, ?, ?)
    ''', (total_btc, average_buy_price, now))
    conn.commit()
    conn.close()

def sell_coin(amount,price):
    total_coin = get_summary()['total_btc'] 
    if total_coin < amount :
        print("가지고 있는 코인 보다 많습니다.")
        return 
    remain_coin = total_coin - amount
    income = amount * price
    average_buy_price = calculate_profit_krw()
    insert_summary(remain_coin,average_buy_price)
    

# 실행
if __name__ == "__main__":

    sell_coin(1,10000)
    calculate_profit_krw()
    add_summary_table()
    print(get_summary())
