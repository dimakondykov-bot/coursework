import json
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional

import requests

from src.utils import parse_amount

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def greeting_by_time(dt: datetime) -> str:
    """Возвращает приветствие в зависимости от времени суток."""
    h = dt.hour
    if 5 <= h < 12:
        return 'Доброе утро'
    if 12 <= h < 18:
        return 'Добрый день'
    if 18 <= h < 23:
        return 'Добрый вечер'
    return 'Доброй ночи'


def _parse_tx_date(s: Any) -> Optional[date]:
    """Парсит дату из строки."""
    if not s:
        return None
    s = str(s).strip()
    formats = ['%d.%m.%Y %H:%M:%S', '%d.%m.%Y', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    return None


def transactions_in_month_range(transactions: List[Dict[str, Any]], dt: datetime) -> List[Dict[str, Any]]:
    """Фильтрует транзакции за месяц до указанной даты."""
    start = date(dt.year, dt.month, 1)
    end = dt.date()
    out = []
    for tx in transactions:
        d = _parse_tx_date(
            tx.get('Дата платежа') or
            tx.get('Дата операции') or
            tx.get('Дата')
        )
        if not d:
            continue
        if start <= d <= end:
            out.append(tx)
    logger.debug('Отфильтрованные транзакции %d по диапазону %s - %s', len(out), start, end)
    return out


def aggregate_by_card(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Группирует транзакции по картам."""
    grouped: Dict[str, float] = {}
    for tx in transactions:
        card = str(tx.get('Номер карты') or '').strip()
        last = card[-4:] if len(card) >= 4 else card or 'unknown'
        amt = parse_amount(
            tx.get('Сумма операции') or
            tx.get('Сумма') or
            tx.get('Сумма платежа')
        )
        if amt is None:
            continue
        grouped[last] = grouped.get(last, 0.0) + abs(amt)

    cards = []
    for last, total in grouped.items():
        cashback = round(total / 100.0, 2)
        cards.append({
            'last_digits': last,
            'total_spent': round(total, 2),
            'cashback': cashback
        })
    return cards


def top_transactions(transactions: List[Dict[str, Any]], n: int = 5) -> List[Dict[str, Any]]:
    """Возвращает топ n транзакций по сумме."""
    items = []
    for tx in transactions:
        amt = parse_amount(
            tx.get('Сумма операции') or
            tx.get('Сумма') or
            tx.get('Сумма платежа')
        )
        if amt is None:
            continue
        d = _parse_tx_date(
            tx.get('Дата платежа') or
            tx.get('Дата операции') or
            tx.get('Дата')
        )
        items.append({
            'date': d.strftime('%d.%m.%Y') if d else None,
            'amount': amt,
            'category': tx.get('Категория'),
            'description': tx.get('Описание')
        })
    items.sort(key=lambda x: abs(x['amount']), reverse=True)
    return items[:n]


def get_currency_rates(currencies: List[str]) -> List[Dict[str, Any]]:
    """Получает курсы валют через API."""
    if not currencies:
        return []
    try:
        symbols = ','.join(currencies)
        url = f'https://api.exchangerate.host/latest?base=RUB&symbols={symbols}'
        r = requests.get(url, timeout=5)
        data = r.json()
        rates = data.get('rates', {})
        result = []
        for c in currencies:
            rate = rates.get(c)
            result.append({
                'currency': c,
                'rate': float(rate) if rate is not None else None
            })
        return result
    except Exception as e:
        logger.error('Не удалось получить курсы валют.: %s', e)
        return []


def get_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    """Получает цены акций через API."""
    if not stocks:
        return []
    try:
        symbols = ','.join(stocks)
        url = f'https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbols}'
        r = requests.get(url, timeout=5)
        data = r.json()
        results = data.get('quoteResponse', {}).get('result', [])
        out = []
        for s in stocks:
            found = next((x for x in results if x.get('symbol') == s), None)
            price = found.get('regularMarketPrice') if found else None
            out.append({'stock': s, 'price': float(price) if price is not None else None})
        return out
    except Exception as e:
        logger.error('Не удалось получить цены акций: %s', e)
        return []


def generate_main_page_json(
    dt_str: str,
    transactions: List[Dict[str, Any]],
    user_settings_path: str = 'user_settings.json'
) -> Dict[str, Any]:
    """Генерирует JSON для главной страницы."""
    try:
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    except Exception:
        raise ValueError("Параметр dt_str должен быть в формате 'YYYY-MM-DD HH:MM:SS'.")

    tx_range = transactions_in_month_range(transactions, dt)
    cards = aggregate_by_card(tx_range)
    top = top_transactions(tx_range, n=5)

    try:
        with open(user_settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except Exception:
        settings = {}

    currencies = settings.get('user_currencies', [])
    stocks = settings.get('user_stocks', [])

    currency_rates = get_currency_rates(currencies)
    stock_prices = get_stock_prices(stocks)

    return {
        'greeting': greeting_by_time(dt),
        'cards': cards,
        'top_transactions': top,
        'currency_rates': currency_rates,
        'stock_prices': stock_prices,
    }
