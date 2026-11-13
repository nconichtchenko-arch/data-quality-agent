import streamlit as st
import asyncio
import sys
import re
import json
import os
import pandas as pd
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# ==========================================
# 1. НАСТРОЙКА
# ==========================================
st.set_page_config(page_title="AI-Агент по вакансиям", page_icon="💼", layout="wide")
st.title("💼 AI-Агент по вакансиям")
st.markdown("Задайте вопрос на русском языке. Агент сгенерирует SQL и выполнит его в базе `course`.")

# Инициализация LLM
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

# Загружаем .env.course
load_dotenv(".env.course")

# ==========================================
# 2. ФУНКЦИИ
# ==========================================
def ask_llm_to_generate_sql(task: str) -> str:
    """Генерирует SQL для базы вакансий."""
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

### SQL
"""
    response = client.chat.completions.create(
        model="qwen2.5-coder:7b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    
    raw_text = response.choices[0].message.content.strip()
    
    match = re.search(r"(SELECT|WITH)\s+", raw_text, re.IGNORECASE)
    if match:
        sql = raw_text[match.start():]
    else:
        sql = raw_text
    
    sql = sql.replace("```", "").strip()
    sql = sql.replace("<|im_end|>", "").strip()
    
    if ";" in sql:
        sql = sql.split(";")[0] + ";"
    else:
        sql = sql.split("\n\n")[0].strip()
    
    if not re.search(r"(SELECT|WITH)\s+", sql, re.IGNORECASE):
        return "CHAT_ONLY: " + sql
        
    return sql

async def run_agent_query(user_input: str):
    """Асинхронно подключается к MCP, выполняет запрос и возвращает (sql, data)."""
    server_params = StdioServerParameters(
        command="python",
        args=["run_server_course.py"],
        env={
            "DATABASE_URL": os.getenv("DATABASE_URL"),
            "PATH": os.environ.get("PATH", "")
        }
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                sql_query = ask_llm_to_generate_sql(user_input)
                
                if sql_query.startswith("CHAT_ONLY: "):
                    return None, f"🤖 Агент: {sql_query[11:]}"
                
                result = await session.call_tool("query", {"sql": sql_query})
                
                for content in result.content:
                    if hasattr(content, "text"):
                        try:
                            data = json.loads(content.text)
                            if "columns" in data and "rows" in data:
                                if not data["rows"]:
                                    return sql_query, "*Нет данных для отображения.*"
                                return sql_query, (data["columns"], data["rows"])
                            else:
                                return sql_query, f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"
                        except:
                            return sql_query, content.text
                return sql_query, "❌ Нет ответа от сервера."
    except Exception as e:
        return None, f"❌ Ошибка: {e}"

# ==========================================
# 3. ИНТЕРФЕЙС
# ==========================================
# Инициализация истории чата
if "messages" not in st.session_state:
    st.session_state.messages = []

# Отображаем историю
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Поле ввода
if prompt := st.chat_input("Спросите что-нибудь про вакансии..."):
    # Добавляем сообщение пользователя
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Получаем ответ
    with st.chat_message("assistant"):
        with st.spinner("Думаю..."):
            sql, result = asyncio.run(run_agent_query(prompt))
            
            if sql:
                st.code(sql, language="sql")
            
            if isinstance(result, tuple):
                cols, rows = result
                df = pd.DataFrame(rows, columns=cols)
                st.dataframe(df, use_container_width=True)
                response_text = f"Показано строк: {len(rows)}"
            else:
                st.markdown(result)
                response_text = result
    
    # Сохраняем ответ (только текст, чтобы не дублировать SQL)
    st.session_state.messages.append({"role": "assistant", "content": response_text})