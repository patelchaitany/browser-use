from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Browser, BrowserConfig
import asyncio
from dotenv import load_dotenv

load_dotenv()
# Optional: Use your own Chrome instance by uncommenting:
# browser = Browser(
#     config=BrowserConfig(
#         chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 
#     )
# )
async def main():
    agent = Agent(
        task="Go to amazon.com and search for iphone 15",
        llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash"),
        # browser=browser  # Uncomment to use your own Chrome browser
    )
    result = await agent.run()
    print(result)
asyncio.run(main())