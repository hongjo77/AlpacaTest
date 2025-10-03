import asyncio
import dotenv

dotenv.load_dotenv()

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from financial_advisor.agent import financial_advisor


async def test_analysis():
    ticker = "AAPL"
    
    print(f"\n{'='*60}")
    print(f"🔍 Analyzing {ticker}...")
    print(f"{'='*60}\n")
    
    # 1. 세션 서비스 생성
    session_service = InMemorySessionService()
    
    # 2. 세션 생성 - await 추가!
    session = await session_service.create_session(
        app_name="financial_advisor",
        user_id="test_user",
        session_id="test_session"
    )
    
    # 3. Runner 생성
    runner = Runner(
        agent=financial_advisor,
        app_name="financial_advisor",
        session_service=session_service
    )
    
    # 4. 쿼리
    prompt = f"""
    Analyze {ticker} stock and provide a clear BUY, SELL, or HOLD recommendation.
    
    User Profile:
    - Investment Goal: Long-term growth
    - Risk Tolerance: Moderate
    - Investment Timeline: 6-12 months
    """
    
    content = types.Content(role='user', parts=[types.Part(text=prompt)])
    
    try:
        print("📊 Analysis Result:\n")
        
        async for event in runner.run_async(
            user_id="test_user",
            session_id="test_session",
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    print(event.content.parts[0].text)
                    break
            elif event.content and event.content.parts and event.content.parts[0].text:
                print(event.content.parts[0].text, end='', flush=True)
        
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_analysis())