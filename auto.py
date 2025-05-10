import sqlite3
from datetime import datetime
import requests

DB_PATH = "btc_trades.db"

# 📌 현재 비트코인 시세 가져오기
def get_current_btc_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        response = requests.get(url)
        return float(response.json()['price'])
    except:
        print("❌ BTC 시세 조회 실패")
        return None

# 📌 DB 연결 및 테이블 생성 (없을 경우에만)
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

# 📌 거래 저장 (시세 자동 반영)
def save_trade(amount):
    price_per_btc = get_current_btc_price()
    if price_per_btc is None:
        print("❌ 현재 시세를 불러오지 못해 거래 저장을 중단합니다.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO btc_trades (amount, price_per_btc, datetime)
        VALUES (?, ?, ?)
    ''', (amount, price_per_btc, now))
    conn.commit()
    conn.close()
    print(f"✅ 거래 저장 완료: {amount} BTC @ ${price_per_btc} | {now}")

# 📌 저장된 거래 내역 전체 출력
def show_all_trades():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM btc_trades')
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("⚠️ 저장된 거래 내역이 없습니다.")
    else:
        print("📄 저장된 거래 내역:")
        print(f"{'ID':<5}{'수량':<10}{'1BTC당 가격(USD)':<20}{'거래 시각'}")
        for row in rows:
            print(f"{row[0]:<5}{row[1]:<10.5f}${row[2]:<19.2f}{row[3]}")

# ✅ 예시 실행
if __name__ == "__main__":
    init_db()

    # 예시: 0.01 BTC 매수 (현재 시세로 자동 저장)
    save_trade(0.01)

    # 거래 내역 출력
    show_all_trades()
