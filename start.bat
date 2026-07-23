@echo off
echo ========================================
echo    AI Agent - Быстрый старт
echo ========================================
echo.

echo [1/4] Проверка Python...
python --version
if errorlevel 1 (
    echo ОШИБКА: Python не найден. Установите Python 3.11+
    pause
    exit /b 1
)

echo.
echo [2/4] Установка зависимостей...
cd backend
pip install -r requirements.txt -q
if errorlevel 1 (
    echo ОШИБКА: Не удалось установить зависимости
    pause
    exit /b 1
)

echo.
echo [3/4] Выбор модели...
python select_model.py
if errorlevel 1 (
    echo Предупреждение: Ошибка выбора модели
)

echo.
echo [4/4] Запуск сервера...
echo Сервер запустится на http://localhost:8000
echo API документация: http://localhost:8000/docs
echo Нажмите Ctrl+C для остановки
echo.
python -m uvicorn app.main:app --reload --port 8000

pause
