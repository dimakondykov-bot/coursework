import logging
import json
import src.utils as utils
import src.services as services
import src.reports as reports


def _choose_latest_month(operations):
    """Выбирает последний месяц из операций."""
    months = []
    for tx in operations:
        date_val = tx.get('Дата платежа') or tx.get('Дата операции') or tx.get('Дата')
        ym = utils.parse_year_month(date_val)
        if ym:
            months.append(ym)
    if not months:
        return None
    y, m = max(months)
    return f"{y}-{m:02d}"


def main():
    """Главная функция программы."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

    operations = utils.extract_from_xlsx('data/operations.xlsx')

    print("Нажмите Enter, чтобы проанализировать данные за последний найденный месяц,")
    print("или введите месяц в формате ГГГГ-ММ..")
    try:
        month = input("Month (YYYY-MM) [latest]: ").strip()
    except EOFError:
        month = ''

    try:
        msg = "Ограничение на округление для инвестиционного банка (по умолчанию 50): "
        round_limit_str = input(msg).strip()
    except EOFError:
        round_limit_str = ''

    if not month:
        month = _choose_latest_month(operations)
        if not month:
            print('В данных не найдено дат, пригодных для анализа.')
            return

    try:
        year, mon = map(int, month.split('-'))
    except Exception:
        print("Месяц должен быть в формате 'ГГГГ-ММ'.")
        return

    if not round_limit_str:
        round_limit = 50
    else:
        try:
            round_limit = int(round_limit_str)
        except Exception:
            print('Недопустимое значение округления, используется 50.')
            round_limit = 50

    print('Проведение анализа для', month)
    result = services.analyze_profitable_cashback_categories(operations, year, mon)
    print('категории кэшбэка:', result)

    invest_sum = services.investment_bank(month, operations, round_limit)
    print(f'инвестировать банк в общей сложности на {month}: {invest_sum}')

    try:
        msg = "Хотите сгенерировать текстовые отчёты для этого месяца? (y/N): "
        run_reports = input(msg).strip().lower()
    except EOFError:
        run_reports = 'n'

    if run_reports == 'y':
        try:
            summary = reports.monthly_summary(operations, year, mon)
            cat = reports.category_breakdown(operations, year, mon)
            top = reports.top_merchants(operations, year, mon, n=10)

            print('\n=== Отчёт: сводка за месяц ===')
            print(json.dumps(summary, ensure_ascii=False, indent=2))

            print('\n=== Отчёт: распределение по категориям ===')
            print(json.dumps(cat, ensure_ascii=False, indent=2))

            print('\n=== Отчёт: топ получателей/магазинов ===')
            print(json.dumps(top, ensure_ascii=False, indent=2))
        except Exception as e:
            print('Ошибка при генерации отчётов:', e)


if __name__ == '__main__':
    main()
