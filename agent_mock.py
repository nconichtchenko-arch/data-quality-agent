import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ==========================================
# ЗАГЛУШКА ДЛЯ LLM (имитация)
# ==========================================
def mock_llm(prompt: str) -> str:
    """
    Имитирует ответ LLM. Принимает задачу на русском,
    возвращает готовый SQL-запрос.
    """
    prompt_lower = prompt.lower()
    
    if "пропуск" in prompt_lower or "null" in prompt_lower:
        return "SELECT COUNT(*) AS total_rows, COUNT(*) FILTER (WHERE total_revenue IS NULL) AS null_rows FROM dbt_schema.fct_sales;"
    
    elif "дубл" in prompt_lower or "уникальн" in prompt_lower:
        return "SELECT COUNT(*) AS total_rows, COUNT(DISTINCT invoice_no || '-' || stock_code || '-' || order_date || '-' || customer_id) AS unique_rows FROM dbt_schema.fct_sales;"
    
    elif "средн" in prompt_lower or "avg" in prompt_lower:
        return "SELECT AVG(total_revenue) AS avg_revenue FROM dbt_schema.fct_sales;"
    
    else:
        return "SELECT 'Задача не распознана. Попробуйте: проверь пропуски, дубли или среднюю выручку.' AS message;"

# ==========================================
# ОСНОВНАЯ ЛОГИКА АГЕНТА
# ==========================================
async def main():
    # 1. Задача на естественном языке
    task = "Проверь пропуски в total_revenue"
    print(f"📝 Задача: {task}")
    
    # 2. LLM генерирует SQL-запрос
    sql_query = mock_llm(task)
    print(f"🤖 LLM сгенерировала SQL:\n{sql_query}\n")
    
    # 3. Подключаемся к MCP-серверу и выполняем запрос
    server_params = StdioServerParameters(
        command="python",
        args=["run_server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Connected to MCP Server")
            
            # Вызываем инструмент query (правильное имя)
            result = await session.call_tool("query", {"sql": sql_query})
            
            print("📊 Результат от агента:")
            for content in result.content:
                if hasattr(content, "text"):
                    print(content.text)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())