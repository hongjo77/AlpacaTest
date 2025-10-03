import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import dotenv

dotenv.load_dotenv()

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from financial_advisor.agent import financial_advisor
from financial_advisor.sub_agents.trader_agent import trader_agent
from trading_tools import get_account_info


session_service = InMemorySessionService()


async def run_agent(agent, user_id, session_id, prompt):
    """에이전트 실행"""
    runner = Runner(
        agent=agent,
        app_name="financial_advisor",
        session_service=session_service
    )
    
    content = types.Content(role='user', parts=[types.Part(text=prompt)])
    
    final_response = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
                break
    
    return final_response


async def analyze_and_trade(ticker: str):
    from datetime import date
    today = str(date.today())

    # 오늘 이 종목 거래 횟수 확인
    if today not in daily_trades:
        daily_trades[today] = {}
    
    trade_count = daily_trades[today].get(ticker, 0)
    
    if trade_count >= 8:
        print(f"⏸️ {ticker}: 오늘 이미 최대 거래했음, 스킵")
        return

    """종목 분석 및 자동 매매"""
    print(f"\n{'='*60}")
    print(f"[{datetime.now()}] Analyzing {ticker}...")
    print(f"{'='*60}\n")
    
    try:
        # 분석 세션 - await 추가!
        analysis_session_id = f"analysis_{ticker}_{int(datetime.now().timestamp())}"
        await session_service.create_session(
            app_name="financial_advisor",
            user_id="auto_trader",
            session_id=analysis_session_id
        )
        
        # 분석
        analysis_prompt = f"""
        Analyze {ticker} stock and provide a clear BUY, SELL, or HOLD recommendation.
        
        User Profile:
        - Investment Goal: Long-term growth
        - Risk Tolerance: Moderate
        - Investment Timeline: 6-12 months
        """
        
        print("📊 Running analysis...")
        analysis = await run_agent(
            financial_advisor,
            "auto_trader",
            analysis_session_id,
            analysis_prompt
        )
        
        print(f"\n✅ Analysis complete\n")
        
        # 매매 세션 - await 추가!
        trade_session_id = f"trade_{ticker}_{int(datetime.now().timestamp())}"
        await session_service.create_session(
            app_name="financial_advisor",
            user_id="auto_trader",
            session_id=trade_session_id
        )
        
        # 매매
        trade_prompt = f"""
        Based on this analysis, execute appropriate trades:
        
        {analysis}
        
        Check current positions and execute buy/sell orders accordingly.
        """
        
        print("💰 Executing trades...")
        trade_result = await run_agent(
            trader_agent,
            "auto_trader",
            trade_session_id,
            trade_prompt
        )
        
        print(trade_result)

        if "BUY ORDER EXECUTED" in trade_result or "SELL ORDER EXECUTED" in trade_result:
            daily_trades[today][ticker] = trade_count + 1
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def scheduled_task():
    """스케줄 작업"""
    watchlist = [
        "NVDA",   # 엔비디아 - AI 칩 리더, 변동성 높음
        "MSFT",   # 마이크로소프트 - 안정적, AI 투자 활발
        "GOOGL",  # 구글 - 검색/AI, 안정적
        "TSLA",   # 테슬라 - 변동성 높음, 거래량 많음
        "META"    # 메타 - AI 투자, 성장주
    ]
    
    account = get_account_info()
    print(f"\n💰 Account: ${account['portfolio_value']}\n")
    
    for ticker in watchlist:
        await analyze_and_trade(ticker)
        await asyncio.sleep(5)


async def main():
    """메인"""
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(
        scheduled_task,
        'interval',
        minutes=60
    )
    
    scheduler.start()
    print("🤖 Auto-trading bot started!")
    print("📊 Analyzing every 10 minutes...")
    print("Press Ctrl+C to stop\n")
    
    await scheduled_task()
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())