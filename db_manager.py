import sqlite3
import datetime

def init_db():
    """데이터베이스와 테이블을 초기화합니다. (DDL)"""
    # trading_history.db 파일이 없으면 새로 만들고 연결합니다.
    conn = sqlite3.connect("trading_history.db")
    cursor = conn.cursor()
    
    # 매매 내역을 저장할 trades 테이블을 생성합니다.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_time TEXT NOT NULL,
            ticker TEXT NOT NULL,
            trade_type TEXT NOT NULL, -- 'BUY' 또는 'SELL'
            price REAL NOT NULL,      -- 체결 가격
            volume REAL NOT NULL      -- 체결 수량
        )
    ''')
    conn.commit()
    conn.close()

def log_trade(ticker, trade_type, price, volume):
    """매매가 발생할 때마다 DB에 기록을 남깁니다. (DML)"""
    conn = sqlite3.connect("trading_history.db")
    cursor = conn.cursor()
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 안전하게 데이터를 삽입(INSERT)하기 위해 ? 플레이스홀더를 사용합니다.
    cursor.execute('''
        INSERT INTO trades (trade_time, ticker, trade_type, price, volume)
        VALUES (?, ?, ?, ?, ?)
    ''', (now, ticker, trade_type, price, volume))
    
    conn.commit()
    conn.close()
    print(f"💾 [DB 기록 완료] {now} | {ticker} {trade_type} 저장됨")

def view_trades():
    """DB에 저장된 매매 기록을 예쁘게 출력해서 보여줍니다. (DML - SELECT)"""
    conn = sqlite3.connect("trading_history.db")
    cursor = conn.cursor()
    
    # trades 테이블의 모든 데이터를 가져오는 쿼리
    cursor.execute("SELECT * FROM trades ORDER BY id ASC")
    rows = cursor.fetchall()
    
    print("\n=== 📊 자동매매 거래 내역 (DB 조회) ===")
    print(f"{'ID':<4} | {'거래 시간':<20} | {'종목':<10} | {'구분':<5} | {'체결가(원)':<12} | {'수량'}")
    print("-" * 75)
    
    if not rows:
        print("아직 기록된 매매 내역이 없습니다.")
    else:
        for row in rows:
            # row[0]=id, row[1]=time, row[2]=ticker, row[3]=type, row[4]=price, row[5]=volume
            print(f"{row[0]:<4} | {row[1]:<20} | {row[2]:<10} | {row[3]:<5} | {row[4]:<15,.0f} | {row[5]:.6f}")
            
    conn.close()

# # ----- 테스트용 실행 코드 -----
# if __name__ == "__main__":
#     init_db() # 테이블이 없으면 생성
    
#     # 1. 테스트용 가짜 데이터 삽입 (원하지 않으면 주석 # 처리하셔도 됩니다)
#     log_trade("KRW-BTC", "BUY", 95000000, 0.005)
#     log_trade("KRW-ETH", "SELL", 4500000, 0.15)
    
#     # 2. 방금 넣은 데이터가 잘 들어갔는지 화면에 출력
#     view_trades()