import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from tavily import TavilyClient

# Load environment variables
def load_env_variables():
    load_dotenv()

# Initialize clients
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
LLM_NAME = "gpt-4o-mini"

model = ChatOpenAI(api_key=OPENAI_API_KEY, model=LLM_NAME)
tavily = TavilyClient(api_key=TAVILY_API_KEY)
