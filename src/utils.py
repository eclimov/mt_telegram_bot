import datetime
import requests
from bs4 import BeautifulSoup


def get_exchange_rate(currency_code: int, date: datetime):
    r = requests.get(f'http://www.bnm.md/md/official_exchange_rates?get_xml=1&date={date.strftime("%d.%m.%Y")}')
    exchange_rate = BeautifulSoup(r.text, 'lxml').find_all(
        'valute', {
            'id': str(currency_code)
        }
    )[0].value.text
    return exchange_rate
