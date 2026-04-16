import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен вашего бота
API_TOKEN = '8145748002:AAEvWPa5s2ivih0X3i9l46T4ZG1A2HNrado'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Инициализация планировщика
scheduler = AsyncIOScheduler()

# Определение состояний для машины состояний
class TaskStates(StatesGroup):
    waiting_for_task_text = State()
    waiting_for_deadline = State()

# Создание базы данных и таблицы
def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    # Создание таблицы задач
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            user_id INTEGER,
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            deadline TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    ''')

    conn.commit()
    conn.close()

# Функция для получения задач пользователя
def get_user_tasks(user_id):
    """Получение всех задач пользователя"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    cursor.execute('SELECT task_id, text, deadline, status FROM tasks WHERE user_id = ?', (user_id,))
    tasks = cursor.fetchall()

    conn.close()
    return tasks

# Функция для добавления новой задачи
def add_task(user_id, text, deadline):
    """Добавление новой задачи"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    cursor.execute('INSERT INTO tasks (user_id, text, deadline) VALUES (?, ?, ?)',
                   (user_id, text, deadline))

    conn.commit()
    conn.close()

# Функция для обновления статуса задачи
def update_task_status(task_id, status):
    """Обновление статуса задачи"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    cursor.execute('UPDATE tasks SET status = ? WHERE task_id = ?', (status, task_id))

    conn.commit()
    conn.close()

# Функция для удаления задачи
def delete_task(task_id):
    """Удаление задачи"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM tasks WHERE task_id = ?', (task_id,))

    conn.commit()
    conn.close()

# Функция для получения всех задач с ближайшими дедлайнами
def get_near_deadline_tasks():
    """Получение задач с дедлайнами в ближайший час"""
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()

    # Получаем текущее время и время через 1 час
    now = datetime.now()
    one_hour_later = now + timedelta(hours=1)

    # Преобразуем в строки для сравнения
    now_str = now.strftime('%Y-%m-%d %H:%M')
    one_hour_later_str = one_hour_later.strftime('%Y-%m-%d %H:%M')

    cursor.execute('''SELECT user_id, task_id, text, deadline FROM tasks
                      WHERE deadline BETWEEN ? AND ? AND status = 'pending' ''',
                   (now_str, one_hour_later_str))

    tasks = cursor.fetchall()
    conn.close()
    return tasks

# Отправка уведомлений о ближайших дедлайнах
async def send_deadline_notifications():
    """Отправка уведомлений о ближайших дедлайнах"""
    try:
        tasks = get_near_deadline_tasks()
        for user_id, task_id, text, deadline in tasks:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"⏰ Напоминание о задаче!\n\n"
                         f"<b>Задача:</b> {text}\n"
                         f"<b>Дедлайн:</b> {deadline}\n\n"
                         f"Осталось меньше часа до дедлайна!",
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"Sent deadline notification to user {user_id} for task {task_id}")
            except Exception as e:
                logger.error(f"Failed to send notification to user {user_id}: {e}")
    except Exception as e:
        logger.error(f"Error in send_deadline_notifications: {e}")

# Создание главного меню
def get_main_menu():
    """Создание главного меню с кнопками"""
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text="➕ Добавить задачу")
    keyboard.button(text="📝 Мои задачи")
    keyboard.button(text="❌ Удалить задачу")
    keyboard.button(text="ℹ️ Помощь")
    keyboard.adjust(2)  # 2 кнопки в ряд
    return keyboard.as_markup(resize_keyboard=True)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_name = message.from_user.full_name
    welcome_text = (
        f"👋 Привет, {user_name}!\n\n"
        "Я TaskMasterBot - ваш персональный помощник по управлению задачами.\n"
        "С помощью меня вы можете легко создавать, отслеживать и выполнять задачи.\n\n"
        "Выберите действие из меню ниже:"
    )

    await message.answer(welcome_text, reply_markup=get_main_menu())

# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "📚 <b>Помощь по TaskMasterBot</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start - Запуск бота и главное меню\n"
        "/help - Помощь по командам\n"
        "/tasks - Просмотр всех ваших задач\n\n"
        "<b>Функции:</b>\n"
        "➕ <b>Добавить задачу</b> - Создать новую задачу с дедлайном\n"
        "📝 <b>Мои задачи</b> - Посмотреть список всех задач\n"
        "❌ <b>Удалить задачу</b> - Удалить выбранную задачу\n\n"
        "Бот автоматически напоминает о задачах за 1 час до дедлайна!"
    )

    await message.answer(help_text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())

# Обработчик команды /tasks
@dp.message(Command("tasks"))
async def cmd_tasks(message: Message):
    """Обработчик команды /tasks"""
    user_id = message.from_user.id
    tasks = get_user_tasks(user_id)

    if not tasks:
        await message.answer("📋 У вас пока нет задач. Добавьте первую задачу!", reply_markup=get_main_menu())
        return

    # Формируем список задач
    tasks_text = "📋 <b>Ваши задачи:</b>\n\n"
    for i, (task_id, text, deadline, status) in enumerate(tasks, 1):
        status_icon = "✅" if status == "completed" else "⏳"
        status_text = "Выполнена" if status == "completed" else "В процессе"

        # Создаем inline кнопки для каждой задачи
        kb = InlineKeyboardBuilder()
        if status == "pending":
            kb.button(text="✅ Отметить выполненной", callback_data=f"complete_{task_id}")
        kb.button(text="🗑 Удалить задачу", callback_data=f"delete_{task_id}")
        kb.adjust(1)

        tasks_text += (
            f"<b>{i}. {text}</b>\n"
            f"📅 Дедлайн: {deadline}\n"
            f"{status_icon} Статус: {status_text}\n"
            f"🆔 ID: {task_id}\n\n"
        )

        # Отправляем задачу с кнопками
        await message.answer(tasks_text, parse_mode=ParseMode.HTML, reply_markup=kb.as_markup())
        tasks_text = ""  # Очищаем для следующей задачи

    if tasks_text:  # Если остались задачи без кнопок
        await message.answer(tasks_text, parse_mode=ParseMode.HTML)

# Обработчик нажатия на кнопку "Добавить задачу"
@dp.message(F.text == "➕ Добавить задачу")
async def add_task_button(message: Message, state: FSMContext):
    """Обработчик кнопки добавления задачи"""
    await message.answer("✏️ Введите текст задачи:", reply_markup=None)
    await state.set_state(TaskStates.waiting_for_task_text)

# Обработчик текста задачи
@dp.message(TaskStates.waiting_for_task_text)
async def process_task_text(message: Message, state: FSMContext):
    """Обработчик текста задачи"""
    await state.update_data(task_text=message.text)
    await message.answer("📅 Введите дедлайн в формате ГГГГ-ММ-ДД ЧЧ:ММ (например, 2026-04-18 15:30):")
    await state.set_state(TaskStates.waiting_for_deadline)

# Обработчик дедлайна задачи
@dp.message(TaskStates.waiting_for_deadline)
async def process_deadline(message: Message, state: FSMContext):
    """Обработчик дедлайна задачи"""
    user_data = await state.get_data()
    task_text = user_data['task_text']
    deadline = message.text
    user_id = message.from_user.id

    # Проверяем формат даты
    try:
        deadline_dt = datetime.strptime(deadline, '%Y-%m-%d %H:%M')
        # Проверяем, что дедлайн не в прошлом
        if deadline_dt < datetime.now():
            await message.answer("❌ Дата дедлайна не может быть в прошлом. Пожалуйста, введите корректную дату:")
            return
    except ValueError:
        await message.answer("❌ Неверный формат даты. Пожалуйста, введите дедлайн в формате ГГГГ-ММ-ДД ЧЧ:ММ:")
        return

    # Добавляем задачу в базу данных
    add_task(user_id, task_text, deadline)

    await message.answer(
        f"✅ Задача успешно добавлена!\n\n"
        f"<b>Задача:</b> {task_text}\n"
        f"<b>Дедлайн:</b> {deadline}",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_menu()
    )

    await state.clear()

# Обработчик нажатия на кнопку "Мои задачи"
@dp.message(F.text == "📝 Мои задачи")
async def my_tasks_button(message: Message):
    """Обработчик кнопки просмотра задач"""
    await cmd_tasks(message)

# Обработчик нажатия на кнопку "Удалить задачу"
@dp.message(F.text == "❌ Удалить задачу")
async def delete_task_button(message: Message):
    """Обработчик кнопки удаления задачи"""
    user_id = message.from_user.id
    tasks = get_user_tasks(user_id)

    if not tasks:
        await message.answer("📋 У вас пока нет задач для удаления.", reply_markup=get_main_menu())
        return

    # Создаем inline клавиатуру с задачами для удаления
    kb = InlineKeyboardBuilder()
    for task_id, text, deadline, status in tasks:
        kb.button(text=f"{text} ({deadline})", callback_data=f"delete_task_{task_id}")
    kb.adjust(1)

    await message.answer("Выберите задачу для удаления:", reply_markup=kb.as_markup())

# Обработчик нажатия на кнопку "Помощь"
@dp.message(F.text == "ℹ️ Помощь")
async def help_button(message: Message):
    """Обработчик кнопки помощи"""
    await cmd_help(message)

# Обработчик inline кнопок
@dp.callback_query(F.data.startswith("complete_"))
async def complete_task_callback(callback: CallbackQuery):
    """Обработчик отметки задачи выполненной"""
    task_id = int(callback.data.split("_")[1])

    # Обновляем статус задачи
    update_task_status(task_id, "completed")

    await callback.answer("✅ Задача отмечена как выполненная!")

    # Редактируем сообщение, убирая кнопку "Отметить выполненной"
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

@dp.callback_query(F.data.startswith("delete_"))
async def delete_task_callback(callback: CallbackQuery):
    """Обработчик удаления задачи через inline кнопку"""
    task_id = int(callback.data.split("_")[1])

    # Удаляем задачу
    delete_task(task_id)

    await callback.answer("🗑 Задача удалена!")

    # Редактируем сообщение
    try:
        await callback.message.edit_text("🗑 Задача была удалена.")
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

@dp.callback_query(F.data.startswith("delete_task_"))
async def delete_task_from_list_callback(callback: CallbackQuery):
    """Обработчик удаления задачи из списка"""
    task_id = int(callback.data.split("_")[2])

    # Удаляем задачу
    delete_task(task_id)

    await callback.answer("🗑 Задача удалена!")

    # Редактируем сообщение
    try:
        await callback.message.edit_text("🗑 Задача была удалена.")
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

# Обработчик любых других сообщений
@dp.message()
async def any_message(message: Message):
    """Обработчик любых других сообщений"""
    await message.answer("Пожалуйста, используйте меню для взаимодействия с ботом:", reply_markup=get_main_menu())

# Функция запуска бота
async def main():
    """Главная функция запуска бота"""
    # Инициализация базы данных
    init_db()

    # Запуск планировщика
    scheduler.add_job(send_deadline_notifications, 'interval', minutes=1)  # Проверяем каждую минуту
    scheduler.start()

    # Запуск поллинга
    try:
        logger.info("Bot started")
        await dp.start_polling(bot)
    finally:
        # Завершение работы планировщика при остановке бота
        scheduler.shutdown()
        await bot.session.close()

if __name__ == '__main__':
    # Запуск бота
    asyncio.run(main())