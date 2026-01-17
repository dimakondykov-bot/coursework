import pytest
import json
from src.services import analyze_profitable_cashback_categories


@pytest.fixture
def sample_cashback_transactions():
	"""Фикстура для тестов кешбэка."""
	return [
		{"Дата платежа": "15.01.2024", "Категория": "Еда", "Бонусы (включая кэшбэк)": 10},
		{"Дата платежа": "20.01.2024", "Категория": "Еда", "Бонусы (включая кэшбэк)": 5},
		{"Дата платежа": "05.01.2024", "Категория": "Топливо", "Бонусы (включая кэшбэк)": 7},
		{"Дата платежа": "02.02.2024", "Категория": "Еда", "Бонусы (включая кэшбэк)": 100},
	]


@pytest.fixture
def sample_investment_transactions():
	"""Фикстура для тестов инвестиций."""
	return [
		{"Дата платежа": "05.01.2024", "Сумма операции": -1712},
		{"Дата платежа": "10.01.2024", "Сумма операции": -50},
		{"Дата платежа": "20.01.2024", "Сумма операции": -100.0},
		{"Дата платежа": "01.02.2024", "Сумма операции": -200},
	]


@pytest.fixture
def sample_search_transactions():
	"""Фикстура для тестов поиска."""
	return [
		{"Описание": "Оплата в магазине", "Категория": "Еда"},
		{"Описание": "Оплата мобильной связи", "Категория": "Связь"},
	]


def test_analyze_profitable_cashback_categories_basic(sample_cashback_transactions):
	"""Тест анализа кешбэка по категориям."""
	res = analyze_profitable_cashback_categories(sample_cashback_transactions, 2024, 1)
	assert isinstance(res, dict)
	assert res.get('Еда') == 15
	assert res.get('Топливо') == 7


@pytest.mark.parametrize("transactions,year,month,expected_category,expected_value", [
	([
		{"Дата операции": "2024-03-10", "Категория": "Сервисы", "Кэшбэк": "12.5"},
		{"Дата платежа": "11.03.2024", "Категория": "Сервисы", "Бонусы (включая кэшбэк)": "3,5"},
		{"Дата": None, "Категория": "Сервисы", "Бонусы (включая кэшбэк)": 4},
		{"Дата платежа": "01.04.2024", "Категория": "Сервисы", "Бонусы (включая кэшбэк)": 100},
	], 2024, 3, 'Сервисы', 16.0),
])
def test_analyze_profitable_cashback_categories_various_formats(transactions, year, month, expected_category, expected_value):
	"""Параметризованный тест анализа кешбэка с различными форматами."""
	res = analyze_profitable_cashback_categories(transactions, year, month)
	assert abs(res.get(expected_category) - expected_value) < 1e-6


def test_investment_bank_basic(sample_investment_transactions):
	"""Тест расчета инвестиционной копилки."""
	# Шаг округления 50: 1712 -> 1750 (38), 50 -> 50 (0), 100 -> 100 (0)
	from src.services import investment_bank
	res = investment_bank('2024-01', sample_investment_transactions, 50)
	assert abs(res - 38.0) < 1e-6


@pytest.mark.parametrize("transactions,month,limit,expected", [
	([
		{"Дата операции": "2024-03-01", "Amount": '-99.5'},
		{"Дата операции": "2024-03-02", "Сумма": '30,2'},
		{"Дата операции": "2024-03-03", "Сумма операции": -10},
	], '2024-03', 10, 10.3),  # limit 10: 99.5 -> 100 (0.5), 30.2 -> 40 (9.8), 10 -> 10 (0)
])
def test_investment_bank_various_formats(transactions, month, limit, expected):
	"""Параметризованный тест инвестиционной копилки с различными форматами."""
	from src.services import investment_bank
	res = investment_bank(month, transactions, limit)
	assert abs(res - expected) < 1e-6


@pytest.mark.parametrize("query,expected_count,expected_category", [
	('мобильной', 1, 'Связь'),
	('магазине', 1, 'Еда'),
	('несуществующий', 0, None),
])
def test_simple_search(sample_search_transactions, query, expected_count, expected_category):
	"""Параметризованный тест простого поиска."""
	from src.services import simple_search
	json_str = simple_search(query, sample_search_transactions)
	assert isinstance(json_str, str)
	data = json.loads(json_str)
	assert data['count'] == expected_count
	if expected_category:
		assert len(data['results']) > 0
		assert data['results'][0]['Категория'] == expected_category


@pytest.fixture
def sample_phone_transactions():
	"""Фикстура для тестов поиска телефонов."""
	return [
		{"Описание": "Оплата +7 921 11-22-33"},
		{"Описание": "Оплата без номера"},
		{"Описание": "Оплата 8 (812) 123-45-67"},
	]


@pytest.mark.parametrize("description,should_match", [
	("Оплата +7 921 11-22-33", True),
	("Оплата без номера", False),
	("Оплата 8 (812) 123-45-67", True),
	("Оплата +7-999-888-77-66", True),
])
def test_search_phone_numbers(description, should_match):
	"""Параметризованный тест поиска телефонных номеров."""
	from src.services import search_phone_numbers
	transactions = [{"Описание": description}]
	json_str = search_phone_numbers(transactions)
	assert isinstance(json_str, str)
	data = json.loads(json_str)
	if should_match:
		assert data['count'] == 1
	else:
		assert data['count'] == 0


def test_search_phone_numbers_with_fixture(sample_phone_transactions):
	"""Тест поиска телефонов с фикстурой."""
	from src.services import search_phone_numbers
	json_str = search_phone_numbers(sample_phone_transactions)
	assert isinstance(json_str, str)
	data = json.loads(json_str)
	assert 'results' in data
	assert 'count' in data
	assert data['count'] >= 1


@pytest.fixture
def sample_transfer_transactions():
	"""Фикстура для тестов поиска переводов."""
	return [
		{"Категория": "Переводы", "Описание": "Валерий А."},
		{"Категория": "Переводы", "Описание": "Магазин"},
		{"Категория": "Переводы", "Описание": "Иван П."},
	]


@pytest.mark.parametrize("description,should_match", [
	("Валерий А.", True),
	("Магазин", False),
	("Иван П.", True),
	("Обычная транзакция", False),
])
def test_search_person_transfers(description, should_match):
	"""Параметризованный тест поиска переводов физлицам."""
	from src.services import search_person_transfers
	transactions = [{"Категория": "Переводы", "Описание": description}]
	json_str = search_person_transfers(transactions)
	assert isinstance(json_str, str)
	data = json.loads(json_str)
	if should_match:
		assert data['count'] == 1
		assert data['results'][0]['Описание'] == description
	else:
		assert data['count'] == 0


def test_search_person_transfers_with_fixture(sample_transfer_transactions):
	"""Тест поиска переводов с фикстурой."""
	from src.services import search_person_transfers
	json_str = search_person_transfers(sample_transfer_transactions)
	assert isinstance(json_str, str)
	data = json.loads(json_str)
	assert 'results' in data
	assert 'count' in data
	assert data['count'] >= 1

