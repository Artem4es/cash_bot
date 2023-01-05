from dotenv import load_dotenv
from logging import StreamHandler
import os
import sys
import logging

from telegram.ext import CommandHandler, Updater, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

from db import BotDB


logger = logging.getLogger(__name__)


load_dotenv()
secret_token = os.getenv('TOKEN')

db = BotDB('telebot.db')


def wake_up(update, context):
    user_id = context._user_id_and_data[0]
    username = update.message.chat.username
    name = update.message.chat.first_name
    chat = update.effective_chat
    if not db.user_exists(user_id):
        db.add_user(user_id, username)

    text = f'Привет, {name}! Напиши циферками заплаченную сумму👋'
    send_message(context, chat.id, text)


def calculation(context, update, amount=0):
    user_id = context._user_id_and_data[0]
    name = update.message.chat.first_name
    all_users = [user[0] for user in (db.get_users())]
    if amount != 0:
        db.add_sum(user_id, amount)
        message = f'Ребятки, {name}😎 только что заплатил {amount}'
        for user_id in all_users:
            send_message(context, chat_id=user_id, text=message)
    total_paid = db.total()
    numer_of_users = len(all_users)   # проверить работу!
    one_person_owes = total_paid / numer_of_users
    for user_id in all_users:
        user_total = db.total(user_id)
        user_balance = user_total - one_person_owes
        if user_balance < 0:
            message = f'С тебя {"%.2f" % abs(user_balance)}'
            send_message(context, chat_id=user_id, text=message)
        elif user_balance > 0:
            message = f'👍Ты в плюсе на {"%.2f" % user_balance}'
            send_message(context, chat_id=user_id, text=message)
        elif user_balance == 0:
            message = f'Уникальный момент, всё поровну!🥳'
            send_message(context, chat_id=user_id, text=message)


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


def sum_recognition(update, context):
    message = update.message.text
    name = update.message.chat.first_name
    user_id = context._user_id_and_data[0]
    chat_id = update.effective_chat.id
    all_users = [user[0] for user in (db.get_users())]
    all_usernames = [user[0] for user in (db.get_usernames())]
        
        
    # if message.lower() in ('ок', 'ok'):
    #     db.remove_complain(user_id)
    #     message = 'Рад, что вопросик решён, режим психолога выключен)'
    #     send_message(context, chat_id, text=message)
    #     return
    # if message.lower() in confiramtion_messages:
    #     db.set_complain(user_id)
    #     message = 'Расскажи, в чём дело?'
    #     send_message(chat_id, text=message)

    # elif db.complain_stataus(user_id):
    #     problem_recognition(update, context)
    #     return

    if user_id in all_users:
        try:
            if message == '👀Никого не надо':
                context.bot.send_message(chat_id, text='Ладно, не шали так больше🤡', reply_markup=ReplyKeyboardRemove())
                return

            elif message in all_usernames:
                db.delete_user(username=message)
                message = f'Пользователь {name}💩 удалил {message}'
                for user_id in all_users:
                    send_message(context, chat_id, text=message)
                return
            amount = float(update.message.text)
            calculation(context, update, amount)  
        except:
            # message = f'{name}, по балде надаю 🤪!'
            message = 'data:image/jpeg;base64,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!'
            send_message(chat_id=chat_id, text=message, context=context)
            logger.error(f'Введено что-то не то: {update.message.text}.Либо не удалось отправить сообщение')
    else:
        message = 'Я не умею считать твои деньги. Чтобы добавиться в чат введи /start'
        send_message(context, chat_id, message)


def reset_sum(update, context):
    all_users = [user[0] for user in (db.get_users())]
    db.reset_sum()
    name = update.message.chat.first_name
    message = f'Сумма обнулена пользвателем {name}💪'
    for chat_id in all_users:
        send_message(context, chat_id, text=message)



def send_message(context, chat_id, text):
    logger.debug(f'Начата отправка сообщения в чат: {chat_id}')
    try:
        context.bot.send_message(chat_id=chat_id, text=text)
        logger.debug(f'Сообщение отправлено в чат {chat_id}')
    except Exception as error:
        logger.error(f'Не удалось отправить сообщение пользователю {chat_id}. Ошибка {error}')    

def delete_user(update, context):
    all_usernames = [user[0] for user in (db.get_usernames())]
    all_usernames.append('👀Никого не надо')
    chat_id = update.effective_chat.id
    reply_markup = ReplyKeyboardMarkup(keyboard=[all_usernames], resize_keyboard=True, selective=True)

    try:
        context.bot.send_message(chat_id=chat_id, text='Кого кикнуть?☠️', reply_markup=reply_markup)
    except Exception as error:
        logger.error(f'Не удалось отправить сообщение об удалении юзера. {error}')





def main():
    updater = Updater(token=secret_token)
    updater.dispatcher.add_handler(CommandHandler('start', wake_up))
    updater.dispatcher.add_handler(CommandHandler('reset', reset_sum))
    updater.dispatcher.add_handler(CommandHandler('how_much', how_much))
    updater.dispatcher.add_handler(CommandHandler('kick_user', delete_user))
    updater.dispatcher.add_handler(
        MessageHandler(Filters.text, sum_recognition)
    )

    try:
        updater.start_polling()
        updater.idle()
    except:
        logger.critical('Не верный телеграм токен!')
        sys.exit()
    


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
