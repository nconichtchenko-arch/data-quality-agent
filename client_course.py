import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # Подключаемся к серверу БАЗЫ COURSE
    server_params = StdioServerParameters(
        command="python",
        args=["run_server_course.py"],  # <-- ВАЖНО: другой сервер
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Connected to MCP Server (course)")

            # 1. Смотрим схемы
            print("\n📂 Доступные схемы:")
            schemas = await session.call_tool("list_schemas", {})
            for content in schemas.content:
                if hasattr(content, "text"):
                    print(content.text)

            # 2. Смотрим таблицы в pavel_onichtchenko
            print("\n📋 Таблицы в схеме pavel_onichtchenko:")
            tables = await session.call_tool("list_tables", {"schema": "pavel_onichtchenko"})
            for content in tables.content:
                if hasattr(content, "text"):
                    print(content.text)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())