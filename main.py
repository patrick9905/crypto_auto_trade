import time
import datetime
import os
import pyupbit
from dotenv import load_dotenv
from strategy import get_target_price
from db_manager import init_db, log_trade

# 1. API 로그인 세팅
load_dotenv()
access = os.getenv("UPBIT_ACCESS_KEY")
secret = os.getenv("UPBIT_SECRET_KEY")
upbit = pyupbit.Upbit(access, secret)

# 2. 프로그램 시작 전 DB 점검 및 변수 세팅
init_db()
ticker = "KRW-BTC" # 우선 비트코인 하나에 집중!
target_price = get_target_price(ticker, 0.5) # 시작할 때 목표가 장전
print("🚀 변동성 돌파 자동매매 봇을 시작합니다... (DB 연동 완료)")
print(f"✅ 오늘의 목표가: {target_price:,.0f} 원")

# 3. 24시간 무한 루프 시작
is_holding = False    # 현재 코인을 들고 있는지 여부
buy_price = 0.0       # 내가 산 가격
highest_price = 0.0   # 사고 나서 찍은 최고가

while True:
    try:
        now = datetime.datetime.now()
        
        # 매일 아침 9시에 목표가 갱신 및 변수 초기화
        if now.hour == 9 and now.minute == 0 and (0 <= now.second < 10):
            target_price = get_target_price(ticker, 0.5)
            is_holding = False
            print(f"[{now}] 🎯 새로운 하루! 목표가 갱신: {target_price:,.0f}원")
            time.sleep(10) # 10초 동안 대기 (중복 실행 방지)

        current_price = pyupbit.get_current_price(ticker)

        # 🟢 [매수 로직] 코인을 안 들고 있을 때
        if not is_holding:
            if current_price >= target_price:
                krw = upbit.get_balance("KRW") # 👈 내 원화 잔고 확인 (수정완료)
                if krw > 5000: # 최소 주문 금액 5000원 이상일 때만
                    print(f"[{now}] 🚀 목표가 돌파! 매수 실행!")
                    # 수수료(0.05%) 낼 돈은 남겨두고 99.95%만 매수 (에러 방지)
                    upbit.buy_market_order(ticker, krw * 0.9995) 
                    
                    # 변수 업데이트 (머릿속에 기억하기)
                    buy_price = current_price
                    highest_price = current_price
                    is_holding = True
                    print(f"매수가: {buy_price:,.0f}원")
                    
                    # DB 장부에 기록 (필요 시 주석 해제)
                    # log_trade(ticker, "BUY", buy_price, krw * 0.9995)

        # 🔴 [매도 로직] 코인을 들고 있을 때 (익절 & 손절 감시)
        else:
            # 1. 최고가 갱신 (지금 가격이 역대급인지 매번 갱신)
            highest_price = max(highest_price, current_price)
            btc_balance = upbit.get_balance(ticker) # 내 비트코인 개수 확인

            # 2. 손절 (-3%)
            if current_price <= buy_price * 0.97:
                print(f"[{now}] 😭 -3% 손절! 매도 실행! (매도가: {current_price:,.0f}원)")
                upbit.sell_market_order(ticker, btc_balance)
                is_holding = False
                # log_trade(ticker, "SELL_STOPLOSS", current_price, btc_balance)

            # 3. 트레일링 스탑 익절 (최고점 대비 -2% 하락 시)
            elif current_price <= highest_price * 0.98:
                print(f"[{now}] 💰 고점 대비 -2% 하락! 수익 실현(익절)! (매도가: {current_price:,.0f}원)")
                upbit.sell_market_order(ticker, btc_balance)
                is_holding = False
                # log_trade(ticker, "SELL_PROFIT", current_price, btc_balance)

            # 4. 시간 청산 (다음날 아침 8시 59분 50초에 무조건 매도)
            elif now.hour == 8 and now.minute == 59 and now.second > 50:
                print(f"[{now}] ⏰ 일봉 마감 전 시간 청산! 전량 매도! (매도가: {current_price:,.0f}원)")
                upbit.sell_market_order(ticker, btc_balance)
                is_holding = False
                # log_trade(ticker, "SELL_TIME", current_price, btc_balance)
                time.sleep(10)

        time.sleep(1) # 1초에 한 번씩 감시 (업비트 쫓겨남 방지)

    except Exception as e:
        print(f"에러 발생: {e}")
        time.sleep(1)