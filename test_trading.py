import asyncio
import os
import dotenv

dotenv.load_dotenv()

from trading_tools import get_account_info, get_positions


async def test_alpaca():
    """Alpaca 연결 테스트"""
    
    print("\n🔌 Testing Alpaca connection...\n")
    
    try:
        # 계정 정보 확인
        account = get_account_info()
        print("✅ Account Info:")
        print(f"  Cash: ${account['cash']}")
        print(f"  Buying Power: ${account['buying_power']}")
        print(f"  Portfolio Value: ${account['portfolio_value']}\n")
        
        # 현재 보유 종목 확인
        positions = get_positions()
        print(f"📊 Current Positions: {len(positions['positions'])}")
        for pos in positions['positions']:
            print(f"  {pos['symbol']}: {pos['qty']} shares @ ${pos['current_price']}")
        
        if not positions['positions']:
            print("  (No positions yet)")
        
        print("\n✅ Alpaca connection successful!\n")
        
    except Exception as e:
        print(f"❌ Error connecting to Alpaca: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_alpaca())