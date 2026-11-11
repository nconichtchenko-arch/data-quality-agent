import asyncio
import sys
import re
import json
import os
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
    """Генерирует SQL для базы вакансий."""
    # Строгий промпт с обязательным указанием схемы
    prompt = f"""### Task
Generate a SQL query to answer this question: `{task}`

### Database Schema (PostgreSQL)
Tables in schema `pavel_onichtchenko`:
1. `pavel_onichtchenko.vacancies` (id, hh_id, name, employer_name, salary_from, salary_to, area_name, experience, schedule, description, url, published_at)
2. `pavel_onichtchenko.applications` (id, vacancy_id, status, notes, applied_at)

**CRITICAL RULES:**
- ALWAYS use the full table name with schema: `pavel_onichtchenko.vacancies` and `pavel_onichtchenko.applications`. NEVER use just `vacancies` or `applications`.
- If the user asks about "вакансии" (vacancies), count from `pavel_onichtchenko.vacancies`.
- If the user asks about "отклики" (applications/responses), count from `pavel_onichtchenko.applications`.
- Statuses in applications: 'sent', 'replied', 'screening', 'interview', 'rejected', 'ignored'. Do NOT use 'applied'.
- To find top companies by vacancies, use `GROUP BY employer_name` on `pavel_onichtchenko.vacancies`.

### SQL
"""
    response = client.chat.completions.create(
        model="qwen2.5-coder:7b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0, # Строго детерминированный ответ
    )
    
    raw_text = response.choices[0].message.content.strip()
    
    # Очистка от мусора
    match = re.search(r"(SELECT|WITH)\s+", raw_text, re.IGNORECASE)
    if match:
        sql = raw_text[match.start():]
    else:
        sql = raw_text
    
    # Убираем markdown
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
    print("🤖 AI-Агент по вакансиям готов к работе!")
    print("Введите вопрос (например: 'Покажи топ-5 компаний по количеству вакансий') или 'выход'.\n")
    
    # Загружаем .env.course, чтобы получить DATABASE_URL
    from dotenv import load_dotenv
    load_dotenv(".env.course")
    
    server_params = StdioServerParameters(
        command="python",
        args=["run_server_course.py"],
        env={
            "DATABASE_URL": os.getenv("DATABASE_URL"),
            "PATH": os.environ.get("PATH", "")
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Подключено к базе вакансий\n")
            
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