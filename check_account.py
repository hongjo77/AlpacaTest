import dotenv
dotenv.load_dotenv()

from trading_tools import get_account_info, get_positions

print("\n" + "="*60)
print("📊 Current Alpaca Account Status")
print("="*60 + "\n")

# 계정 정보
account = get_account_info()
print("💰 Account Info:")
print(f"  Cash: ${account['cash']:,.2f}")
print(f"  Portfolio Value: ${account['portfolio_value']:,.2f}")
print(f"  Buying Power: ${account['buying_power']:,.2f}")
print(f"  Equity: ${account['equity']:,.2f}\n")

# 포지션
positions = get_positions()
print(f"📈 Current Positions: {len(positions['positions'])}\n")

if positions['positions']:
    for pos in positions['positions']:
        print(f"  {pos['symbol']}:")
        print(f"    Quantity: {pos['qty']} shares")
        print(f"    Avg Price: ${pos['avg_entry_price']:.2f}")
        print(f"    Current Price: ${pos['current_price']:.2f}")
        print(f"    Market Value: ${pos['market_value']:,.2f}")
        print(f"    P/L: ${pos['unrealized_pl']:,.2f} ({pos['unrealized_plpc']*100:.2f}%)")
        print()
else:
    print("  (No positions)\n")

print("="*60 + "\n")