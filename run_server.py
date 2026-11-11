import sys
import asyncio
import os
from mcp_postgres_server import server as mcp_server

if __name__ == "__main__":
    # 1. Принудительно переключаем event loop на Selector для Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # 2. Запускаем основной цикл сервера
    # (в пакете mcp-postgres-server функция main() запускает stdio-сервер)
    asyncio.run(mcp_server.main())