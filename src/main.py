from dotenv import load_dotenv
from logging import StreamHandler
import datetime
import os
import re
import sys
import logging

from telegram.ext import CommandHandler, Updater, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot, BotCommand

from src.crud import user_exists, add_user, get_users, add_payment, get_period_payments, set_user_owes, set_min_pays_since, \
    delete_db_user, get_db_all_payments, delete_payments
from src.config import settings

from src.models import Users



logger = logging.getLogger(__name__)

load_dotenv()
SECRET_TOKEN = os.getenv('TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')






def wake_up(update, context):
    tg_id = context._user_id_and_data[0]
    username = update.message.chat.username
    name = update.message.chat.first_name
    chat = update.effective_chat
    # if not db.user_exists(user_id):
    if not user_exists(tg_id):
        # db.add_user(user_id, username)  # дата расчётов по умолчанию дата регистрации
        add_user(tg_id, username)  # дата расчётов по умолчанию дата регистрации
        reply_markup = ReplyKeyboardMarkup(keyboard=[['Поделить всё с момента регистрации первого участника'],['Считать мой долг с текущей даты']], resize_keyboard=True)
        message = f'Привет, {name}! Возможно уже были платежи (сумму можно посмотреть в меню). Выбери что делать, пожалуйста!'
        send_message(context, chat.id, message, reply_markup=reply_markup)
        return

    text = f'Привет, {name}! Напиши циферками заплаченную сумму👋'
    send_message(context, chat.id, text, reply_markup=ReplyKeyboardRemove())


def calculation(update, context, amount=None):
    # получаем всех юзеров и регим их аттрибуты
    name = update.effective_chat.username
    # получаем всех юзеров и регим их аттрибуты
    user_info = dict()
    all_users: list[Users] = get_users()
    # all_users = [user[0] for user in (db.get_users())]
    for user in all_users:
        # user_id, username, pays_since = db.get_user_data(user_id)
        user_info[user.username] = [user.tg_id, user.pays_since]
        

    tg_id = context._user_id_and_data[0]
    if amount is not None:
        # db.add_sum(user_id, amount)
        add_payment(tg_id, amount)
        message = f'Ребятки, {name}😎 только что заплатил {amount}'
        if len(all_users) == 1:
            message = f'{name} ты пока один в чатике и должен сам себе)'
            return send_message(context=context, chat_id=tg_id, text=message)

        for user in all_users:
            send_message(context=context, chat_id=user.tg_id, text=message)

    times = list()
    for values in user_info.values():
        times.append(values[1])
    period_qty = len(times) - 1
    number_of_users = 1
    for i in range(period_qty):

        since = user_info[list(user_info)[i+1]][1]
        until = str(datetime.datetime.now())
        if not i == (period_qty-1):
            until = user_info[list(user_info)[i+2]][1]
        number_of_users += 1  # перенести выше
        # totally_paid = db.get_period_payments(since=since, until=until)
        totally_paid: float = get_period_payments(since=since, until=until)
        if not totally_paid:
            send_message(context, tg_id, 'Ты ничего не должен, потому что никто не платил')
        for i in range(number_of_users):
            username = list(user_info)[i]
            tg_id = user_info[username][0]
            totally_user: float = get_period_payments(since=since, until=until, user_id=tg_id)
            one_person_owes = totally_paid / number_of_users
            user_balance = round((totally_user - one_person_owes), 2)
            user_info[username].append(user_balance) 
    user_owes_dict = dict()       
    for username, value in user_info.items():
        user_owes = 0 
        for i in range(2, len(value)):
            user_owes += value[i]
            user_owes_dict[username] = user_owes
    
    for user, owes in user_owes_dict.items():
        if owes < 0:
            message = f'С тебя {abs(owes)} тугриков🤸🏻‍♂️'
        elif owes > 0:
            message = f'👍Ты в плюсе на {owes} тугриков' 
        else:
            message = 'Вот это да, ты в нулину!🥳'
        tg_id = user_info[user][0]
        send_message(context, tg_id, message)
        # db.set_user_owes(tg_id, owes)
        set_user_owes(tg_id, owes)



def how_much(update, context):
    calculation(update, context)


def sum_recognition(update, context):
    message = update.message.text
    name = update.message.chat.first_name
    tg_id = context._user_id_and_data[0]
    chat_id = update.effective_chat.id
    # all_users = [user[0] for user in (db.get_users())]
    all_users = get_users()
    all_usernames = [user.username for user in all_users]
    user_tg_ids = [user.tg_id for user in all_users]
    if tg_id in user_tg_ids:
        # wants_to_say = db.public_message_status(tg_id)   ### ЭТО можно реализовать через STATE aiogram
        try:
            # if wants_to_say == True:
            #     for user in all_users:
            #         send_message(context, user, message)
            #     # db.reset_public(tg_id)
            #     return

            if message == 'Поделить всё с момента регистрации первого участника':
                # db.set_pays_since(tg_id)
                set_min_pays_since(tg_id)
                return send_message(context, chat_id, 'Окей!Считаем от истоков)', reply_markup=ReplyKeyboardRemove())  # в будущем добавить дату с которой

            elif message == 'Считать мой долг с текущей даты':
                return send_message(context, chat_id, 'Окей, будем считать с текущего момента', reply_markup=ReplyKeyboardRemove())

            elif message == '👀Никого не надо':
                send_message(context=context, chat_id=chat_id, text='Ладно, не шали так больше🤡', reply_markup=ReplyKeyboardRemove())
                return

            elif message in all_usernames:
                # db.delete_user(username=message)
                delete_db_user(username=message)
                message = f'Пользователь {name}💩 удалил {message}'
                for tg_id in all_users:
                    send_message(context=context, chat_id=tg_id, text=message, reply_markup=ReplyKeyboardRemove())
                return
            validated_message = re.sub(r'(, )|(,)|(. )', '.', message)
            amount = float(validated_message)
            calculation(update, context, amount)

        except:
            message = f'{name},это не число! По балде надаю 🤪!'
            send_message(chat_id=chat_id, text=message, context=context, reply_markup=ReplyKeyboardRemove())
            logger.error(f'Введено что-то не то: {update.message.text}.Либо не удалось отправить сообщение')
    else:
        
        message = 'Я тебя не знаю! Если ты хочешь добавиться нажми /start'
        send_message(context, chat_id, message)


def reset_sum(update, context):
    # all_users = [user[0] for user in (db.get_users())]
    all_users = get_users()
    # db.reset_sum()
    # db.set_user_owes()
    delete_payments()
    set_user_owes()
    name = update.message.chat.first_name
    message = f'Сумма обнулена пользователем {name}💪'
    for user in all_users:
        send_message(context, user.tg_id, text=message)



def send_message(context, chat_id, text, parse_mode=None, reply_markup=None):
    logger.debug(f'Начата отправка сообщения в чат: {chat_id}')
    try:
        context.bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode, reply_markup=reply_markup)
        logger.debug(f'Сообщение отправлено в чат {chat_id}')
    except Exception as error:
        logger.error(f'Не удалось отправить сообщение пользователю {chat_id}. Ошибка {error}') 

def group_message(update, context):
    chat_id = update.effective_chat.id
    # db.set_public(chat_id)
    context.bot.send_message(chat_id=chat_id, text='Теперь можно написать сообщение и его увидят все участники')

def delete_user(update, context):
    # all_users = [user[0] for user in (db.get_users())]
    all_users = get_users()
    users_tg_ids = {user.tg_id for user in all_users}
    all_usernames = [user.username for user in all_users]
    tg_id = update.effective_chat.id
    if tg_id in users_tg_ids:
        all_usernames.append('👀Никого не надо')
        tg_id = update.effective_chat.id
        reply_markup = ReplyKeyboardMarkup(keyboard=[all_usernames], resize_keyboard=True, selective=True)

        try:
            context.bot.send_message(chat_id=tg_id, text='Кого кикнуть?☠️', reply_markup=reply_markup) # перенести в send message

        except Exception as error:
            logger.error(f'Не удалось отправить сообщение об удалении юзера. {error}')
            return

    else:
        message = 'Я тебя не знаю! Если ты хочешь добавиться нажми /start'
        send_message(context, tg_id, message)


def get_all_payments(update=None, context=None):
    # if db.get_all_payments():
    all_payments = get_db_all_payments()
    if all_payments:
        # форматируем кортежи результатов ('username', 10.99, datetime)
        new_list = map(lambda el: (str(el[0]).center(10), str(el[1]).center(6), str(el[2])), all_payments)
        message = '\n'.join(map(lambda el: ' '.join(el), new_list))

        message = f"```\n{message}\n```"
    else:
        message = 'Пока в базе нет платежей'

    if update and context:
        chat_id = update.effective_chat.id

    # return send_message(context=context, chat_id=chat_id,text='Пока в базе нет платежей', parse_mode='MarkdownV2')
    return send_message(context=context, chat_id=chat_id, text=message, parse_mode='MarkdownV2')


def main():
    updater = Updater(token=settings.bot_token)
    bot = Bot(token=settings.bot_token)
    bot.send_message(settings.admin_id, 'Меня запустили снова, ура!')
    commands = [BotCommand('start', 'Стартуем!'), BotCommand('reset', 'Обнулить должок у всех'),
                BotCommand('how_much', 'Сколько с меня?'), BotCommand('all_payments', 'История платежей'),
                BotCommand('kick_user', 'Удалить юзера'), BotCommand('group_message', 'Написать всем в этом чате')]
    bot.set_my_commands(commands)
    updater.dispatcher.add_handler(CommandHandler('start', wake_up))
    updater.dispatcher.add_handler(CommandHandler('reset', reset_sum))
    updater.dispatcher.add_handler(CommandHandler('how_much', how_much))
    updater.dispatcher.add_handler(CommandHandler('all_payments', get_all_payments))
    updater.dispatcher.add_handler(CommandHandler('kick_user', delete_user))
    updater.dispatcher.add_handler(CommandHandler('group_message', group_message))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, sum_recognition))

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
    file_handler = logging.FileHandler('src/logs/bot.log', encoding='UTF-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(terminal_handler)
    logger.addHandler(file_handler)

    main()
