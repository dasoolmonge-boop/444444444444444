# test_imports.py
print("1. Начало теста импортов")

try:
    print("2. Попытка импорта db_cakes...")
    import db_cakes
    print(f"3. db_cakes импортирован, функции: {dir(db_cakes)}")
except Exception as e:
    print(f"❌ Ошибка импорта db_cakes: {e}")
    import traceback
    traceback.print_exc()

print("4. Конец теста")
input("Нажмите Enter для выхода...")