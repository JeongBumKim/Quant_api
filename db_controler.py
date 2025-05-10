import sqlite3

DB_PATH = "btc_trades.db"

def delete_trades_in_range(start_id, end_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM btc_trades WHERE id BETWEEN ? AND ?",
        (start_id, end_id)
    )
    conn.commit()
    conn.close()
    print(f"🗑️ 거래 ID {start_id}번부터 {end_id}번까지 삭제 완료.")

# ✅ 예시 실행
if __name__ == "__main__":
    delete_trades_in_range(1, 10)  # 원하는 범위로 조정하세요
