import os
import re
from typing import Any, Optional, Tuple, List, Dict
from datetime import datetime

import pandas as pd


def extract_from_xlsx(path_to_file: str) -> List[Dict[str, Any]]:
    """Чтение XLSX файла в список словарей."""
    if not os.path.exists(path_to_file):
        raise FileNotFoundError(f"Файл не найден: {path_to_file}")

    if not os.path.isfile(path_to_file):
        raise ValueError(f'это не файл {path_to_file}')

    try:
        df = pd.read_excel(path_to_file)
    except Exception as e:
        raise RuntimeError(f"Ошибка при чтении Excel: {e}")

    if df.empty:
        return []

    data: List[Dict[str, Any]] = df.to_dict('records')
    for row in data:
        for key, value in list(row.items()):
            if pd.isna(value):
                row[key] = None
    return data


def parse_year_month(date_str: Any) -> Optional[Tuple[int, int]]:
    """Попробовать распарсить строку даты и вернуть (year, month) или None."""
    if not date_str:
        return None
    s = str(date_str).strip()
    if ' ' in s and '.' in s:
        s = s.split(' ')[0]

    formats = [
        '%d.%m.%Y',
        '%d.%m.%Y %H:%M:%S',
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m',
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.year, dt.month
        except ValueError:
            pass

    try:
        if '.' in s:
            parts = s.split('.')
            if len(parts) >= 3:
                year = parts[2].split()[0]
                return int(year), int(parts[1])
        if '-' in s:
            parts = s.split('T')[0].split('-')
            if len(parts) >= 2:
                return int(parts[0]), int(parts[1])
    except Exception:
        return None

    return None


def parse_amount(value: Any) -> Optional[float]:
    """Преобразовать строковое/числовое представление суммы в float."""
    if value is None:
        return None
    s = str(value).strip()
    if s == '':
        return None

    s = s.replace('\xa0', '').replace(' ', '')

    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()

    s = s.replace(',', '.')

    cleaned = re.sub(r'[^0-9.\-]', '', s)
    if cleaned in ('', '.', '-', '-.'):
        return None

    try:
        val = float(cleaned)
    except ValueError:
        m = re.search(r'-?\d+(?:\.\d+)?', cleaned)
        if not m:
            return None
        try:
            val = float(m.group(0))
        except ValueError:
            return None

    if negative:
        val = -abs(val)

    return val
