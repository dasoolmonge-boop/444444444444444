# test_bot.py
import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("1. Начало выполнения test_bot.py")
print(f"2. Python version: {sys.version}")

async def main():
    print("3. Внутри main()")
    logger.info("4. Лог внутри main")
    print("5. Ждем 2 секунды...")
    await asyncio.sleep(2)
    print("6. Завершение main")

if __name__ == "__main__":
    print("7. Запуск asyncio.run()")
    asyncio.run(main())
    print("8. После asyncio.run()")