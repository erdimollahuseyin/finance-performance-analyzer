import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Retrieve environment variables with a default value if not found
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
LLM_NAME = os.getenv("LLM_NAME", "gpt-4o-mini")

# Ensure that the required environment variables are set
if not OPENAI_API_KEY or not TAVILY_API_KEY:
    raise ValueError("Required API keys are not set in the environment variables.")
