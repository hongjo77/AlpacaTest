import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Alpaca 클라이언트 초기화
trading_client = TradingClient(
    api_key=os.getenv("ALPACA_API_KEY"),
    secret_key=os.getenv("ALPACA_SECRET_KEY"),
    paper=True  # Paper Trading 모드
)


def get_account_info():
    """계좌 정보 조회"""
    account = trading_client.get_account()
    return {
        "success": True,
        "cash": float(account.cash),
        "portfolio_value": float(account.portfolio_value),
        "buying_power": float(account.buying_power),
        "equity": float(account.equity),
    }


def get_positions():
    """현재 보유 포지션 조회"""
    positions = trading_client.get_all_positions()
    result = []
    for position in positions:
        result.append({
            "symbol": position.symbol,
            "qty": float(position.qty),
            "avg_entry_price": float(position.avg_entry_price),
            "current_price": float(position.current_price),
            "market_value": float(position.market_value),
            "unrealized_pl": float(position.unrealized_pl),
            "unrealized_plpc": float(position.unrealized_plpc),
        })
    return {"success": True, "positions": result}


def place_market_order(ticker: str, quantity: int, side: str):
    """
    시장가 주문 실행
    
    Args:
        ticker: 주식 심볼 (예: 'AAPL')
        quantity: 수량
        side: 'buy' 또는 'sell'
    """
    try:
        order_side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
        
        market_order_data = MarketOrderRequest(
            symbol=ticker,
            qty=quantity,
            side=order_side,
            time_in_force=TimeInForce.DAY
        )
        
        order = trading_client.submit_order(order_data=market_order_data)
        
        return {
            "success": True,
            "order_id": order.id,
            "symbol": order.symbol,
            "qty": float(order.qty),
            "side": order.side,
            "status": order.status,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def calculate_position_size(ticker: str, allocation_percent: float):  # 기본값 제거!
    """
    포트폴리오 대비 적절한 매수 수량 계산
    
    Args:
        ticker: 주식 심볼
        allocation_percent: 포트폴리오의 몇 %를 투자할지
    """
    import yfinance as yf
    
    account = trading_client.get_account()
    buying_power = float(account.buying_power)
    
    stock = yf.Ticker(ticker)
    current_price = stock.info.get('currentPrice', 0)
    
    if current_price == 0:
        return {"success": False, "error": "Could not get current price"}
    
    invest_amount = buying_power * (allocation_percent / 100)
    quantity = int(invest_amount / current_price)
    
    return {
        "success": True,
        "ticker": ticker,
        "current_price": current_price,
        "quantity": quantity,
        "estimated_cost": quantity * current_price,
        "allocation_percent": allocation_percent,
    }

def monitor_positions_and_manage_risk():
    """
    모든 포지션 체크해서 손절/익절 자동 실행
    """
    positions = get_positions()
    
    for pos in positions['positions']:
        symbol = pos['symbol']
        unrealized_plpc = pos['unrealized_plpc']  # 수익률 (0.1 = 10%)
        qty = pos['qty']
        
        # 10% 손실 -> 전량 매도
        if unrealized_plpc <= -0.10:
            place_market_order(symbol, int(qty), 'sell')
            print(f"🛑 STOP LOSS: {symbol} sold at -10%")
        
        # 20% 이익 -> 절반 매도
        elif unrealized_plpc >= 0.20:
            sell_qty = int(float(qty) / 2)
            if sell_qty > 0:
                place_market_order(symbol, sell_qty, 'sell')
                print(f"💰 TAKE PROFIT: {symbol} sold {sell_qty} shares at +20%")


# 거래 횟수 제한
daily_trade_count = {}

def can_trade_today(ticker):
    """하루 최대 3번 제한"""
    from datetime import date
    today = str(date.today())
    
    if today not in daily_trade_count:
        daily_trade_count.clear()
        daily_trade_count[today] = {}
    
    count = daily_trade_count[today].get(ticker, 0)
    return count < 3

def record_trade(ticker):
    """거래 기록"""
    from datetime import date
    today = str(date.today())
    daily_trade_count[today][ticker] = daily_trade_count[today].get(ticker, 0) + 1