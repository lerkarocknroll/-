import telebot
from telebot import custom_filters
from telebot.storage import StateMemoryStorage
from config import BOT_TOKEN
from bot.handlers import register_handlers


def main():
    try:
        print("Starting EnglishCard Telegram Bot...")

        # Тест подключения к БД
        try:
            from database.db_config import Database
            db = Database()
            print("Database connection successful")
            db.close()
        except Exception as e:
            print(f"Database error: {e}")
            print("Bot will continue but may not work properly")

        # Создание бота
        state_storage = StateMemoryStorage()
        bot = telebot.TeleBot(BOT_TOKEN, state_storage=state_storage)

        # Удаление webhook
        try:
            bot.remove_webhook()
            print("Webhook removed")
        except:
            pass

        # Регистрация обработчиков
        register_handlers(bot)
        bot.add_custom_filter(custom_filters.StateFilter(bot))

        print("Bot is running! Send /start in Telegram")
        bot.infinity_polling(skip_pending=True)

    except KeyboardInterrupt:
        print("Bot stopped")
    except Exception as e:
        print(f"Critical error: {e}")


if __name__ == "__main__":
    main()