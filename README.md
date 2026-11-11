# 🤖 Мульти-базовый AI-агент для анализа данных (MCP)

Pet-проект: AI-агент, который принимает задачу на естественном языке (например, «Покажи топ-5 товаров по выручке»), генерирует SQL-запрос и выполняет его в PostgreSQL через **MCP (Model Context Protocol)**. 

**Главная особенность:** агент умеет работать с **двумя разными базами данных** одновременно:
1. `dwh_marketplace` — аналитика продаж (таблица `fct_sales`).
2. `course` — анализ вакансий и откликов (таблицы `vacancies`, `applications`).

Проект демонстрирует интеграцию локальной LLM с пайплайнами данных без API-ключей.

## 📸 Скриншоты

**1. Чат-бот для аналитики продаж (вопрос → SQL → данные):**

![Chat Agent](assets/chat_agent.png)

**2. Проверка пропусков (локальная модель Qwen):**

![Local Agent](assets/local_agent_workflow.png)

**3. Агент для анализа вакансий (база course):**

![Jobs Agent](assets/jobs_agent.png)

## 🎯 Зачем это

В 2026 году агентные архитектуры (AI-агенты) становятся стандартом для автоматизации рутинных задач. Этот проект показывает, как с помощью **MCP** подключить LLM к базе данных, чтобы она могла самостоятельно выполнять аналитические запросы без участия человека. 

Проект работает в двух режимах:
- **Облачный** (заглушка/API) — для демонстрации логики.
- **Локальный** (Ollama + Qwen) — полностью автономный, без интернета и ключей.

Проект поддерживает **две базы данных**:
- `dwh_marketplace` (аналитика продаж) — агент `agent_chat.py`.
- `course` (вакансии и отклики) — агент `agent_chat_jobs.py`.

## 🏗 Архитектура

```mermaid
graph LR
    User["Пользователь<br/>(вопрос на русском)"] -->|"Покажи топ-5 товаров"| Agent["Агент<br/>(LLM + MCP Client)"]
    Agent -->|"SQL-запрос"| MCP["MCP Server<br/>(PostgreSQL)"]
    MCP -->|"Результат"| Agent
    Agent -->|"Данные"| User
    
    classDef user fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef agent fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef mcp fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px;
    
    class User user;
    class Agent agent;
    class MCP mcp;
```

## 📂 Структура

```
data-quality-agent/
├── run_server.py           # MCP-сервер для dwh_marketplace
├── run_server_course.py    # MCP-сервер для course
├── client.py               # Проверка подключения к dwh_marketplace
├── client_course.py        # Проверка подключения к course
├── agent_mock.py           # Агент с заглушкой LLM (работает без API)
├── agent_local.py          # Агент с локальной моделью Qwen (Ollama)
├── agent_chat.py           # Чат-бот для dwh_marketplace
├── agent_chat_jobs.py      # Чат-бот для course (вакансии)
├── assets/                 # Скриншоты
├── README.md
└── requirements.txt
```

## 🚀 Запуск

### 1. Установи зависимости
```bash
pip install -r requirements.txt
```

### 2. Настрой подключение к БД
Создайте файлы `.env` (для dwh_marketplace) и `.env.course` (для course) на основе `.env.example` и укажите свои реальные данные.

### 3. Запуск с локальной моделью (рекомендуется)
Этот режим не требует API-ключей и работает полностью автономно:
```bash
# Установите Ollama (https://ollama.com/)
# Скачайте модель
ollama pull qwen2.5-coder:7b

# Запустите чат-бота для продаж
python agent_chat.py

# Или чат-бота для вакансий
python agent_chat_jobs.py
```

**Пример работы чат-бота (продажи):**
```
Вы: Покажи топ-5 товаров по выручке
⏳ Думаю (генерация SQL)...
📝 SQL: SELECT stock_code, SUM(total_revenue) AS total_revenue
FROM dbt_schema.fct_sales
GROUP BY stock_code
ORDER BY total_revenue DESC
LIMIT 5;

📊 Результат:
{"columns": ["stock_code", "total_revenue"], "rows": [["23843", 168469.6], ["22423", 142592.95], ...], "row_count": 5, "execution_time_ms": 2082.23}
```

**Пример работы чат-бота (вакансии):**
```
Вы: Покажи топ-5 компаний по количеству вакансий
⏳ Думаю (генерация SQL)...
📝 SQL: SELECT v.employer_name, COUNT(a.id) AS application_count
FROM pavel_onichtchenko.vacancies v
JOIN pavel_onichtchenko.applications a ON v.id = a.vacancy_id
GROUP BY v.employer_name
ORDER BY application_count DESC
LIMIT 5;

📊 Результат:
{"columns": ["employer_name", "application_count"], "rows": [["Aston", 46], ["Top Selection", 37], ...], "row_count": 5, "execution_time_ms": 136.77}
```

### 4. Запуск с заглушкой (без LLM)
Если нет ни API, ни Ollama:
```bash
python agent_mock.py
```

## 💬 Примеры вопросов к агенту

**Для аналитики продаж (`agent_chat.py`):**
- «Покажи топ-5 товаров по выручке»
- «Сколько всего уникальных клиентов?»
- «Какая средняя выручка за день?»

**Для базы вакансий (`agent_chat_jobs.py`):**
- «Сколько всего вакансий?»
- «Сколько вакансий в статусе sent?»
- «Покажи топ-5 компаний по количеству вакансий»

## 🔮 Что дальше

Проект можно расширить:
- Добавить **Telegram-бота** (чтобы задавать вопросы с телефона).
- Подключить **третий MCP-сервер** (например, для работы с API HeadHunter).
- Настроить **автоматическую проверку качества** (алерты в Telegram при нахождении аномалий).

## 🔗 Связанные проекты

- [`data-governance-platform`](https://github.com/nconichtchenko-arch/data-governance-platform) — Data Governance (Каталог, Контракты, Lineage).
- [`soda-data-quality-demo`](https://github.com/nconichtchenko-arch/soda-data-quality-demo) — Data Quality проверки.
- [`api-data-contracts`](https://github.com/nconichtchenko-arch/api-data-contracts) — Data Contracts для API.

## 📫 Контакты

- **GitHub:** [github.com/nconichtchenko-arch](https://github.com/nconichtchenko-arch)
- **Email:** pavloni@mail.ru
- **Формат работы:** удалённо
