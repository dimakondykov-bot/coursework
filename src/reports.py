from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime
import os
import json

import pandas as pd

from src.utils import parse_year_month, parse_amount


def _default_report_filename(func_name: str) -> str:
    """Создает имя файла для отчета по умолчанию."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{func_name}_{timestamp}.json"


def _write_report_to_file(result: Any, filename: str) -> None:
    """Записывает результат отчета в файл."""
    os.makedirs('reports_output', exist_ok=True)
    filepath = os.path.join('reports_output', filename)
    
    if isinstance(result, pd.DataFrame):
        data = json.loads(result.to_json(orient='records', force_ascii=False, date_format='iso'))
    else:
        data = result
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_report(arg=None):
    """Декоратор для сохранения результатов отчетов в файл."""
    if callable(arg):
        # Использован как @save_report
        func = arg
        
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            filename = _default_report_filename(func.__name__)
            _write_report_to_file(result, filename)
            return result
        
        return wrapper
    else:
        # Использован как @save_report('filename.json')
        filename = arg
        
        def decorator(func):
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                file_to_save = filename if filename else _default_report_filename(func.__name__)
                _write_report_to_file(result, file_to_save)
                return result
            
            return wrapper
        
        return decorator


def monthly_summary(transactions: List[Dict[str, Any]], year: int, month: int) -> Dict[str, Any]:
    """Возвращает сводку за месяц."""
    income = 0.0
    expense = 0.0
    by_cat: Dict[str, float] = defaultdict(float)

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

        amt = parse_amount(
            tx.get('Сумма операции') or
            tx.get('Сумма') or
            tx.get('Сумма платежа')
        )
        if amt is None:
            continue

        if amt > 0:
            income += amt
        else:
            expense += abs(amt)

        cat = tx.get('Категория') or tx.get('category') or 'Без категории'
        by_cat[cat] += abs(amt)

    net = income - expense
    return {
        'income': round(income, 2),
        'expense': round(expense, 2),
        'net': round(net, 2),
        'by_category': dict(by_cat)
    }


def category_breakdown(transactions: List[Dict[str, Any]], year: int, month: int) -> Dict[str, float]:
    """Вернуть словарь категорий -> суммы расходов за месяц."""
    out: Dict[str, float] = defaultdict(float)
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

        amt = parse_amount(
            tx.get('Сумма операции') or
            tx.get('Сумма') or
            tx.get('Сумма платежа')
        )
        if amt is None:
            continue

        cat = tx.get('Категория') or tx.get('category') or 'Без категории'
        out[cat] += abs(amt)

    return dict(out)


def monthly_cashflow(transactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Считаем по всем месяцам cashflow."""
    out: Dict[str, Dict[str, float]] = {}
    temp: Dict[str, Dict[str, float]] = defaultdict(
        lambda: {'income': 0.0, 'expense': 0.0}
    )

    for tx in transactions:
        date_val = (tx.get('Дата платежа') or
                    tx.get('Дата операции') or
                    tx.get('Дата'))
        ym = parse_year_month(date_val)
        if not ym:
            continue
        y, m = ym
        key = f"{y}-{m:02d}"

        amt = parse_amount(
            tx.get('Сумма операции') or
            tx.get('Сумма') or
            tx.get('Сумма платежа')
        )
        if amt is None:
            continue

        if amt > 0:
            temp[key]['income'] += amt
        else:
            temp[key]['expense'] += abs(amt)

    for k, v in temp.items():
        out[k] = {'income': round(v['income'], 2), 'expense': round(v['expense'], 2)}
    return out


def top_merchants(transactions: List[Dict[str, Any]], year: int, month: int, n: int = 10) -> List[Dict[str, Any]]:
    """Найти топ n получателей по сумме расходов."""
    totals: Dict[str, float] = defaultdict(float)
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

        amt = parse_amount(
            tx.get('Сумма операции') or
            tx.get('Сумма') or
            tx.get('Сумма платежа')
        )
        if amt is None:
            continue
        if amt >= 0:
            continue

        desc = str(
            tx.get('Описание') or
            tx.get('description') or
            'Неизвестно'
        ).strip()
        totals[desc] += abs(amt)

    items = sorted(
        [{'merchant': k, 'total': round(v, 2)} for k, v in totals.items()],
        key=lambda x: x['total'],
        reverse=True
    )
    return items[:n]


def spending_by_category(
    transactions: pd.DataFrame,
    category: str,
    date: Optional[str] = None
) -> pd.DataFrame:
    """Возвращает траты по категории за последние три месяца."""
    if not isinstance(transactions, pd.DataFrame):
        raise ValueError('transactions must be a pandas DataFrame')

    date_col = None
    for c in ('Дата платежа', 'Дата операции', 'Дата'):
        if c in transactions.columns:
            date_col = c
            break
    if date_col is None:
        raise ValueError('No date column found')

    cat_col = None
    for c in ('Категория', 'category'):
        if c in transactions.columns:
            cat_col = c
            break
    if cat_col is None:
        raise ValueError('No category column found')

    amt_col = None
    for c in ('Сумма операции', 'Сумма', 'Amount', 'Сумма платежа'):
        if c in transactions.columns:
            amt_col = c
            break
    if amt_col is None:
        raise ValueError('No amount column found')

    if date is None:
        end = pd.to_datetime(datetime.now())
    else:
        end = pd.to_datetime(date)
    start = end - pd.DateOffset(months=3)

    df = transactions.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])

    df_cat = df[df[cat_col].astype(str) == str(category)].copy()

    mask = (df_cat[date_col] >= start) & (df_cat[date_col] <= end)
    res = df_cat.loc[mask].copy()

    def parse_amount_safe(v):
        return parse_amount(v) if pd.notna(v) else None

    res['_amount'] = res[amt_col].apply(parse_amount_safe)
    return res
