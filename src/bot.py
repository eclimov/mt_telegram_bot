import datetime
import sys

sys.path.append("../..")

from src.google_spreadsheet import GoogleSpreadsheetReader
from src.database import Database

from telegram.ext import Updater, MessageHandler, Filters, Handler
from telegram.ext import CommandHandler, CallbackQueryHandler, DispatcherHandlerStop
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ChatAction
import config as config_global
import env
from src.utils import get_exchange_rate
from functools import wraps


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(instance, *args, **kwargs):  # instance = self
        bot, update = args
        bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(instance, bot, update, **kwargs)

    return command_func


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


# telegram examples: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets
class Bot:
    def __init__(self):
        self.__db = Database('database.db')
        self.__updater = Updater(token=env.telegram_bot_token)  # Токен API к Telegram
        self.__dispatcher = self.__updater.dispatcher
        self.__gsheet = GoogleSpreadsheetReader()
        handlers = self.get_handlers()

        # https://python-telegram-bot.readthedocs.io/en/stable/telegram.ext.dispatcher.html
        self.__dispatcher.add_handler(MessageHandler(Filters.text, self.check_user_auth_handler), -1)
        self.__dispatcher.add_handler(CallbackQueryHandler(self.check_user_auth_handler, pattern=''), -1)
        for handler in handlers:
            self.__dispatcher.add_handler(handler, 0)

    def get_db_user(self, phone_number='', first_name='', last_name='', user_id=''):
        result = self.__db.execute(
            """
                SELECT users.user_id
                FROM users
                WHERE 1=1
                    AND (
                        users.phone_number = ?
                        OR users.first_name = ?
                        OR users.last_name = ?
                        OR users.user_id = ?
                    )         
            """,
            phone_number,
            first_name,
            last_name,
            user_id
        ).fetchall()

        if len(result):
            for row in result:
                return {
                    'user_id': row['user_id']
                }

        return None

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

    def check_user_auth_handler(self, bot, update):
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

    @send_typing_action
    def start_handler(self, bot, update):
        update.message.reply_text(
            'Authentication required',
            reply_markup=self.authenticate_keyboard()
        )

    def main_menu_handler(self, bot, update):
        query = update.callback_query
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=self.main_menu_message(),
            reply_markup=self.main_menu_keyboard()
        )
        raise DispatcherHandlerStop

    def get_emoji(self, emoji):
        return config_global.emojis[emoji]

    def get_about_info(self):
        return env.about['info']

    def get_about_website(self):
        return env.about['website']

    '''
    how to avoid auth frauds: https://groosha.gitbooks.io/telegram-bot-lessons/content/chapter9.html
    +
    Compare user_id from contact with chat_id of user, who sent this contact
    '''

    @send_typing_action
    def authenticate_handler(self, bot, update):
        contact = update.message.contact
        chat_id = update.message.chat.id
        spreadsheet_record = self.__gsheet.get_record_by_condition('Phone number', contact.phone_number)

        existing_user_by_phone_number = self.get_db_user(phone_number=contact.phone_number)

        # If phone number not found in spreadsheet or someone else is trying to access data of other user
        if spreadsheet_record is None or (existing_user_by_phone_number is not None and existing_user_by_phone_number['user_id'] != chat_id):
            bot.send_message(
                chat_id=chat_id,
                text='Access denied'
            )
            raise DispatcherHandlerStop
        # Change phone number how-to: https://telegram.org/blog/telegram-me-change-number-and-pfs

        spreadsheet_record_full_name = str(spreadsheet_record['Name']).strip()
        spreadsheet_record_first_name, spreadsheet_record_last_name = spreadsheet_record_full_name.split()
        spreadsheet_record_phone_number = str(spreadsheet_record['Phone number']).strip()

        if spreadsheet_record_phone_number == contact.phone_number:
            if self.get_db_user(first_name=spreadsheet_record_first_name, last_name=spreadsheet_record_last_name) is None:
                self.__db.execute(
                    """
                        INSERT INTO users(first_name, last_name, phone_number, user_id)
                        VALUES(?, ?, ?, ?)
                    """,
                    spreadsheet_record_first_name,
                    spreadsheet_record_last_name,
                    contact.phone_number,
                    contact.user_id
                )
                bot.send_message(
                    chat_id=chat_id,
                    text='You have been registered'
                )

            self.__db.execute(  # refresh user data
                """
                    UPDATE users
                    SET 
                        phone_number = ?,
                        when_authorized = datetime('now')
                    WHERE users.user_id = ?
                """,
                spreadsheet_record_phone_number,
                chat_id
            )

            bot.send_message(
                chat_id=chat_id,
                text=f'Received Contact: {contact}',
            )
            bot.send_message(
                chat_id=chat_id,
                text=self.main_menu_message(),
                reply_markup=self.main_menu_keyboard()
            )
            self.main_menu_handler(bot, update)

            raise DispatcherHandlerStop


    def day_offs_menu_handler(self, bot, update):
        query = update.callback_query
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=self.main_menu_message(),
            reply_markup=self.day_offs_menu_keyboard()
        )

    def day_offs_mine_handler(self, bot, update):
        query = update.callback_query

        personal_day_offs_count = 0
        text = f'You have {personal_day_offs_count} day-offs left'

        bot.answer_callback_query(callback_query_id=query.id, text=text, show_alert=True)

    @send_typing_action
    def day_offs_paid_handler(self, bot, update):
        query = update.callback_query

        this_year_day_offs = env.paid_day_offs
        text = '*Paid day-offs:*\n' + '\n'.join(
            [f'{holiday} - {this_year_day_offs[holiday]}' for holiday in this_year_day_offs]
        )

        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(build_menu(buttons=[self.get_main_menu_button()], n_cols=1))
        )

    def salary_handler(self, bot, update):
        query = update.callback_query
        bot.answer_callback_query(callback_query_id=query.id, text="0", show_alert=True)

    def currency_handler(self, bot, update):
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

    @send_typing_action
    def about_us_handler(self, bot, update):
        bot.send_photo(
            chat_id=update.callback_query.message.chat_id,
            caption=self.get_about_info(),
            photo=open('../assets/logo.png', 'rb'),
            reply_markup=InlineKeyboardMarkup(build_menu(buttons=[self.get_website_link_button()], n_cols=1))
        )

    def main_menu_message(self):
        return 'Choose an option:'

    @send_typing_action
    def text_message_handler(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="Direct messaging doesn't work yet")

    def main_menu_keyboard(self):
        keyboard = [
            InlineKeyboardButton(self.get_emoji('palm_tree') + ' Day-offs', callback_data='day_offs_menu'),
            InlineKeyboardButton(self.get_emoji('euro_banknote') + ' Salary', callback_data='salary'),
            InlineKeyboardButton(self.get_emoji('chart_upwards') + ' Currency', callback_data='currency'),
            InlineKeyboardButton(self.get_emoji('about') + ' About us', callback_data='about_us'),
        ]
        return InlineKeyboardMarkup(build_menu(buttons=keyboard, n_cols=1))

    def day_offs_menu_keyboard(self):
        keyboard = [
            InlineKeyboardButton(self.get_emoji('airplane') + ' My day-offs', callback_data='day_offs_mine'),
            InlineKeyboardButton(self.get_emoji('snowman') + ' Paid day-offs', callback_data='day_offs_paid'),
        ]
        return InlineKeyboardMarkup(build_menu(buttons=keyboard, footer_buttons=[self.get_main_menu_button()], n_cols=2))

    def get_main_menu_button(self):
        return InlineKeyboardButton(self.get_emoji('back') + ' Main menu', callback_data='main')

    def get_website_link_button(self):
        return InlineKeyboardButton('Website', url=self.get_about_website())

    def get_handlers(self):
        return [
            MessageHandler(Filters.text, self.text_message_handler),
            CommandHandler('start', self.start_handler),
            # CallbackQueryHandler(authenticate, pattern='authenticate'),
            MessageHandler(Filters.contact, self.authenticate_handler),

            CallbackQueryHandler(self.main_menu_handler, pattern='main'),
            CallbackQueryHandler(self.day_offs_menu_handler, pattern='day_offs_menu'),
            CallbackQueryHandler(self.day_offs_mine_handler, pattern='day_offs_mine'),
            CallbackQueryHandler(self.day_offs_paid_handler, pattern='day_offs_paid'),
            CallbackQueryHandler(self.salary_handler, pattern='salary'),
            CallbackQueryHandler(self.currency_handler, pattern='currency'),
            CallbackQueryHandler(self.about_us_handler, pattern='about_us')
        ]

    def idle(self):
        # Начинаем поиск обновлений
        self.__updater.start_polling(clean=True)
        # Останавливаем бота, если были нажаты Ctrl + C
        self.__updater.idle()
