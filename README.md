# Finance Management API

API для управления личными финансами с отслеживанием доходов, расходов и бюджетов.

## Функциональность

- Регистрация и авторизация пользователей
- Учет доходов и расходов с категориями
- Создание и отслеживание бюджетов
- Создание финансовых целей
- Генерация отчетов
- Планирование регулярных платежей
- Поиск и фильтрация транзакций

## Технический стек

- Python 3.10+
- FastAPI 0.95+
- MongoDB (через Motor для асинхронной работы)
- Pydantic 2.0+
- JWT для аутентификации

## Установка и запуск

1. Клонировать репозиторий
2. Создать виртуальное окружение:
   ```
   python -m venv venv
   source venv/bin/activate  # для Linux/macOS
   venv\Scripts\activate     # для Windows
   ```
3. Установить зависимости:
   ```
   pip install -r requirements.txt
   ```
4. Создать файл `.env` на основе `.env.example`
5. Запустить MongoDB
6. Запустить приложение:
   ```
   python main.py
   ```

После запуска API будет доступно по адресу http://localhost:8000

## API Endpoints

### Аутентификация

- `POST /api/auth/register` - Регистрация нового пользователя
- `POST /api/auth/login` - Авторизация и получение JWT токена
- `POST /api/auth/refresh-token` - Обновление JWT токена

### Пользователи

- `GET /api/users/me` - Получение информации о текущем пользователе
- `PUT /api/users/me` - Обновление информации о текущем пользователе
- `GET /api/users/me/statistics` - Получение статистики пользователя

### Транзакции

- `POST /api/transactions` - Создание новой транзакции
- `GET /api/transactions` - Получение списка транзакций с фильтрацией
- `GET /api/transactions/{transaction_id}` - Получение транзакции по ID
- `PUT /api/transactions/{transaction_id}` - Обновление транзакции
- `DELETE /api/transactions/{transaction_id}` - Удаление транзакции

### Категории

- `POST /api/categories` - Создание новой категории
- `GET /api/categories` - Получение списка категорий
- `GET /api/categories/{category_id}` - Получение категории по ID
- `PUT /api/categories/{category_id}` - Обновление категории
- `DELETE /api/categories/{category_id}` - Удаление категории

### Бюджеты

- `POST /api/budgets` - Создание нового бюджета
- `GET /api/budgets` - Получение списка бюджетов
- `GET /api/budgets/{budget_id}` - Получение бюджета по ID
- `PUT /api/budgets/{budget_id}` - Обновление бюджета
- `DELETE /api/budgets/{budget_id}` - Удаление бюджета
- `GET /api/budgets/{budget_id}/progress` - Получение прогресса по бюджету

### Финансовые цели

- `POST /api/goals` - Создание новой финансовой цели
- `GET /api/goals` - Получение списка финансовых целей
- `GET /api/goals/{goal_id}` - Получение финансовой цели по ID
- `PUT /api/goals/{goal_id}` - Обновление финансовой цели
- `DELETE /api/goals/{goal_id}` - Удаление финансовой цели
- `GET /api/goals/{goal_id}/progress` - Получение прогресса по финансовой цели
- `POST /api/goals/{goal_id}/contributions` - Добавление взноса к финансовой цели

### Отчеты

- `GET /api/reports/monthly` - Получение ежемесячного отчета
- `GET /api/reports/category` - Получение отчета по категориям
- `GET /api/reports/income-expense` - Получение отчета по доходам и расходам

## Примеры запросов

### Создание транзакции

```
POST /api/transactions
{
  "type": "expense",
  "amount": 1500.50,
  "currency": "RUB",
  "category_id": "category_id_here",
  "description": "Покупка продуктов",
  "date": "2023-11-15T14:30:00",
  "tags": ["продукты", "еда"]
}
```

### Создание бюджета

```
POST /api/budgets
{
  "name": "Бюджет на продукты",
  "amount": 15000,
  "currency": "RUB",
  "period": "monthly",
  "category_id": "category_id_here",
  "start_date": "2023-11-01",
  "end_date": "2023-11-30"
}
```

### Создание финансовой цели

```
POST /api/goals
{
  "name": "Покупка ноутбука",
  "target_amount": 80000,
  "currency": "RUB",
  "current_amount": 15000,
  "deadline": "2024-03-01",
  "description": "Накопить на новый ноутбук"
}
```

### Получение ежемесячного отчета

```
GET /api/reports/monthly?year=2023&month=11
```
