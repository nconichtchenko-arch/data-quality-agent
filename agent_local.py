import asyncio
import sys
import re
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ==========================================
# 1. НАСТРОЙКА ЛОКАЛЬНОЙ LLM (Ollama)
# ==========================================
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

def ask_llm_to_generate_sql(task: str) -> str:
    """
    Отправляет задачу в локальную модель Qwen и возвращает чистый SQL.
    """
    prompt = f"Write a SQL query for PostgreSQL to: {task}. Table: dbt_schema.fct_sales. Columns: invoice_no, stock_code, order_date, customer_id, total_quantity, total_revenue. Only return the SQL."
    
    response = client.chat.completions.create(
        model="qwen2.5-coder:7b",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
    )
    
    raw_text = response.choices[0].message.content.strip()
    
    # 1. Ищем начало SQL (SELECT или WITH)
    match = re.search(r"(SELECT|WITH)\s+", raw_text, re.IGNORECASE)
    if match:
        sql = raw_text[match.start():]
    else:
        sql = raw_text
    
    # 2. Убираем markdown-кавычки и артефакты
    sql = sql.replace("```", "").strip()
    sql = sql.replace("<|im_end|>", "").strip()
    
    return sql

# ==========================================
# 2. ОСНОВНАЯ ЛОГИКА АГЕНТА
# ==========================================
async def main():
    task = "Проверь пропуски в total_revenue"
    print(f"📝 Задача: {task}")
    
    print("⏳ Локальная модель думает (это может занять 20-30 секунд)...")
    sql_query = ask_llm_to_generate_sql(task)
    print(f"🤖 LLM сгенерировала SQL:\n{sql_query}\n")
    
    server_params = StdioServerParameters(
        command="python",
        args=["run_server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Connected to MCP Server")
            
            result = await session.call_tool("query", {"sql": sql_query})
            
            print("📊 Результат от агента:")
            for content in result.content:
                if hasattr(content, "text"):
                    print(content.text)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())