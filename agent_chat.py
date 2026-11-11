import asyncio
import sys
import re
import json
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
    """Генерирует SQL для базы продаж."""
    prompt = f"""### Task
Generate a SQL query to answer this question: `{task}`
### Database Schema
CREATE TABLE dbt_schema.fct_sales (
  invoice_no VARCHAR,
  stock_code VARCHAR,
  order_date DATE,
  customer_id INTEGER,
  total_quantity BIGINT,
  total_revenue NUMERIC
);
### SQL
"""
    response = client.chat.completions.create(
        model="qwen2.5-coder:7b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    
    raw_text = response.choices[0].message.content.strip()
    
    # Очистка от мусора
    match = re.search(r"(SELECT|WITH)\s+", raw_text, re.IGNORECASE)
    if match:
        sql = raw_text[match.start():]
    else:
        sql = raw_text
    
    sql = sql.replace("```", "").strip()
    sql = sql.replace("<|im_end|>", "").strip()
    
    # Отрезаем всё после первой точки с запятой (чтобы убрать пояснения)
    if ";" in sql:
        sql = sql.split(";")[0] + ";"
    else:
        sql = sql.split("\n\n")[0].strip()
        
    return sql

# ==========================================
# 2. ОСНОВНАЯ ЛОГИКА (ЦИКЛ ЧАТА)
# ==========================================
async def main():
    print("🤖 AI-Агент по продажам готов к работе!")
    print("Введите вопрос (например: 'Покажи топ-5 товаров по выручке') или 'выход'.\n")
    
    server_params = StdioServerParameters(
        command="python",
        args=["run_server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Подключено к базе продаж\n")
            
            while True:
                user_input = input("Вы: ").strip()
                if user_input.lower() in ["выход", "exit", "quit", "q"]:
                    print("До свидания!")
                    break
                if not user_input:
                    continue
                
                print("⏳ Думаю (генерация SQL)...")
                try:
                    sql_query = ask_llm_to_generate_sql(user_input)
                    print(f"📝 SQL: {sql_query}")
                    
                    print("⏳ Выполняю запрос...")
                    result = await session.call_tool("query", {"sql": sql_query})
                    
                    print("📊 Результат:")
                    for content in result.content:
                        if hasattr(content, "text"):
                            try:
                                data = json.loads(content.text)
                                # Вывод в виде таблицы
                                if "columns" in data and "rows" in data:
                                    cols = data["columns"]
                                    rows = data["rows"]
                                    
                                    # Определяем ширину колонок
                                    widths = [len(str(c)) for c in cols]
                                    for row in rows:
                                        for i, val in enumerate(row):
                                            widths[i] = max(widths[i], len(str(val)))
                                    
                                    # Печатаем шапку
                                    header = " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(cols))
                                    print("-" * len(header))
                                    print(header)
                                    print("-" * len(header))
                                    
                                    # Печатаем строки
                                    for row in rows:
                                        print(" | ".join(str(val).ljust(widths[i]) for i, val in enumerate(row)))
                                    print("-" * len(header))
                                    print(f"Всего строк: {data.get('row_count', len(rows))}, Время: {data.get('execution_time_ms', 0):.2f} мс")
                                else:
                                    print(json.dumps(data, ensure_ascii=False, indent=2))
                            except:
                                print(content.text)
                    print("-" * 50 + "\n")
                    
                except Exception as e:
                    print(f"❌ Ошибка: {e}\n")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())