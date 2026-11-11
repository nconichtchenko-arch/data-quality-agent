import sys
import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные из .env.course
load_dotenv(".env.course")

from mcp_postgres_server import server as mcp_server

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(mcp_server.main())