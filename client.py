import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # Параметры запуска сервера (тот самый, что мы только что проверили)
    server_params = StdioServerParameters(
        command="python",
        args=["run_server.py"],  # запускаем наш сервер через обертку
    )

    # Подключаемся к серверу по stdio
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. Инициализация
            await session.initialize()
            print("✅ Connected to MCP Server")

            # 2. Смотрим, какие инструменты доступны
            tools = await session.list_tools()
            print("\n🛠 Доступные инструменты:")
            for tool in tools.tools:
                print(f" - {tool.name}: {tool.description}")

            # 3. Выполняем SQL-запрос (проверка качества данных)
            print("\n🔍 Выполняем запрос: проверка пропусков в total_revenue")
            query = """
                SELECT 
                    COUNT(*) AS total_rows,
                    COUNT(*) FILTER (WHERE total_revenue IS NULL) AS null_rows
                FROM dbt_schema.fct_sales;
            """
            
            # Вызываем инструмент execute_query (он есть в mcp-postgres-server)
            result = await session.call_tool("query", {"sql": query})
            
            print("\n📊 Результат:")
            for content in result.content:
                if hasattr(content, "text"):
                    print(content.text)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())