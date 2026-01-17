import pytest
import pandas as pd
from src.reports import spending_by_category, monthly_summary, category_breakdown, top_merchants


@pytest.fixture
def sample_dataframe():
    """Фикстура для генерации тестового DataFrame."""
    return pd.DataFrame([
        {'Дата платежа': '2025-01-05', 'Сумма операции': '-100.50', 'Категория': 'Еда', 'Описание': 'Кафе А'},
        {'Дата платежа': '2025-01-10', 'Сумма операции': '200', 'Категория': 'Зарплата', 'Описание': 'Перевод от работы'},
        {'Дата платежа': '2025-01-15', 'Сумма операции': '-50', 'Категория': 'Транспорт', 'Описание': 'Метро'},
        {'Дата платежа': '2025-02-01', 'Сумма операции': '-300', 'Категория': 'Еда', 'Описание': 'Ресторан'},
        {'Дата платежа': None, 'Сумма операции': '-20', 'Категория': 'Еда', 'Описание': 'Без даты'},
    ])


@pytest.fixture
def sample_transactions():
    """Фикстура для генерации тестовых транзакций."""
    return [
        {'Дата платежа': '15.01.2024', 'Сумма операции': -100.50, 'Категория': 'Еда', 'Описание': 'Кафе'},
        {'Дата платежа': '20.01.2024', 'Сумма операции': 2000, 'Категория': 'Зарплата', 'Описание': 'Зарплата'},
        {'Дата платежа': '25.01.2024', 'Сумма операции': -50, 'Категория': 'Транспорт', 'Описание': 'Метро'},
        {'Дата платежа': '01.02.2024', 'Сумма операции': -300, 'Категория': 'Еда', 'Описание': 'Ресторан'},
    ]


@pytest.mark.parametrize("category,date,expected_count", [
    ('Еда', '2025-02-15', 2),
    ('Транспорт', '2025-02-15', 1),
    ('Зарплата', '2025-02-15', 1),
])
def test_spending_by_category(sample_dataframe, category, date, expected_count):
    """Параметризованный тест трат по категориям."""
    res = spending_by_category(sample_dataframe, category, date=date)
    assert len(res) == expected_count
    assert all(res['Категория'] == category)
    assert '_amount' in res.columns


def test_monthly_summary(sample_transactions):
    """Тест сводки за месяц."""
    res = monthly_summary(sample_transactions, 2024, 1)
    assert 'income' in res
    assert 'expense' in res
    assert 'net' in res
    assert 'by_category' in res
    assert isinstance(res['income'], (int, float))
    assert isinstance(res['expense'], (int, float))


def test_category_breakdown(sample_transactions):
    """Тест распределения по категориям."""
    res = category_breakdown(sample_transactions, 2024, 1)
    assert isinstance(res, dict)
    assert 'Еда' in res or 'Транспорт' in res


def test_top_merchants(sample_transactions):
    """Тест топ получателей."""
    res = top_merchants(sample_transactions, 2024, 1, n=5)
    assert isinstance(res, list)
    assert len(res) <= 5
    if res:
        assert 'merchant' in res[0]
        assert 'total' in res[0]
