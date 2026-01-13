from typing import List, Dict, Optional, Any
import math
import re
import json

from src.utils import parse_year_month, parse_amount


def analyze_profitable_cashback_categories(
    transactions: List[Dict],
    year: int,
    month: int,
) -> Dict[str, float]:
    """Агрегировать сумму кешбэка по категориям за указанный год и месяц."""
    totals: Dict[str, float] = {}

    for tx in transactions:
        date_val = (tx.get('Дата платежа') or
                    tx.get('Дата операции') or
                    tx.get('Дата'))
        ym = parse_year_month(date_val)
        if not ym:
            continue
        y, m = ym
        if y != year or m != month:
            continue

        category = tx.get('Категория') or tx.get('category') or 'Без категории'
        cashback_val = (tx.get('Бонусы (включая кэшбэк)') or
                        tx.get('Кэшбэк') or
                        tx.get('cashback') or
                        None)
        cb = parse_amount(cashback_val) or 0.0
        totals[category] = totals.get(category, 0.0) + cb

    return totals


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """Вычислить сумму, которую можно отложить в Инвесткопилку."""
    if not isinstance(limit, (int, float)) or limit <= 0:
        raise ValueError('limit must be positive')

    try:
        target_year, target_month = map(int, month.split('-'))
    except Exception:
        raise ValueError("month must be in 'YYYY-MM' format")

    def get_amount_from_tx(tx: Dict[str, Any]) -> Optional[float]:
        keys = ('Сумма операции', 'Сумма', 'Amount', 'Сумма операции, руб.')
        for key in keys:
            if key in tx:
                v = parse_amount(tx[key])
                if v is not None:
                    return v
        return None

    savings = []
    for tx in transactions:
        date_val = (tx.get('Дата платежа') or
                    tx.get('Дата операции') or
                    tx.get('Дата'))
        ym = parse_year_month(date_val)
        if not ym:
            continue
        y, m = ym
        if y != target_year or m != target_month:
            continue

        amt = get_amount_from_tx(tx)
        if amt is None:
            continue

        expense = abs(amt)
        if expense == 0:
            continue

        rounded = math.ceil(expense / limit) * limit
        invest = rounded - expense
        if invest > 0:
            savings.append(invest)

    total = float(sum(savings))
    return round(total, 2)


def simple_search(query: str, transactions: List[Dict[str, Any]]) -> str:
    """Простой поиск по полям 'Описание' и 'Категория'. Возвращает JSON-строку."""
    q = str(query).casefold()
    out = []
    for tx in transactions:
        desc = str(
            tx.get('Описание') or
            tx.get('description') or
            ''
        ).casefold()
        cat = str(
            tx.get('Категория') or
            tx.get('category') or
            ''
        ).casefold()
        if q in desc or q in cat:
            out.append(tx)
    
    data = {
        'query': query,
        'results': out,
        'count': len(out)
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def search_phone_numbers(transactions: List[Dict[str, Any]]) -> str:
    """Найти транзакции, в описании которых есть мобильный номер. Возвращает JSON-строку."""
    pattern = r"(?:\+7|8)?[\s-]*\(?\d{3}\)?[\s-]*\d{1,3}[\s-]*\d{2}[\s-]*\d{2}"
    phone_re = re.compile(pattern)
    out = []
    for tx in transactions:
        desc = str(
            tx.get('Описание') or
            tx.get('description') or
            ''
        )
        if phone_re.search(desc):
            out.append(tx)
    
    data = {
        'results': out,
        'count': len(out)
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def search_person_transfers(transactions: List[Dict[str, Any]]) -> str:
    """Найти переводы физлицам. Возвращает JSON-строку."""
    name_re = re.compile(r'\b[А-ЯЁA-Z][а-яёa-z]+\s+[А-ЯЁA-Z]\.')
    out = []
    for tx in transactions:
        cat = tx.get('Категория') or tx.get('category') or ''
        desc = str(
            tx.get('Описание') or
            tx.get('description') or
            ''
        )
        if str(cat).lower() == 'переводы' and name_re.search(desc):
            out.append(tx)
    
    data = {
        'results': out,
        'count': len(out)
    }
    return json.dumps(data, ensure_ascii=False, indent=2)
