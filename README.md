# TaskMasterBot - Telegram Bot

Telegram-бот для управления задачами с дедлайнами и автоматическими напоминаниями.

## Основные функции

1. Добавление задач с дедлайнами
2. Хранение задач в SQLite базе данных
3. Автоматические напоминания за 1 час до дедлайна
4. Пометка задач как выполненных
5. Удаление задач

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone <repo-url>
cd telegram_bot
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Получение токена бота

1. Откройте Telegram
2. Найдите @BotFather
3. Отправьте команду `/newbot`
4. Следуйте инструкциям для создания бота
5. Скопируйте полученный токен

### 4. Настройка токена

Откройте файл `bot.py` и замените строку:

```python
API_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
```

на ваш реальный токен:

```python
API_TOKEN = '1234567890:ABCDEFghijklmnopqrstuvwxyz1234567890'
```

### 5. Запуск бота

```bash
python bot.py
```

## Использование

После запуска бота:

1. Найдите своего бота в Telegram
2. Отправьте команду `/start`
3. Используйте кнопки меню для управления задачами:
   - ➕ Добавить задачу
   - 📝 Мои задачи
   - ❌ Удалить задачу
   - ℹ️ Помощь

## Деплой на Render.com

1. Создайте аккаунт на [Render](https://render.com/)
2. Создайте новый Web Service
3. Подключите ваш репозиторий с ботом
4. Установите следующие настройки:
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
5. Добавьте переменную окружения:
   - Key: `TELEGRAM_BOT_TOKEN`
   - Value: ваш токен бота
6. Замените в коде `API_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'` на `API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')`
7. Разверните сервис

## Деплой на VPS

1. Загрузите файлы бота на ваш VPS
2. Установите Python 3.7+
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Установите токен в файле `bot.py`
5. Запустите бота:
   ```bash
   python bot.py
   ```
6. Для работы в фоновом режиме рекомендуется использовать systemd или screen:
   
   ### Вариант с screen:
   ```bash
   screen -S taskmasterbot
   python bot.py
   # Нажмите Ctrl+A, затем D для выхода из screen
   ```

## Структура проекта

```
telegram_bot/
├── bot.py              # Основной файл бота
├── requirements.txt    # Зависимости
├── tasks.db            # База данных SQLite (создается автоматически)
└── README.md           # Этот файл
```

## База данных

Бот использует SQLite базу данных для хранения задач. При первом запуске автоматически создается файл `tasks.db` со следующей структурой:

```sql
CREATE TABLE tasks (
    user_id INTEGER,
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    deadline TEXT NOT NULL,
    status TEXT DEFAULT 'pending'
);
```

## Лицензия

MIT License