import datetime
import sys

sys.path.append("../..")

from src.database import Database

from telegram.ext import Updater, MessageHandler, Filters, Handler
from telegram.ext import CommandHandler, CallbackQueryHandler, DispatcherHandlerStop
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
import config as config_global
import env
from src.utils import get_exchange_rate


# telegram examples: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets
class Bot:
    def __init__(self):
        self.__db = Database('database.db')
        self.__updater = Updater(token=self.get_api_keys()['telegram_bot_token'])  # Токен API к Telegram
        self.__dispatcher = self.__updater.dispatcher
        handlers = self.get_handlers()

        # https://python-telegram-bot.readthedocs.io/en/stable/telegram.ext.dispatcher.html
        self.__dispatcher.add_handler(MessageHandler(Filters.text, self.check_user_auth), -1)
        self.__dispatcher.add_handler(CallbackQueryHandler(self.check_user_auth, pattern=''), -1)
        for handler in handlers:
            self.__dispatcher.add_handler(handler, 0)

    def is_phone_number_exists(self, phone_number):
        result = self.__db.execute(
            """
                SELECT users.id
                FROM users
                WHERE 1=1
                    AND users.phone_number = ?            
            """,
            phone_number
        ).fetchall()
        return len(result) != 0

    def is_user_registered(self, phone_number):
        result = self.__db.execute(
            """
                SELECT users.id
                FROM users
                WHERE 1=1
                    AND users.phone_number = ?
                    AND users.user_id IS NOT NULL            
            """,
            phone_number
        ).fetchall()
        return len(result) != 0


    def is_user_authenticated(self, user_id):
        result = self.__db.execute(
            """
                SELECT users.id
                FROM users
                WHERE 1=1
                    AND users.user_id = ?
                    AND users.when_authorized > date('now','-7 days')            
            """,
            user_id
        ).fetchall()
        return len(result) != 0


    def is_contact_valid(self, phone_number, user_id):
        result = self.__db.execute(
            """
                SELECT users.id
                FROM users
                WHERE 1=1
                    AND users.phone_number = ?
                    AND users.user_id = ?
            """,
            phone_number,
            user_id
        ).fetchall()
        return len(result) != 0

    def check_user_auth(self, bot, update):
        try:
            user_id = chat_id = update['callback_query']['message']['chat']['id']
        except Exception as e:
            user_id = chat_id = update['message']['chat']['id']
        if not self.is_user_authenticated(user_id):
            bot.send_message(
                chat_id=chat_id,
                text='Authentication required',
                reply_markup=self.authenticate_keyboard()
            )
            raise DispatcherHandlerStop


    def authenticate_keyboard(self):
        keyboard = [
            [KeyboardButton('Authenticate', request_contact=True, callback_data='authenticate')]
        ]

        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    def start(self, bot, update):
        update.message.reply_text(
            'Authentication required',
            reply_markup=self.authenticate_keyboard()
        )


    def main_menu(self, bot, update):
        query = update.callback_query
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=self.main_menu_message(),
            reply_markup=self.main_menu_keyboard()
        )

    def get_emoji(self, emoji):
        return config_global.emojis[emoji]

    def get_about(self):
        return env.about_info

    def get_api_keys(self):
        return env.api_keys

    '''
    how to avoid auth frauds: https://groosha.gitbooks.io/telegram-bot-lessons/content/chapter9.html
    +
    Compare user_id from contact with chat_id of user, who sent this contact
    '''
    def authenticate(self, bot, update):
        contact = update.message.contact
        if self.is_phone_number_exists(contact.phone_number):
            if not self.is_user_registered(contact.phone_number):
                self.__db.execute(
                    """
                        UPDATE users
                        SET user_id = ?
                        WHERE users.phone_number = ?
                    """,
                    contact.user_id,
                    contact.phone_number
                )
                bot.send_message(
                    chat_id=update.message.chat.id,
                    text='You have been registered'
                )
            elif not self.is_contact_valid(contact.phone_number, contact.user_id):
                bot.send_message(
                    chat_id=update.message.chat.id,
                    text='Access denied'
                )
                raise DispatcherHandlerStop
            self.__db.execute(
                """
                    UPDATE users
                    SET when_authorized = datetime('now')
                    WHERE 1=1
                        AND users.phone_number = ?
                        AND users.user_id = ?
                """,
                contact.phone_number,
                contact.user_id
            )
            bot.send_message(
                chat_id=update.message.chat.id,
                text=f'Received Contact: {contact}',
            )
            bot.send_message(
                chat_id=update.message.chat.id,
                text=self.main_menu_message(),
                reply_markup=self.main_menu_keyboard()
            )
            self.main_menu(bot, update)
        else:
            bot.send_message(
                chat_id=update.message.chat.id,
                text='Access denied'
            )


    def day_offs_menu(self, bot, update):
        query = update.callback_query
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=self.main_menu_message(),
            reply_markup=self.day_offs_menu_keyboard()
        )

    def day_offs_mine(self, bot, update):
        query = update.callback_query

        personal_day_offs_count = 0
        text = f'You have {personal_day_offs_count} day-offs left'

        bot.answer_callback_query(callback_query_id=query.id, text=text, show_alert=True)

    def day_offs_paid(self, bot, update):
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

    def salary(self, bot, update):
        query = update.callback_query
        bot.answer_callback_query(callback_query_id=query.id, text="0", show_alert=True)

    def currency(self, bot, update):
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

    def about_us(self, bot, update):
        bot.send_photo(
            chat_id=update.callback_query.message.chat_id,
            caption=self.get_about(),
            photo=open('../assets/logo.png', 'rb')
        )

    def main_menu_message(self):
        return 'Choose an option:'

    def textMessage(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="Direct messaging doesn't work yet")

    def main_menu_keyboard(self):
        keyboard = [
            [InlineKeyboardButton(self.get_emoji('palm_tree') + ' Day-offs', callback_data='day_offs_menu')],
            [InlineKeyboardButton(self.get_emoji('euro_banknote') + ' Salary', callback_data='salary')],
            [InlineKeyboardButton(self.get_emoji('chart_upwards') + ' Currency', callback_data='currency')],
            [InlineKeyboardButton(self.get_emoji('about') + ' About us', callback_data='about_us')],
        ]
        return InlineKeyboardMarkup(keyboard)

    def day_offs_menu_keyboard(self):
        keyboard = [
            [InlineKeyboardButton(self.get_emoji('airplane') + ' My day-offs', callback_data='day_offs_mine')],
            [InlineKeyboardButton(self.get_emoji('snowman') + ' Paid day-offs', callback_data='day_offs_paid')],
            [InlineKeyboardButton(self.get_emoji('back') + ' Main menu', callback_data='main')],
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_handlers(self):
        return [
            MessageHandler(Filters.text, self.textMessage),
            CommandHandler('start', self.start),
            # CallbackQueryHandler(authenticate, pattern='authenticate'),
            MessageHandler(Filters.contact, self.authenticate),

            CallbackQueryHandler(self.main_menu, pattern='main'),
            CallbackQueryHandler(self.day_offs_menu, pattern='day_offs_menu'),
            CallbackQueryHandler(self.day_offs_mine, pattern='day_offs_mine'),
            CallbackQueryHandler(self.day_offs_paid, pattern='day_offs_paid'),
            CallbackQueryHandler(self.salary, pattern='salary'),
            CallbackQueryHandler(self.currency, pattern='currency'),
            CallbackQueryHandler(self.about_us, pattern='about_us')
        ]

    def idle(self):
        # Начинаем поиск обновлений
        self.__updater.start_polling(clean=True)
        # Останавливаем бота, если были нажаты Ctrl + C
        self.__updater.idle()
