from dotenv import load_dotenv
from logging import StreamHandler
import os
import sys
import logging

from telegram.ext import CommandHandler, Updater, MessageHandler, Filters

from db import BotDB


KSENIA_ID = 157256682
ARTEM_ID = 291198651

logger = logging.getLogger(__name__)


load_dotenv()
secret_token = os.getenv('TOKEN')

db = BotDB('telebot.db')


def wake_up(update, context):  # запросить данные из базы id
    user_id = context._user_id_and_data[0]
    username = update.message.chat.username
    name = update.message.chat.first_name
    chat = update.effective_chat
    if not db.user_exists(user_id):
        db.add_user(user_id, username)

    if name == 'Ksenia':
        text = 'Привет, Ксюш 👩! Cколько заплатила?'
    elif name == 'Artem':
        text = 'Привет, Тём! Cколько заплатил?'
    else:
        text = 'Я тебя не знаю. Попроси разработчика добавить тебя в чат.'
    send_message(context, chat.id, text)


def calculation(context, update, amount=0):
    user_id = context._user_id_and_data[0]
    name = update.message.chat.first_name
    if amount != 0:
        db.add_sum(user_id, amount)
    total_paid = db.total()
    total_user = db.total(user_id)

    one_person_owes = total_paid / 2  # можно ввести число пользователей
    user_balance = total_user - one_person_owes
    if user_balance < 0:
        message = f'С тебя {"%.2f" % abs(user_balance)}'
        return message
    elif user_balance > 0:
        message = f'Ты в плюсе на {"%.2f" % abs(user_balance)}'
        return message
    elif user_balance == 0:
        message = f'Уникальный момент, всё поровну!'
        return message


def how_much(update, context):
    message = calculation(context, update)
    send_message(context, chat_id=update.effective_chat.id, text=message)


confiramtion_messages = (
    'да',
    'нет',
    'не согласен',
    'не согласна',
    'да!',
    'нет!',
)
problem_words = (
    'целует',
    'цалует',
    'обнимает',
    'обнимашки',
    'цветочки',
    'по балде надаю',
)


def problem_recognition(update, context):
    message = update.message.text
    chat_id = update.effective_chat.id
    for word in message.lower().split():
        if word in problem_words:
            reason = word
            message = f'Почему он не {reason}? Я ему надаю по балде!😈'
            send_message(context, chat_id, text=message)
    else:
        message = f'Ребятки, урегулируйте спорный моментик 😈. Если решили - напишите мне слово ок и я отстану)'
        send_message(context, chat_id, text=message)


def sum_recognition(
    update, context
):  # получаем цифру (с описанием потом). сохраняем в базу цифру и кто платил
    message = update.message.text
    payer = update.message.chat.first_name
    user_id = context._user_id_and_data[0]
    chat_id = update.effective_chat.id
    username = update.message.chat.username
    if message.lower() in ('ок', 'ok'):
        db.remove_complain(user_id)
        message = 'Рад, что вопросик решён, режим психолога выключен)'
        send_message(context, chat_id, text=message)
        return
    if message.lower() in confiramtion_messages:
        db.set_complain(user_id)
        message = 'Расскажи, в чём дело?'
        send_message(chat_id, text=message)

    elif db.complain_stataus(user_id):
        problem_recognition(update, context)
        return

    if payer in ['Artem', 'Ksenia']:  # список польователей если есть смысл
        try:
            amount = float(update.message.text)
        except:
            if payer == 'Artem':
                message = f'{username}, по балде надаю 🤪! Нужно вводить число или что-то пошло не так?'
            send_message(chat_id=chat_id, text=message, context=context)
            logger.error(f'Введено что-то не то: {update.message.text}')
            raise TypeError('Введено не число')
        message = calculation(context, update, amount)
        send_message(context, chat_id, message)
    else:
        message = 'Я не умею считать твои деньги. Свяжись с разработчиком'
        logger.error(f'Новый юзер залез в чат: {username}')
        send_message(context, ARTEM_ID, message)
        send_message(context, KSENIA_ID, message)


def reset_sum(update, context):
    all_users = db.get_users()
    db.reset_sum()
    payer = update.message.chat.first_name
    message = f'Сумма обнулена пользвателем {payer}'
    for chat_id in all_users:
        send_message(context, chat_id[0], text=message)


def send_message(context, chat_id, text):
    context.bot.send_message(chat_id=chat_id, text=text)
    logger.debug(f'Сообщение отправлено в чат {chat_id}')


def main():
    updater = Updater(token=secret_token)

    updater.dispatcher.add_handler(CommandHandler('start', wake_up))
    updater.dispatcher.add_handler(CommandHandler('reset', reset_sum))
    updater.dispatcher.add_handler(CommandHandler('how_much', how_much))
    updater.dispatcher.add_handler(
        MessageHandler(Filters.text, sum_recognition)
    )

    try:
        updater.start_polling()
    except:
        logger.critical('Не верный телеграм токен!')
        sys.exit()
    updater.idle()


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s, %(levelname)s, %(name)s, %(message)s, Строка: %(lineno)s,'
    )
    terminal_handler = StreamHandler(sys.stdout)
    terminal_handler.setFormatter(formatter)
    file_handler = logging.FileHandler('bot.log', encoding='UTF-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(terminal_handler)
    logger.addHandler(file_handler)
    logging.basicConfig(
        level=logging.DEBUG,
        filename='program.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    )

    main()
