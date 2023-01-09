from dotenv import load_dotenv
from logging import StreamHandler
import os
import re
import sys
import logging

from telegram.ext import CommandHandler, Updater, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot

from db import BotDB
db = BotDB('telebot.db')

logger = logging.getLogger(__name__)


load_dotenv()
secret_token = os.getenv('TOKEN')




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
        for user_id in all_users:
            total_paid = db.total() #
            numer_of_users = len(all_users) #
            one_person_owes = total_paid / numer_of_users #      
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
    else: 
            total_paid = db.total() #
            numer_of_users = len(all_users) #
            one_person_owes = total_paid / numer_of_users #                                                            #тут можно упростить
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


def sum_recognition(update, context):
    message = update.message.text
    name = update.message.chat.first_name
    user_id = context._user_id_and_data[0]
    chat_id = update.effective_chat.id
    wants_to_say = db.public_message_status(user_id)
    all_users = [user[0] for user in (db.get_users())]
    all_usernames = [user[0] for user in (db.get_usernames())]
        
        
    if user_id in all_users:
        try:
            if wants_to_say == True:
                for user in all_users:
                    send_message(context, user, message)
                db.reset_public(user_id)    
                return

            elif message == '👀Никого не надо':
                send_message(context=context, chat_id=chat_id, text='Ладно, не шали так больше🤡', reply_markup=ReplyKeyboardRemove())
                return

            elif message in all_usernames:
                db.delete_user(username=message)
                message = f'Пользователь {name}💩 удалил {message}'
                for user_id in all_users:
                    send_message(context=context, chat_id=user_id, text=message, reply_markup=ReplyKeyboardRemove())
                return
            validated_message = re.sub(',','.', message)
            amount = float(validated_message)
            calculation(context, update, amount)  
        except:
            message = f'{name},это не число! По балде надаю 🤪!'
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



def send_message(context, chat_id, text, parse_mode=None, reply_markup=None):
    logger.debug(f'Начата отправка сообщения в чат: {chat_id}')
    try:
        context.bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode, reply_markup=reply_markup)
        logger.debug(f'Сообщение отправлено в чат {chat_id}')
    except Exception as error:
        logger.error(f'Не удалось отправить сообщение пользователю {chat_id}. Ошибка {error}') 

def group_message(update, context):
    chat_id = update.effective_chat.id
    db.set_public(chat_id)
    context.bot.send_message(chat_id=chat_id, text='Теперь можно написать сообщение и его увидят все участники')



def delete_user(update, context):
    all_usernames = [user[0] for user in (db.get_usernames())]
    all_usernames.append('👀Никого не надо')
    chat_id = update.effective_chat.id
    reply_markup = ReplyKeyboardMarkup(keyboard=[all_usernames], resize_keyboard=True, selective=True)

    try:
        context.bot.send_message(chat_id=chat_id, text='Кого кикнуть?☠️', reply_markup=reply_markup)
    except Exception as error:
        logger.error(f'Не удалось отправить сообщение об удалении юзера. {error}')

def get_all_payments(update=None, context=None):
    if db.get_all_payments():
        new_list = [list(el) for el in db.get_all_payments()]    
        for list_el in new_list:
            for i in range(len(list_el)):
                list_el[i] = str(list_el[i]).center(15)
        for i in range(len(new_list)):
            new_list[i] = str(new_list[i])   
        message = '\n'.join(new_list)
        message = f"```\n{message}\n```"
        if update and context:
            chat_id = update.effective_chat.id
            return send_message(context=context,chat_id=chat_id,text=message, parse_mode='MarkdownV2')
        return message
    return 'Пока в базе нет платежей'


def main():
    updater = Updater(token=secret_token)
    bot = Bot(token=secret_token)
    bot.send_message(291198651, 'Меня запустили снова, ура!')
    message = get_all_payments()
    bot.send_message(291198651, message, parse_mode='MarkdownV2')
    
    updater.dispatcher.add_handler(CommandHandler('start', wake_up))
    updater.dispatcher.add_handler(CommandHandler('reset', reset_sum))
    updater.dispatcher.add_handler(CommandHandler('how_much', how_much))
    updater.dispatcher.add_handler(CommandHandler('all_payments', get_all_payments))
    updater.dispatcher.add_handler(CommandHandler('kick_user', delete_user))
    updater.dispatcher.add_handler(CommandHandler('group_message', group_message))
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
