import os
from dotenv import load_dotenv

load_dotenv()

class AgentSettings:
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")
    FASTAPI_URL: str = os.getenv("FASTAPI_URL", "http://localhost:8000/api")
    AGENT_INTERVAL: int = int(os.getenv("AGENT_INTERVAL", 3600))  # Run every hour (in seconds)

agentSettings = AgentSettings()