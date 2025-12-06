# 💿 Встановлення

Детальна інструкція з встановлення SattelishMaps для локальної розробки.

## Системні вимоги

### Мінімальні вимоги
- **OS**: Linux, macOS, або Windows 10/11 з WSL2
- **RAM**: 4 GB (рекомендовано 8 GB)
- **Disk**: 5 GB вільного місця
- **CPU**: 2 cores (рекомендовано 4 cores)

### Програмне забезпечення

#### Обов'язково
- **Docker** 20.10+ та **Docker Compose** 2.0+
- **Git** 2.30+

#### Для локальної розробки (опціонально)
- **Python** 3.11 або новіше
- **pip** 23.0+
- **Node.js** 18+ (для frontend розробки)

## Варіанти встановлення

### Варіант 1: Docker (Рекомендовано)

Найпростіший спосіб для початку роботи.

#### 1. Встановити Docker

**Linux (Ubuntu/Debian):**
```bash
# Оновити пакети
sudo apt update

# Встановити Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Додати користувача до групи docker
sudo usermod -aG docker $USER
newgrp docker

# Перевірити встановлення
docker --version
docker-compose --version
```

**macOS:**
```bash
# Завантажити Docker Desktop з https://www.docker.com/products/docker-desktop
# Або через Homebrew:
brew install --cask docker
```

**Windows:**
1. Встановити WSL2: https://docs.microsoft.com/en-us/windows/wsl/install
2. Завантажити Docker Desktop: https://www.docker.com/products/docker-desktop

#### 2. Клонувати репозиторій

```bash
git clone https://github.com/Skriplss/SattelishMaps.git
cd SattelishMaps
```

#### 3. Налаштувати змінні середовища

```bash
cp .env.example .env
# Відредагувати .env (див. розділ Конфігурація)
```

#### 4. Запустити

```bash
docker-compose up -d
```

### Варіант 2: Локальна розробка (без Docker)

Для розробників, які хочуть запускати сервіси локально.

#### 1. Встановити Python 3.11+

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**macOS:**
```bash
brew install python@3.11
```

**Windows:**
Завантажити з https://www.python.org/downloads/

#### 2. Клонувати репозиторій

```bash
git clone https://github.com/Skriplss/SattelishMaps.git
cd SattelishMaps
```

#### 3. Створити віртуальне середовище

```bash
# Створити venv
python3.11 -m venv .venv

# Активувати
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

#### 4. Встановити залежності

```bash
# Backend залежності
pip install -r requirements.txt

# Backend додаткові залежності
cd backend
pip install -r requirements.txt
cd ..
```

#### 5. Налаштувати змінні середовища

```bash
cp .env.example .env
cp backend/.env.example backend/.env
# Відредагувати обидва файли
```

#### 6. Запустити backend

```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

#### 7. Запустити frontend (в окремому терміналі)

```bash
# Простий HTTP сервер
cd frontend
python -m http.server 3000

# Або з Node.js
npx http-server -p 3000
```

## Налаштування бази даних

### Supabase (Рекомендовано)

1. Створити проект на https://supabase.com/
2. Перейти в **SQL Editor**
3. Виконати скрипт з `database/schema.sql`
4. Скопіювати credentials у `.env`

### Локальний PostgreSQL (Опціонально)

#### Встановити PostgreSQL з PostGIS

**Linux (Ubuntu/Debian):**
```bash
sudo apt install postgresql-15 postgresql-15-postgis-3
```

**macOS:**
```bash
brew install postgresql@15 postgis
```

#### Створити базу даних

```bash
# Увійти в PostgreSQL
sudo -u postgres psql

# Створити БД
CREATE DATABASE sattelishmaps;
\c sattelishmaps

# Увімкнути PostGIS
CREATE EXTENSION postgis;

# Створити користувача
CREATE USER sattelish WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE sattelishmaps TO sattelish;
```

#### Виконати міграції

```bash
psql -U sattelish -d sattelishmaps -f database/schema.sql
```

## Встановлення інструментів розробки

### Python інструменти

```bash
# Активувати venv
source .venv/bin/activate

# Встановити dev залежності
pip install ruff mypy pytest pytest-cov black isort

# Або через requirements-dev.txt (якщо є)
pip install -r requirements-dev.txt
```

### Pre-commit hooks (опціонально)

```bash
pip install pre-commit
pre-commit install
```

## Перевірка встановлення

### Перевірити Python версію

```bash
python --version  # Має бути 3.11+
```

### Перевірити залежності

```bash
pip list | grep -E "fastapi|uvicorn|rasterio|shapely"
```

### Перевірити Docker

```bash
docker --version
docker-compose --version
docker ps
```

### Запустити тести

```bash
# Якщо є тести
pytest tests/
```

## Наступні кроки

✅ Встановлення завершено! Тепер:

1. 📖 Прочитайте [Конфігурацію](configuration.md) для налаштування
2. 🚀 Перейдіть до [Швидкого старту](quick-start.md) для запуску
3. 🔧 Ознайомтеся з [Development Guide](../development/README.md)

## Проблеми при встановленні?

### Docker не запускається

```bash
# Перевірити статус Docker
sudo systemctl status docker

# Перезапустити Docker
sudo systemctl restart docker
```

### Python залежності не встановлюються

```bash
# Оновити pip
pip install --upgrade pip setuptools wheel

# Встановити build tools (Linux)
sudo apt install python3-dev build-essential

# Встановити GDAL (для rasterio)
sudo apt install libgdal-dev
```

### Порти зайняті

```bash
# Перевірити що використовує порт 8000
sudo lsof -i :8000

# Змінити порт у docker-compose.yml
# ports:
#   - "8001:8000"  # Використати 8001 замість 8000
```

Більше рішень у [Troubleshooting Guide](../development/troubleshooting.md).
