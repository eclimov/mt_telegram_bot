import json
from json import JSONEncoder

from apiai import apiai

from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from eminia import config

# emojis: https://apps.timwhitlock.info/emoji/tables/unicode
emojis = {
    'back': u'\U00002b05',
    'top': u'\U000026A1',
    'about': u'\U00002754',
    'top_popular': u'\U00002B50',
    'top_new': u'\U0001F34F',
    'top_cheap': u'\U0001F4B8'
}


# telegram examples: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets

############################### Bot ############################################
def start(bot, update):
    update.message.reply_text(
        main_menu_message(),
        reply_markup=main_menu_keyboard()
    )


def main_menu(bot, update):
    query = update.callback_query
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=main_menu_message(),
        reply_markup=main_menu_keyboard()
    )


def topstock_menu(bot, update):
    query = update.callback_query
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=topstock_menu_message(),
        reply_markup=topstock_menu_keyboard()
    )


def aboutus_menu(bot, update):
    query = update.callback_query
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=aboutus_menu_message(),
        reply_markup=aboutus_menu_keyboard()
    )


def top_popular(bot, update):
    for i in range(1, 6):
        bot.send_photo(
            chat_id=update.callback_query.message.chat_id,
            caption=f'{emojis["top_popular"]} Item {i}\nprice: 0.{i}{i}€',
            photo=open('../assets/logo.jpg', 'rb')
        )


def top_new(bot, update):
    for i in range(1, 6):
        bot.send_photo(
            chat_id=update.callback_query.message.chat_id,
            caption=f'{emojis["top_new"]} Item {i}\nprice: 0.{i}{i}€',
            photo=open('../assets/logo.jpg', 'rb')
        )


def top_cheap(bot, update):
    for i in range(1, 6):
        bot.send_photo(
            chat_id=update.callback_query.message.chat_id,
            caption=f'{emojis["top_cheap"]} Item {i}\nprice: 0.{i}{i}€',
            photo=open('../assets/logo.jpg', 'rb')
        )


def textMessage(bot, update):
    request = apiai.ApiAI(api_keys['dialog_flow_client_access_token']).text_request()  # Токен API к Dialogflow
    request.lang = 'en'  # На каком языке будет послан запрос
    request.session_id = 'BatlabAIBot'  # ID Сессии диалога (нужно, чтобы потом учить бота)
    request.query = update.message.text  # Посылаем запрос к ИИ с сообщением от юзера
    responseJson = json.loads(request.getresponse().read().decode('utf-8'))
    response = responseJson['result']['fulfillment']['speech']  # Разбираем JSON и вытаскиваем ответ
    # Если есть ответ от бота - присылаем юзеру, если нет - бот его не понял
    if response:
        bot.send_message(chat_id=update.message.chat_id, text=response)
    else:
        bot.send_message(chat_id=update.message.chat_id, text='I don''t understand!')


############################ Keyboards #########################################
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton(emojis['top'] + ' TOP 5 stock', callback_data='m1')],
        [InlineKeyboardButton(emojis['about'] + ' About us', callback_data='m2')],
        [InlineKeyboardButton('Store', url='http://www.eminiatrading.com/')]
    ]
    return InlineKeyboardMarkup(keyboard)


def topstock_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton(emojis['top_popular'] + ' Most popular', callback_data='most_popular')],
        [InlineKeyboardButton(emojis['top_new'] + ' Newest', callback_data='newest')],
        [InlineKeyboardButton(emojis['top_cheap'] + ' Cheapest', callback_data='cheapest')],
        [InlineKeyboardButton(emojis['back'] + ' Main menu', callback_data='main')]
    ]
    return InlineKeyboardMarkup(keyboard)


def aboutus_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton(emojis['back'] + ' Main menu', callback_data='main')]
    ]
    return InlineKeyboardMarkup(keyboard)


############################# Messages #########################################
def main_menu_message():
    return 'Choose an option:'


def topstock_menu_message():
    return 'Choose criteria:'


def aboutus_menu_message():
    return config.about_info


############################# Handlers #########################################

if __name__ == '__main__':
    api_keys = config.api_keys
    updater = Updater(token=api_keys['telegram_bot_token'])  # Токен API к Telegram
    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.text, textMessage))

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern='main'))
    dispatcher.add_handler(CallbackQueryHandler(topstock_menu, pattern='m1'))
    dispatcher.add_handler(CallbackQueryHandler(aboutus_menu, pattern='m2'))

    dispatcher.add_handler(CallbackQueryHandler(top_popular, pattern='most_popular'))
    dispatcher.add_handler(CallbackQueryHandler(top_new, pattern='newest'))
    dispatcher.add_handler(CallbackQueryHandler(top_cheap, pattern='cheapest'))

    # Начинаем поиск обновлений
    updater.start_polling(clean=True)
    # Останавливаем бота, если были нажаты Ctrl + C
    updater.idle()
