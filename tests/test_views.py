import json
import pytest
from unittest.mock import patch, Mock
from datetime import datetime

import src.views as views


@pytest.fixture
def sample_transactions():
    """Фикстура для генерации тестовых транзакций."""
    return [
        {"Дата платежа": "01.12.2021", "Номер карты": "*7197", "Сумма операции": -160.89, "Категория": "Супермаркеты", "Описание": "Колхоз"},
        {"Дата платежа": "05.12.2021", "Номер карты": "*7197", "Сумма операции": -64.00, "Категория": "Супермаркеты", "Описание": "Колхоз"},
        {"Дата платежа": "10.12.2021", "Номер карты": "*5091", "Сумма операции": -7.07, "Категория": "Каршеринг", "Описание": "Ситидрайв"},
        {"Дата платежа": "15.12.2021", "Номер карты": "*4556", "Сумма операции": 5046.00, "Категория": "Пополнения", "Описание": "Пополнение"},
    ]


@pytest.fixture
def sample_datetime():
    """Фикстура для генерации тестовой даты."""
    return datetime.strptime('2021-12-20 12:00:00', '%Y-%m-%d %H:%M:%S')


@pytest.mark.parametrize("hour,expected", [
    (6, 'Доброе утро'),
    (13, 'Добрый день'),
    (19, 'Добрый вечер'),
    (2, 'Доброй ночи'),
])
def test_greeting_by_time(hour, expected):
    """Параметризованный тест для приветствия по времени суток."""
    assert views.greeting_by_time(datetime(2021, 1, 1, hour, 0, 0)) == expected


def test_transactions_in_month_range_and_aggregate(sample_transactions, sample_datetime):
    """Тест фильтрации транзакций и агрегации по картам."""
    filtered = views.transactions_in_month_range(sample_transactions, sample_datetime)
    assert len(filtered) == 4

    cards = views.aggregate_by_card(filtered)
    # проверяем наличие карт и сумм
    card_map = {c['last_digits']: c for c in cards}
    assert '*7197'[-4:] in card_map
    assert card_map['7197']['total_spent'] == round(160.89 + 64.0, 2)


@patch('src.views.requests.get')
def test_get_currency_and_stock_prices(mock_get):
    # mock currency API
    mock_resp_currency = Mock()
    mock_resp_currency.json.return_value = {'rates': {'USD': 73.21, 'EUR': 87.08}}

    # mock stock API (Yahoo-like)
    mock_resp_stock = Mock()
    mock_resp_stock.json.return_value = {'quoteResponse': {'result': [{'symbol': 'AAPL', 'regularMarketPrice': 150.12}, {'symbol': 'AMZN', 'regularMarketPrice': 3173.18}]}} 

    mock_get.side_effect = [mock_resp_currency, mock_resp_stock]

    currencies = ['USD', 'EUR']
    stocks = ['AAPL', 'AMZN']

    rates = views.get_currency_rates(currencies)
    assert rates[0]['currency'] == 'USD' and rates[0]['rate'] == 73.21

    prices = views.get_stock_prices(stocks)
    assert prices[0]['stock'] == 'AAPL' and prices[0]['price'] == 150.12


@patch('src.views.requests.get')
def test_generate_main_page_json_integration(mock_get, sample_transactions):
    """Тест генерации JSON для главной страницы."""
    mock_resp_currency = Mock()
    mock_resp_currency.json.return_value = {'rates': {'USD': 73.21}}
    mock_resp_stock = Mock()
    mock_resp_stock.json.return_value = {'quoteResponse': {'result': [{'symbol': 'AAPL', 'regularMarketPrice': 150.12}]}}
    mock_get.side_effect = [mock_resp_currency, mock_resp_stock]

    json_str = views.generate_main_page_json('2021-12-20 12:00:00', sample_transactions, user_settings_path='user_settings.json')
    assert isinstance(json_str, str)
    
    out = json.loads(json_str)
    assert out['greeting'] in ('Доброе утро', 'Добрый день', 'Добрый вечер', 'Доброй ночи')
    assert isinstance(out['cards'], list)
    assert isinstance(out['top_transactions'], list)
    assert isinstance(out['currency_rates'], list)
    assert isinstance(out['stock_prices'], list)


def test_generate_events_page_json(sample_transactions):
    """Тест генерации JSON для страницы События."""
    json_str = views.generate_events_page_json(sample_transactions, limit=10)
    assert isinstance(json_str, str)
    
    data = json.loads(json_str)
    assert 'events' in data
    assert 'total' in data
    assert isinstance(data['events'], list)
    assert len(data['events']) <= 10
