# strategy.py

import time
from typing import Optional
import pyupbit


def get_target_price(ticker: str, k: float = 0.5, max_retries: int = 3, retry_delay: float = 0.2) -> Optional[float]:
    """
    변동성 돌파 전략의 매수 목표가 계산
    목표가 = 오늘 시가 + (어제 고가 - 어제 저가) * k
    """
    for attempt in range(max_retries):
        try:
            df = pyupbit.get_ohlcv(ticker, interval="day", count=2)

            if df is None or len(df) < 2:
                raise ValueError("일봉 데이터를 충분히 가져오지 못했습니다.")

            yesterday = df.iloc[-2]
            today = df.iloc[-1]

            yesterday_high = float(yesterday["high"])
            yesterday_low = float(yesterday["low"])
            today_open = float(today["open"])

            target_price = today_open + (yesterday_high - yesterday_low) * k

            if target_price <= 0:
                raise ValueError("계산된 목표가가 비정상적입니다.")

            return target_price

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print(f"❌ [{ticker}] 목표가 계산 중 에러 발생: {e}")
                return None


def should_buy(current_price: float, target_price: Optional[float], balance: float, bought_today: bool) -> bool:
    """
    매수 여부 판단
    """
    if target_price is None:
        return False

    if bought_today:
        return False

    if balance > 0:
        return False

    return current_price >= target_price


def get_sell_signal(
    current_price: float,
    avg_buy_price: float,
    highest_price: float,
    stop_loss_rate: float = 0.03,
    trailing_stop_rate: float = 0.02,
):
    """
    손절 / 트레일링 스탑 매도 신호 판단

    Returns:
        signal (str | None): "STOP_LOSS", "TRAILING_STOP", None
        updated_highest_price (float): 갱신된 최고가
        stop_loss_price (float): 손절가
        trailing_stop_price (float): 트레일링 스탑가
    """
    if avg_buy_price is None or avg_buy_price <= 0:
        return None, highest_price, None, None

    updated_highest_price = max(highest_price, current_price, avg_buy_price)

    stop_loss_price = avg_buy_price * (1 - stop_loss_rate)
    trailing_stop_price = updated_highest_price * (1 - trailing_stop_rate)

    # 손절 우선
    if current_price <= stop_loss_price:
        return "STOP_LOSS", updated_highest_price, stop_loss_price, trailing_stop_price

    # 수익 구간에서만 트레일링 스탑 적용
    if updated_highest_price > avg_buy_price and current_price <= trailing_stop_price:
        return "TRAILING_STOP", updated_highest_price, stop_loss_price, trailing_stop_price

    return None, updated_highest_price, stop_loss_price, trailing_stop_price