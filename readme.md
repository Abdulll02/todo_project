# ToDo Bot Project

Телеграм-бот для управления задачами с бекендом на Django.

## 🚀 Технологии

- **Backend**: Django + Django REST Framework
- **Database**: PostgreSQL
- **Bot**: Aiogram 3.x
- **Queue**: Redis + Celery
- **Containerization**: Docker + Docker Compose

## 📦 Установка и запуск

### Предварительные требования

- Docker
- Docker Compose
- Telegram Bot Token (от @BotFather)

### 1. Клонирование репозитория

git clone <https://github.com/Abdulll02/todo_project.git>

cd todo_project

### 2. Настройка переменных окружения
Создайте файл .env в корне проекта:

# Django
SECRET_KEY=your-django-secret-key

DEBUG=True

DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend

# Database
POSTGRES_DB=todo_db

POSTGRES_USER=todo_user

POSTGRES_PASSWORD=todo_password

DB_HOST=db

DB_PORT=5432

# Telegram Bot

BOT_TOKEN=your-telegram-bot-token

DJANGO_API_URL=http://backend:8000/api


### 3. Запуск проекта

docker-compose up -d

Сервисы будут доступны по следующим адресам:

Django API: http://localhost:8000

Admin Panel: http://localhost:8000/admin

PostgreSQL: localhost:5432

Redis: localhost:6379


### 4. Первоначальная настройка

Создание суперпользователя Django:
docker-compose exec backend python manage.py createsuperuser

Выполнение миграций:
docker-compose exec backend python manage.py migrate

Сбор статических файлов:
docker-compose exec backend python manage.py collectstatic --noinput


### 5. Использование
1) Админ-панель: http://localhost:8000/admin
 - Управление задачами и категориями
 - Просмотр пользователей


2) API Endpoints:

GET /api/tasks/ - список задач
POST /api/tasks/ - создание задачи
GET /api/categories/ - список категорий

3) Telegram Bot:

Найдите бота в Telegram по юзернейму

Используйте команду /start для начала работы

Доступные функции:

 - 📋 Просмотр задач

 - ➕ Добавление задач

 - 🏷️ Управление категориями

### 🛠 Команды управления

Просмотр логов:
docker-compose logs -f

Остановка проекта:
docker-compose down

Пересборка образов:
docker-compose build --no-cache

Выполнение команд в контейнере:
docker-compose exec backend python manage.py <command>
