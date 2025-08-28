import telebot
from telebot import types
from telebot.handler_backends import State, StatesGroup

from config import Command, WELCOME_MESSAGE, CORRECT_ANSWER, WRONG_ANSWER
from database.models import UserManager, WordManager

bot_instance = None


class BotStates(StatesGroup):
    waiting_english_word = State()
    waiting_russian_word = State()
    playing_game = State()


def register_handlers(bot):
    global bot_instance
    bot_instance = bot

    @bot.message_handler(commands=['start', 'cards'])
    def start_command(message):
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name

        UserManager.create_user(user_id, username, first_name)
        bot.send_message(message.chat.id, WELCOME_MESSAGE)
        start_new_game(message)

    @bot.message_handler(func=lambda message: message.text == Command.NEXT)
    def next_word_handler(message):
        start_new_game(message)

    @bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
    def add_word_handler(message):
        bot.send_message(
            message.chat.id,
            "📝 Введите английское слово, которое хотите добавить:",
            reply_markup=create_cancel_keyboard()
        )
        bot.set_state(message.from_user.id, BotStates.waiting_english_word, message.chat.id)

    @bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
    def delete_word_handler(message):
        user_id = message.from_user.id
        personal_words = WordManager.get_user_personal_words(user_id)

        if not personal_words:
            bot.send_message(
                message.chat.id,
                "❌ У вас нет персональных слов для удаления.",
                reply_markup=create_main_keyboard()
            )
            return

        keyboard = create_delete_words_keyboard(personal_words)
        bot.send_message(
            message.chat.id,
            "🗑 Выберите слово для удаления:",
            reply_markup=keyboard
        )

    @bot.message_handler(state=BotStates.waiting_english_word)
    def process_english_word(message):
        if message.text.lower() == 'отмена':
            bot.send_message(message.chat.id, "❌ Добавление слова отменено.")
            bot.delete_state(message.from_user.id, message.chat.id)
            start_new_game(message)
            return

        english_word = message.text.strip().title()

        try:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                if data is None:
                    data = {}
                data['english_word'] = english_word
        except:
            if not hasattr(bot, '_temp_data'):
                bot._temp_data = {}
            bot._temp_data[message.from_user.id] = {'english_word': english_word}

        bot.send_message(
            message.chat.id,
            f"✅ Английское слово: {english_word}\n"
            f"📝 Теперь введите русский перевод:",
            reply_markup=create_cancel_keyboard()
        )
        bot.set_state(message.from_user.id, BotStates.waiting_russian_word, message.chat.id)

    @bot.message_handler(state=BotStates.waiting_russian_word)
    def process_russian_word(message):
        if message.text.lower() == 'отмена':
            bot.send_message(message.chat.id, "❌ Добавление слова отменено.")
            bot.delete_state(message.from_user.id, message.chat.id)
            start_new_game(message)
            return

        user_id = message.from_user.id
        russian_word = message.text.strip().title()
        english_word = ""

        try:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                if data:
                    english_word = data.get('english_word', '')
        except:
            if hasattr(bot, '_temp_data') and user_id in bot._temp_data:
                english_word = bot._temp_data[user_id].get('english_word', '')
                del bot._temp_data[user_id]

        if not english_word:
            bot.send_message(message.chat.id, "❌ Ошибка: не найдено английское слово. Попробуйте снова.")
            start_new_game(message)
            return

        success = WordManager.add_user_word(user_id, english_word, russian_word)

        if success:
            words_count = UserManager.get_user_words_count(user_id)
            bot.send_message(
                message.chat.id,
                f"🎉 Слово добавлено!\n"
                f"🇬🇧 {english_word} - 🇷🇺 {russian_word}\n"
                f"📚 У вас теперь {words_count} слов для изучения"
            )
        else:
            bot.send_message(
                message.chat.id,
                "❌ Ошибка при добавлении слова."
            )

        bot.delete_state(message.from_user.id, message.chat.id)
        start_new_game(message)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('delete_word_'))
    def delete_word_callback(call):
        word_id = int(call.data.split('_')[2])
        user_id = call.from_user.id

        success = WordManager.delete_user_word(user_id, word_id)

        if success:
            words_count = UserManager.get_user_words_count(user_id)
            bot.answer_callback_query(call.id, "✅ Слово удалено!")
            bot.edit_message_text(
                f"🗑 Слово удалено!\n📚 У вас осталось {words_count} слов",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка удаления!")

        start_new_game(call.message)

    @bot.message_handler(func=lambda message: True, content_types=['text'])
    def handle_game_answer(message):
        user_id = message.from_user.id

        try:
            correct_word = None
            try:
                with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                    if data:
                        correct_word = data.get('correct_word')
            except:
                pass

            if not correct_word:
                start_new_game(message)
                return

            if message.text == correct_word['english_word']:
                words_count = UserManager.get_user_words_count(user_id)
                response = (
                    f"{CORRECT_ANSWER}\n"
                    f"🇷🇺 {correct_word['russian_word']} = 🇬🇧 {correct_word['english_word']}\n"
                    f"📚 Изучаете слов: {words_count}"
                )
                keyboard = create_main_keyboard()
                bot.send_message(message.chat.id, response, reply_markup=keyboard)
            else:
                response = (
                    f"{WRONG_ANSWER}\n"
                    f"Попробуйте угадать перевод слова: 🇷🇺 {correct_word['russian_word']}"
                )
                try:
                    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                        options = data.get('all_options', []) if data else []
                        if not options:
                            start_new_game(message)
                            return
                        keyboard = create_game_keyboard(options)
                        bot.send_message(message.chat.id, response, reply_markup=keyboard)
                except:
                    start_new_game(message)

        except Exception as e:
            print(f"Game answer error: {e}")
            start_new_game(message)


def start_new_game(message):
    user_id = message.from_user.id

    game_data = WordManager.get_random_word_with_options(user_id)

    if not game_data:
        bot_instance.send_message(
            message.chat.id,
            "❌ Недостаточно слов для игры!\nДобавьте персональные слова.",
            reply_markup=create_main_keyboard()
        )
        return

    try:
        bot_instance.set_state(message.from_user.id, BotStates.playing_game, message.chat.id)

        with bot_instance.retrieve_data(message.from_user.id, message.chat.id) as data:
            if data is None:
                data = {}
            data['correct_word'] = game_data['correct_word']
            data['all_options'] = game_data['all_options']
    except Exception as e:
        print(f"State save error: {e}")
        if not hasattr(bot_instance, '_game_data'):
            bot_instance._game_data = {}
        bot_instance._game_data[user_id] = {
            'correct_word': game_data['correct_word'],
            'all_options': game_data['all_options']
        }

    keyboard = create_game_keyboard(game_data['all_options'])
    question = f"🎯 Выберите перевод слова:\n🇷🇺 {game_data['russian_word']}"
    bot_instance.send_message(message.chat.id, question, reply_markup=keyboard)


def create_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(
        types.KeyboardButton(Command.NEXT),
        types.KeyboardButton(Command.ADD_WORD),
        types.KeyboardButton(Command.DELETE_WORD)
    )
    return keyboard


def create_game_keyboard(options):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    option_buttons = [types.KeyboardButton(option['english_word']) for option in options]
    keyboard.add(*option_buttons)
    keyboard.add(
        types.KeyboardButton(Command.NEXT),
        types.KeyboardButton(Command.ADD_WORD),
        types.KeyboardButton(Command.DELETE_WORD)
    )
    return keyboard


def create_cancel_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.add(types.KeyboardButton('Отмена'))
    return keyboard


def create_delete_words_keyboard(words):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for word in words:
        button_text = f"🗑 {word['english_word']} - {word['russian_word']}"
        callback_data = f"delete_word_{word['word_id']}"
        keyboard.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    return keyboard