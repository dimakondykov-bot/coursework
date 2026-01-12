# Financial Assistant

Простой помощник для анализа банковских операций из Excel файлов.

## Что делает

- Анализирует транзакции из Excel файла
- Считает кешбэк по категориям
- Рассчитывает сумму для инвестиционной копилки
- Генерирует отчёты по месяцам
- Получает курсы валют и цены акций

## Установка

```bash
poetry install
```

## Запуск

```bash
poetry run python main.py
```

Программа попросит:
1. Ввести месяц в формате `YYYY-MM` (или нажать Enter для последнего месяца)
2. Ввести лимит округления для копилки (по умолчанию 50)
3. Сгенерировать отчёты (y/N)

## Структура проекта

- `main.py` - точка входа программы
- `src/utils.py` - чтение Excel и парсинг данных
- `src/services.py` - анализ кешбэка и инвесткопилка
- `src/reports.py` - генерация отчётов
- `src/views.py` - функции для веб-страниц
- `data/operations.xlsx` - файл с транзакциями

## Примеры использования

### Анализ кешбэка
```python
import src.services as services
result = services.analyze_profitable_cashback_categories(operations, 2025, 1)
```

### Инвесткопилка
```python
invest_sum = services.investment_bank("2025-01", operations, limit=50)
```

### Отчёты
```python
import src.reports as reports
summary = reports.monthly_summary(operations, 2025, 1)
```

## Требования

- Python 3.11+
- pandas
- openpyxl
- requests

## Тесты

```bash
poetry run pytest -q
```

