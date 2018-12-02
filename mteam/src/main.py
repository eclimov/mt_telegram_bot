import sys
sys.path.append("../..")

import datetime
import json
from json import JSONEncoder

from apiai import apiai

from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove
from mteam import config
import config as config_global
from mteam.src.utils import get_exchange_rate

emojis = config_global.emojis


# telegram examples: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets

############################### Bot ############################################
def start(bot, update):
    '''
    update.message.reply_text(
        start_message(),
        reply_markup=main_menu_keyboard()
    )
    '''
    update.message.reply_text(
        start_message(),
        reply_markup=authenticate_keyboard()
    )


'''
how to avoid auth frauds: https://groosha.gitbooks.io/telegram-bot-lessons/content/chapter9.html
+
Compare user_id from contact with chat_id of user, who sent this contact
'''


def authenticate(bot, update):
    contact = update.message.contact
    bot.send_message(
        chat_id=update.message.chat.id,
        text=f'Received Contact: {contact}',
    )
    bot.send_message(
        chat_id=update.message.chat.id,
        text=main_menu_message(),
        reply_markup=main_menu_keyboard()
    )
    main_menu(bot, update)


def main_menu(bot, update):
    query = update.callback_query
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=main_menu_message(),
        reply_markup=main_menu_keyboard()
    )


def day_offs_menu(bot, update):
    query = update.callback_query
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=main_menu_message(),
        reply_markup=day_offs_menu_keyboard()
    )


def day_offs_mine(bot, update):
    query = update.callback_query

    personal_day_offs_count = 0
    text = f'You have {personal_day_offs_count} day-offs left'

    bot.answer_callback_query(callback_query_id=query.id, text=text, show_alert=True)


def day_offs_paid(bot, update):
    query = update.callback_query

    this_year_day_offs = {
        "New Year": '1/1/2019',
        "New Year 2": '2/1/2019',
        "Christmas (Old Style)": '7/1/2019',
        "instead of 1.05.2019": '22/4/2019',
        "Easter": '29/4/2019',
        "Paştele Blajinilor": '6/5/2019',
        "instead of 14.10.2019": '1/11/2019',
        "instead of 8.03.2019": '23/12/2019',
        "Christmas (New Style)": '25/12/2019'
    }
    text = '*Paid day-offs:*\n' + '\n'.join(
        [f'{holiday} - {this_year_day_offs[holiday]}' for holiday in this_year_day_offs]
    )

    bot.send_message(
        chat_id=query.message.chat_id,
        text=text,
        parse_mode='Markdown'
    )


def salary(bot, update):
    query = update.callback_query
    bot.answer_callback_query(callback_query_id=query.id, text="0", show_alert=True)


def currency(bot, update):
    query = update.callback_query

    try:
        today = datetime.datetime.today()
        today_exchange_rate = get_exchange_rate(47, today)  # EUR
        last_day_of_prev_month = today.replace(day=1) - datetime.timedelta(days=1)
        prev_month_exchange_rate = get_exchange_rate(47, last_day_of_prev_month)  # EUR
        text = f"{prev_month_exchange_rate} -> {today_exchange_rate}"
    except ConnectionError as e:
        text = "Could not connect to server. Try again later"
    except IndexError as e:
        text = "Error: unexpected API response. Please, contact responsible IT rep to fix this problem"
    except Exception as e:
        text = "Error. Please, contact responsible IT rep to fix this problem"

    bot.answer_callback_query(callback_query_id=query.id, text=text, show_alert=True)


def about_us(bot, update):
    bot.send_photo(
        chat_id=update.callback_query.message.chat_id,
        caption=config.about_info,
        photo=open('../assets/logo.png', 'rb')
    )


def textMessage(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Direct messaging doesn't work yet")


############################ Keyboards #########################################
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton(emojis['palm_tree'] + ' Day-offs', callback_data='day_offs_menu')],
        [InlineKeyboardButton(emojis['euro_banknote'] + ' Salary', callback_data='salary')],
        [InlineKeyboardButton(emojis['chart_upwards'] + ' Currency', callback_data='currency')],
        [InlineKeyboardButton(emojis['about'] + ' About us', callback_data='about_us')],
    ]
    return InlineKeyboardMarkup(keyboard)


def day_offs_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton(emojis['airplane'] + ' My day-offs', callback_data='day_offs_mine')],
        [InlineKeyboardButton(emojis['snowman'] + ' Paid day-offs', callback_data='day_offs_paid')],
        [InlineKeyboardButton(emojis['back'] + ' Main menu', callback_data='main')],
    ]
    return InlineKeyboardMarkup(keyboard)


def authenticate_keyboard():
    keyboard = [
        [KeyboardButton('Authenticate', request_contact=True, callback_data='authenticate')]
    ]

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


############################# Messages #########################################
def main_menu_message():
    return 'Choose an option:'


def start_message():
    return 'Authentication required'


############################# Handlers #########################################

if __name__ == '__main__':
    api_keys = config.api_keys
    updater = Updater(token=api_keys['telegram_bot_token'])  # Токен API к Telegram
    dispatcher = updater.dispatcher

    handlers = [
        MessageHandler(Filters.text, textMessage),
        CommandHandler('start', start),
        # CallbackQueryHandler(authenticate, pattern='authenticate'),
        MessageHandler(Filters.contact, authenticate),

        CallbackQueryHandler(main_menu, pattern='main'),
        CallbackQueryHandler(day_offs_menu, pattern='day_offs_menu'),
        CallbackQueryHandler(day_offs_mine, pattern='day_offs_mine'),
        CallbackQueryHandler(day_offs_paid, pattern='day_offs_paid'),
        CallbackQueryHandler(salary, pattern='salary'),
        CallbackQueryHandler(currency, pattern='currency'),
        CallbackQueryHandler(about_us, pattern='about_us')
    ]

    for handler in handlers:
        dispatcher.add_handler(handler)

    # Начинаем поиск обновлений
    updater.start_polling(clean=True)
    # Останавливаем бота, если были нажаты Ctrl + C
    updater.idle()
