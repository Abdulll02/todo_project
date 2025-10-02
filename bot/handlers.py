import aiohttp
import os
import re
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
import json

router = Router()

API_URL = os.getenv('DJANGO_API_URL', 'http://backend:8000/api')

class AddTaskStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_due_date = State()
    waiting_for_categories = State()

class DeleteTaskStates(StatesGroup):
    waiting_for_task_number = State()

class CategoryStates(StatesGroup):
    waiting_for_category_name = State()
    waiting_for_category_to_delete = State()

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Мои задачи"), KeyboardButton(text="➕ Добавить задачу")],
            [KeyboardButton(text="🗑️ Удалить задачу"), KeyboardButton(text="🏷️ Категории")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )

def get_categories_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Список категорий"), KeyboardButton(text="➕ Добавить категорию")],
            [KeyboardButton(text="🗑️ Удалить категорию"), KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

async def make_api_request(endpoint, method='GET', data=None, headers=None):
    url = f"{API_URL}/{endpoint}"
    
    if headers is None:
        headers = {}
    
    headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=data, headers=headers) as response:
                content_type = response.headers.get('Content-Type', '')
                
                if 'application/json' not in content_type:
                    text = await response.text()
                    return {'error': True, 'status_code': response.status, 'message': 'Non-JSON response'}
                
                text = await response.text()
                if response.status >= 400:
                    return {'error': True, 'status_code': response.status, 'message': text}
                
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {'error': True, 'message': 'Invalid JSON response'}
                    
    except Exception as e:
        logging.exception("API request error: %s %s data=%s headers=%s", method, url, data, headers)
        return {'error': True, 'message': 'Connection failed'}

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в ToDo бот!\n\n"
        "Используйте кнопки ниже для управления задачами:",
        reply_markup=get_main_keyboard()
    )

@router.message(F.text == "🔙 Назад")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔙 Возвращаемся в главное меню:", reply_markup=get_main_keyboard())

@router.message(F.text == "📋 Мои задачи")
async def show_tasks(message: Message):
    try:
        result = await make_api_request('tasks/')
        
        if isinstance(result, dict) and result.get('error'):
            await message.answer("❌ Ошибка при получении задач.")
            return
        
        tasks = result.get('results', []) if isinstance(result, dict) else result
        
        if not tasks:
            await message.answer("📭 У вас пока нет задач.")
            return
            
        response = "📋 Ваши задачи:\n\n"
        for i, task in enumerate(tasks, 1):
            if isinstance(task, dict) and 'title' in task:
                status = "✅" if task.get('completed') else "⏳"
                if task.get('is_overdue') and not task.get('completed'):
                    status = "🚨"  # Просроченная задача
                    
                categories = ", ".join([cat['name'] for cat in task.get('categories', []) if isinstance(cat, dict)])
                created_date = task.get('created_date', 'Неизвестно')
                due_date = task.get('due_date')
                
                response += f"{i}. {status} {task['title']}\n"
                response += f"   📅 Создана: {created_date[:10]}\n"
                if due_date:
                    due_status = "🚨 ПРОСРОЧЕНА" if task.get('is_overdue') else "⏰ Дедлайн"
                    response += f"   {due_status}: {due_date[:10]}\n"
                if categories:
                    response += f"   🏷️ Категории: {categories}\n"
                if task.get('description'):
                    desc = task['description']
                    if len(desc) > 50:
                        desc = desc[:50] + "..."
                    response += f"   📄 Описание: {desc}\n"
                response += f"   🆔 ID: {task['id'][:8]}...\n\n"
            
        response += "💡 Для удаления задачи нажмите «🗑️ Удалить задачу»"
        await message.answer(response)
        
    except Exception as e:
        logging.exception("Error in show_tasks handler")
        await message.answer("❌ Ошибка при получении задач.")

        
@router.message(F.text == "➕ Добавить задачу")
async def add_task_start(message: Message, state: FSMContext):
    await state.set_state(AddTaskStates.waiting_for_title)
    await message.answer(
        "📝 Введите название задачи:",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(AddTaskStates.waiting_for_title)
async def process_task_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddTaskStates.waiting_for_description)
    await message.answer("📄 Введите описание задачи (или отправьте '-' для пропуска):")

@router.message(AddTaskStates.waiting_for_description)
async def process_task_description(message: Message, state: FSMContext):
    description = message.text if message.text != '-' else ''
    await state.update_data(description=description)
    await state.set_state(AddTaskStates.waiting_for_due_date)
    await message.answer(
        "📅 Введите дату дедлайна (в формате ДД.ММ.ГГГГ, например 25.12.2024)\n"
        "Или отправьте '-' чтобы пропустить:"
    )

@router.message(AddTaskStates.waiting_for_due_date)
async def process_task_due_date(message: Message, state: FSMContext):
    due_date_input = message.text.strip()
    
    if due_date_input != '-':
        # Парсим дату
        date_pattern = r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
        match = re.match(date_pattern, due_date_input)
        
        if match:
            day, month, year = match.groups()
            try:
                due_date = datetime(int(year), int(month), int(day))
                await state.update_data(due_date=due_date.isoformat())
            except ValueError:
                await message.answer("❌ Неверная дата! Пожалуйста, введите дату в формате ДД.ММ.ГГГГ:")
                return
        else:
            await message.answer("❌ Неверный формат! Пожалуйста, введите дату в формате ДД.ММ.ГГГГ:")
            return
    else:
        await state.update_data(due_date=None)
    
    await state.set_state(AddTaskStates.waiting_for_categories)
    
    # Получаем список существующих категорий
    categories_result = await make_api_request('categories/')
    existing_categories = []
    if not isinstance(categories_result, dict) or not categories_result.get('error'):
        categories = categories_result.get('results', []) if isinstance(categories_result, dict) else categories_result
        existing_categories = [cat['name'] for cat in categories if isinstance(cat, dict)]
    
    if existing_categories:
        categories_text = ", ".join(existing_categories)
        await message.answer(
            f"🏷️ Введите категории через запятую (доступные: {categories_text})\n"
            "Или отправьте '-' чтобы пропустить:"
        )
    else:
        await message.answer(
            "🏷️ Введите категории через запятую\n"
            "Или отправьте '-' чтобы пропустить:"
        )

@router.message(AddTaskStates.waiting_for_categories)
async def process_task_categories(message: Message, state: FSMContext):
    data = await state.get_data()
    categories_input = message.text.strip()
    
    task_data = {
        'title': data['title'],
        'description': data.get('description', ''),
        'completed': False,
        'due_date': data.get('due_date')
    }
    
    # Обрабатываем категории
    if categories_input != '-':
        category_names = [cat.strip() for cat in categories_input.split(',') if cat.strip()]
        
        # Проверяем существование категорий
        valid_categories = []
        invalid_categories = []
        
        for category_name in category_names:
            check_result = await make_api_request(f'categories/check_category?name={category_name}')
            if not isinstance(check_result, dict) or not check_result.get('error'):
                if check_result.get('exists'):
                    valid_categories.append(category_name)
                else:
                    invalid_categories.append(category_name)
        
        if invalid_categories:
            await message.answer(
                f"❌ Следующие категории не существуют: {', '.join(invalid_categories)}\n"
                f"✅ Существующие категории: {', '.join(valid_categories) if valid_categories else 'нет'}\n\n"
                "Пожалуйста, создайте категории сначала через меню «🏷️ Категории» или используйте существующие.",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            return
        
        task_data['category_names'] = valid_categories
    
    try:
        result = await make_api_request('tasks/', 'POST', task_data)
        
        if isinstance(result, dict) and result.get('error'):
            await message.answer("❌ Ошибка при добавлении задачи.", reply_markup=get_main_keyboard())
        else:
            success_msg = "✅ Задача успешно добавлена!"
            if categories_input != '-' and category_names:
                success_msg += f"\n🏷️ Категории: {', '.join(category_names)}"
            if data.get('due_date'):
                success_msg += f"\n📅 Дедлайн: {data['due_date'][:10]}"
            
            await message.answer(success_msg, reply_markup=get_main_keyboard())
            
    except Exception as e:
        logging.exception("Error in process_task_categories handler")
        await message.answer("❌ Ошибка при добавлении задачи.", reply_markup=get_main_keyboard())
    
    await state.clear()

@router.message(F.text == "🗑️ Удалить задачу")
async def delete_task_start(message: Message, state: FSMContext):
    # Сначала показываем список задач
    result = await make_api_request('tasks/')
    
    if isinstance(result, dict) and result.get('error'):
        await message.answer("❌ Ошибка при получении задач.")
        return
    
    tasks = result.get('results', []) if isinstance(result, dict) else result
    
    if not tasks:
        await message.answer("📭 У вас пока нет задач для удаления.")
        return
    
    # Сохраняем задачи в состоянии
    await state.update_data(tasks=tasks)
    await state.set_state(DeleteTaskStates.waiting_for_task_number)
    
    response = "🗑️ Выберите номер задачи для удаления:\n\n"
    for i, task in enumerate(tasks, 1):
        if isinstance(task, dict) and 'title' in task:
            response += f"{i}. {task['title']}\n"
    
    await message.answer(response)

@router.message(DeleteTaskStates.waiting_for_task_number)
async def process_task_deletion(message: Message, state: FSMContext):
    try:
        task_number = int(message.text.strip())
        data = await state.get_data()
        tasks = data.get('tasks', [])
        
        if 1 <= task_number <= len(tasks):
            task_to_delete = tasks[task_number - 1]
            task_id = task_to_delete['id']
            
            # Удаляем задачу
            result = await make_api_request(f'tasks/{task_id}/delete_task/', 'POST')
            
            if isinstance(result, dict) and result.get('error'):
                await message.answer("❌ Ошибка при удалении задачи.", reply_markup=get_main_keyboard())
            else:
                await message.answer(f"✅ Задача «{task_to_delete['title']}» успешно удалена!", reply_markup=get_main_keyboard())
        else:
            await message.answer("❌ Неверный номер задачи. Пожалуйста, выберите номер из списка:")
            return
            
    except ValueError:
        await message.answer("❌ Пожалуйста, введите номер задачи (число):")
        return
    
    await state.clear()

@router.message(F.text == "🏷️ Категории")
async def show_categories_menu(message: Message):
    await message.answer(
        "🏷️ Управление категориями:",
        reply_markup=get_categories_keyboard()
    )

@router.message(F.text == "📋 Список категорий")
async def show_categories(message: Message):
    try:
        result = await make_api_request('categories/')
        
        if isinstance(result, dict) and result.get('error'):
            await message.answer("❌ Ошибка при получении категорий.")
            return
        
        categories = result.get('results', []) if isinstance(result, dict) else result
            
        if not categories:
            await message.answer("📭 Категории пока не созданы.")
            return
            
        response = "🏷️ Доступные категории:\n\n"
        for i, category in enumerate(categories, 1):
            if isinstance(category, dict) and 'name' in category:
                response += f"{i}. {category['name']}\n"
            
        await message.answer(response)
        
    except Exception as e:
        logging.exception("Error in show_categories handler")
        await message.answer("❌ Ошибка при получении категорий.")

@router.message(F.text == "➕ Добавить категорию")
async def add_category_start(message: Message, state: FSMContext):
    await state.set_state(CategoryStates.waiting_for_category_name)
    await message.answer("🏷️ Введите название новой категории:")

@router.message(CategoryStates.waiting_for_category_name)
async def process_category_name(message: Message, state: FSMContext):
    category_name = message.text.strip()
    
    if not category_name:
        await message.answer("❌ Название категории не может быть пустым. Попробуйте еще раз:")
        return
    
    # Проверяем, существует ли уже категория
    check_result = await make_api_request(f'categories/check_category?name={category_name}')
    if not isinstance(check_result, dict) or not check_result.get('error'):
        if check_result.get('exists'):
            await message.answer(f"❌ Категория «{category_name}» уже существует!", reply_markup=get_categories_keyboard())
            await state.clear()
            return
    
    # Создаем категорию
    category_data = {'name': category_name}
    result = await make_api_request('categories/create_category/', 'POST', category_data)
    
    if isinstance(result, dict) and result.get('error'):
        await message.answer("❌ Ошибка при создании категории.", reply_markup=get_categories_keyboard())
    else:
        await message.answer(f"✅ Категория «{category_name}» успешно создана!", reply_markup=get_categories_keyboard())
    
    await state.clear()

@router.message(F.text == "🗑️ Удалить категорию")
async def delete_category_start(message: Message, state: FSMContext):
    # Сначала показываем список категорий
    result = await make_api_request('categories/')
    
    if isinstance(result, dict) and result.get('error'):
        await message.answer("❌ Ошибка при получении категорий.")
        return
    
    categories = result.get('results', []) if isinstance(result, dict) else result
    
    if not categories:
        await message.answer("📭 У вас пока нет категорий для удаления.")
        return
    
    # Сохраняем категории в состоянии
    await state.update_data(categories=categories)
    await state.set_state(CategoryStates.waiting_for_category_to_delete)
    
    response = "🗑️ Выберите номер категории для удаления:\n\n"
    for i, category in enumerate(categories, 1):
        if isinstance(category, dict) and 'name' in category:
            response += f"{i}. {category['name']}\n"
    
    await message.answer(response)

@router.message(CategoryStates.waiting_for_category_to_delete)
async def process_category_deletion(message: Message, state: FSMContext):
    try:
        category_number = int(message.text.strip())
        data = await state.get_data()
        categories = data.get('categories', [])
        
        if 1 <= category_number <= len(categories):
            category_to_delete = categories[category_number - 1]
            category_id = category_to_delete['id']
            
            # Удаляем категорию
            result = await make_api_request(f'categories/{category_id}/delete_category/', 'POST')
            
            if isinstance(result, dict) and result.get('error'):
                await message.answer("❌ Ошибка при удалении категории.", reply_markup=get_categories_keyboard())
            else:
                await message.answer(f"✅ Категория «{category_to_delete['name']}» успешно удалена!", reply_markup=get_categories_keyboard())
        else:
            await message.answer("❌ Неверный номер категории. Пожалуйста, выберите номер из списка:")
            return
            
    except ValueError:
        await message.answer("❌ Пожалуйста, введите номер категории (число):")
        return
    
    await state.clear()

@router.message(F.text == "ℹ️ Помощь")
async def show_help(message: Message):
    help_text = """
ℹ️ **Помощь по боту**

**Основные команды:**
📋 Мои задачи - Показать все ваши задачи
➕ Добавить задачу - Создать новую задачу
🗑️ Удалить задачу - Удалить существующую задачу
🏷️ Категории - Управление категориями

**Управление категориями:**
📋 Список категорий - Показать все категории
➕ Добавить категорию - Создать новую категорию  
🗑️ Удалить категорию - Удалить существующую категорию

**Особенности:**
• При создании задачи можно указать дедлайн (формат: ДД.ММ.ГГГГ)
• Можно добавлять задачи к существующим категориям
• Если категории не существует - задача не создается
• Задачи автоматически сортируются по дате создания

Для начала работы нажмите «Мои задачи» или «Добавить задачу».
    """
    await message.answer(help_text)