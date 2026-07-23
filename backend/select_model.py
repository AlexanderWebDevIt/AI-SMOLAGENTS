import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.models import get_models, get_chat_models, get_active_model, set_active_model


def main():
    print("=" * 50)
    print("     AI Agent - Выбор модели")
    print("=" * 50)
    print()

    models = get_chat_models()
    if not models:
        print("Ошибка: Не удалось получить список моделей.")
        print("Проверьте, запущен ли LM Studio.")
        return

    active = get_active_model()
    print(f"Текущая модель: {active}")
    print()
    print("Доступные модели:")
    print("-" * 50)

    for i, m in enumerate(models, 1):
        marker = " *" if m["id"] == active else ""
        print(f"  {i}. {m['name']}{marker}")

    print("-" * 50)
    print()

    while True:
        try:
            choice = input("Выберите модель (номер) или Enter для текущей: ").strip()
            if not choice:
                print(f"Оставляем текущую: {active}")
                return

            idx = int(choice) - 1
            if 0 <= idx < len(models):
                selected = models[idx]
                set_active_model(selected["id"])
                print(f"Выбрана модель: {selected['name']}")
                return
            else:
                print("Неверный номер. Попробуйте снова.")
        except ValueError:
            print("Введите число.")
        except KeyboardInterrupt:
            print("\nОтмена.")
            return


if __name__ == "__main__":
    main()
