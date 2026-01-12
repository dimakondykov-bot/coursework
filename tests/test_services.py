from src.services import analyze_profitable_cashback_categories


def test_analyze_profitable_cashback_categories_basic():
	transactions = [
		{"Дата платежа": "15.01.2024", "Категория": "Еда", "Бонусы (включая кэшбэк)": 10},
		{"Дата платежа": "20.01.2024", "Категория": "Еда", "Бонусы (включая кэшбэк)": 5},
		{"Дата платежа": "05.01.2024", "Категория": "Топливо", "Бонусы (включая кэшбэк)": 7},
		{"Дата платежа": "02.02.2024", "Категория": "Еда", "Бонусы (включая кэшбэк)": 100},
	]

	res = analyze_profitable_cashback_categories(transactions, 2024, 1)
	assert isinstance(res, dict)
	assert res.get('Еда') == 15
	assert res.get('Топливо') == 7


def test_analyze_profitable_cashback_categories_various_formats():
	transactions = [
		{"Дата операции": "2024-03-10", "Категория": "Сервисы", "Кэшбэк": "12.5"},
		{"Дата платежа": "11.03.2024", "Категория": "Сервисы", "Бонусы (включая кэшбэк)": "3,5"},
		{"Дата": None, "Категория": "Сервисы", "Бонусы (включая кэшбэк)": 4},
		{"Дата платежа": "01.04.2024", "Категория": "Сервисы", "Бонусы (включая кэшбэк)": 100},
	]

	res = analyze_profitable_cashback_categories(transactions, 2024, 3)
	assert abs(res.get('Сервисы') - 16.0) < 1e-6


def test_investment_bank_basic():
	transactions = [
		{"Дата платежа": "05.01.2024", "Сумма операции": -1712},
		{"Дата платежа": "10.01.2024", "Сумма операции": -50},
		{"Дата платежа": "20.01.2024", "Сумма операции": -100.0},
		{"Дата платежа": "01.02.2024", "Сумма операции": -200},
	]

	# Шаг округления 50: 1712 -> 1750 (38), 50 -> 50 (0), 100 -> 100 (0)
	res = __import__('src.services', fromlist=['']).investment_bank('2024-01', transactions, 50)
	assert abs(res - 38.0) < 1e-6


def test_investment_bank_various_formats():
	transactions = [
		{"Дата операции": "2024-03-01", "Amount": '-99.5'},
		{"Дата операции": "2024-03-02", "Сумма": '30,2'},
		{"Дата операции": "2024-03-03", "Сумма операции": -10},
	]

	# limit 10: 99.5 -> 100 (0.5), 30.2 -> 40 (9.8), 10 -> 10 (0)
	res = __import__('src.services', fromlist=['']).investment_bank('2024-03', transactions, 10)
	assert abs(res - (0.5 + 9.8)) < 1e-6


def test_simple_search():
	transactions = [
		{"Описание": "Оплата в магазине", "Категория": "Еда"},
		{"Описание": "Оплата мобильной связи", "Категория": "Связь"},
	]
	res = __import__('src.services', fromlist=['']).simple_search('мобильной', transactions)
	assert len(res) == 1
	assert res[0]['Категория'] == 'Связь'


def test_search_phone_numbers():
	transactions = [
		{"Описание": "Оплата +7 921 11-22-33"},
		{"Описание": "Оплата без номера"},
	]
	res = __import__('src.services', fromlist=['']).search_phone_numbers(transactions)
	assert len(res) == 1


def test_search_person_transfers():
	transactions = [
		{"Категория": "Переводы", "Описание": "Валерий А."},
		{"Категория": "Переводы", "Описание": "Магазин"},
	]
	res = __import__('src.services', fromlist=['']).search_person_transfers(transactions)
	assert len(res) == 1
	assert res[0]['Описание'] == 'Валерий А.'

