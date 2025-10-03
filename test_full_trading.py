import asyncio
import dotenv

dotenv.load_dotenv()

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from financial_advisor.agent import financial_advisor
from financial_advisor.sub_agents.trader_agent import trader_agent
from trading_tools import get_account_info


async def run_agent(agent, session_service, user_id, session_id, prompt):
    """에이전트 실행 헬퍼"""
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
        elif event.content and event.content.parts and event.content.parts[0].text:
            print(event.content.parts[0].text, end='', flush=True)
    
    print()
    return final_response


async def test_full_flow():
    ticker = "AAPL"
    
    print(f"\n{'='*60}")
    print(f"🤖 Full Trading Test: {ticker}")
    print(f"{'='*60}\n")
    
    # 1. 계정 확인
    account = get_account_info()
    print(f"💰 Starting Cash: ${account['cash']}\n")
    
    # 2. 세션 서비스
    session_service = InMemorySessionService()
    
    # 3. 분석 세션 생성 - await 추가!
    analysis_session = await session_service.create_session(
        app_name="financial_advisor",
        user_id="test_user",
        session_id="analysis_session"
    )
    
    # 4. 종목 분석
    print("📊 Step 1: Analyzing stock...\n")
    analysis_prompt = f"""
    Analyze {ticker} stock and provide a clear BUY, SELL, or HOLD recommendation.
    
    User Profile:
    - Investment Goal: Long-term growth
    - Risk Tolerance: Moderate
    - Investment Timeline: 6-12 months
    """
    
    analysis = await run_agent(
        financial_advisor,
        session_service,
        "test_user",
        "analysis_session",
        analysis_prompt
    )
    
    # 5. 매매 세션 생성 - await 추가!
    trade_session = await session_service.create_session(
        app_name="financial_advisor",
        user_id="test_user",
        session_id="trade_session"
    )
    
    # 6. 매매 실행
    print("\n💼 Step 2: Executing trade...\n")
    trade_prompt = f"""
    Based on this analysis, execute appropriate trades:
    
    {analysis}
    
    Check current positions and execute buy/sell orders accordingly.
    Follow all risk management rules (max 5% per position).
    """
    
    trade_result = await run_agent(
        trader_agent,
        session_service,
        "test_user",
        "trade_session",
        trade_prompt
    )
    
    # 7. 최종 결과
    final_account = get_account_info()
    print(f"\n{'='*60}")
    print(f"📈 Final Status:")
    print(f"  Cash: ${final_account['cash']}")
    print(f"  Portfolio Value: ${final_account['portfolio_value']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(test_full_flow())