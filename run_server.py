#!/usr/bin/env python3

import sys
import os

# Добавляем путь к backend в PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from app.main import start_server
    
    if __name__ == "__main__":
        print("Запуск сервера AI-smolagents...")
        start_server()
        
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Проверьте, что все модули доступны")
    
except Exception as e:
    print(f"Ошибка запуска сервера: {e}")