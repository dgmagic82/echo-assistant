"""PEf05: budget and monetization for "Echo" on measured RAG tokens. Writes the xlsx with live formulas and prints the same numbers.

Based on zerocoder-pef04/budget.py. Main scenario: RAG + Haiku 4.5 + prompt cache (measured 20.11.2026)."""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

OUT = Path(__file__).resolve().parent.parent / "submission" / "Эхо_бюджет_и_монетизация.xlsx"

# ---------------- inputs ----------------
A = {  # key: (label, value, unit, source)
    "users": ("Активные пользователи (сотрудники поддержки)", 3, "чел.", "ТЗ 3.1"),
    "req_day": ("Запросов на пользователя в день", 30, "шт.", "40–60 отзывов/день + вопросы и сводки, ТЗ 1.1"),
    "days": ("Рабочих дней в месяце", 22, "дн.", "шаблон урока"),
    "tin_full": ("PEf04: токенов на входе, вся база в промпте", 9464, "ток.", "замер PEf03: промпт + 10 документов"),
    "tout_full": ("PEf04: токенов на выходе", 324, "ток.", "замер PEf03"),
    "tin": ("RAG: токенов на входе на запрос", 10417, "ток.", "замер PEf05, прогон 2: промпт, 4 документа целиком, 6 фрагментов, схема ответа"),
    "tout": ("RAG: токенов на выходе на запрос", 277, "ток.", "замер PEf05, прогон 2"),
    "tin_c": ("RAG с кэшем: токенов на входе на запрос", 10733, "ток.", "замер PEf05, прогон 5 (промпт v2.3, кэш), 20.11.2026"),
    "cached": ("Из них читается из кэша", 8933, "ток.", "тот же замер: промпт, документы 04, 07, 08, 09 и схема ответа"),
    "tout_c": ("RAG с кэшем: токенов на выходе", 287, "ток.", "тот же замер"),
    "writes_day": ("Записей кэша в рабочий день", 4, "шт.", "кэш живёт 1 ч и продлевается каждым запросом; 4 перерыва дольше часа, с запасом"),
    "k_read": ("Чтение кэша, доля цены входа", 0.1, "доля", "тарифы Anthropic prompt caching"),
    "k_write": ("Запись кэша на 1 ч, доля цены входа", 2.0, "доля", "то же"),
    "p_in": ("Haiku 4.5: вход", 1.00, "$ за 1 млн", "openrouter.ai/api/v1/models, 19.11.2026"),
    "p_out": ("Haiku 4.5: выход", 5.00, "$ за 1 млн", "то же"),
    "p55_in": ("Haiku 5.5: вход", 0.10, "$ за 1 млн", "openrouter.ai, 19.11.2026; на эталоне не проверена"),
    "p55_out": ("Haiku 5.5: выход", 0.50, "$ за 1 млн", "то же"),
    "fx": ("Курс доллара", 90, "₽ за $", "допущение"),
    "fee": ("Комиссия пополнения OpenRouter", 0.055, "доля", "допущение по условиям OpenRouter"),
    "vps": ("VPS для боевой версии (Telegram-бот)", 300, "₽/мес", "демо на Streamlit Cloud бесплатно"),
    "rate": ("Ставка разработчика", 1500, "₽/ч", "допущение: фриланс no-code"),
    "support_h": ("Поддержка после запуска", 4, "ч/мес", "правка базы, промпта, мониторинг"),
    "buffer": ("Буфер", 0.30, "доля", "30%: сезон ноябрь–декабрь до 150 отзывов/день"),
    "saved_h": ("Экономия времени поддержки", 2, "ч в день", "ТЗ 2.2: с 3 ч до 1 ч"),
    "hour_cost": ("Стоимость часа сотрудника поддержки", 470, "₽/ч", "60 000 ₽ оклад + 30% взносов / 168 ч"),
}
DEV = [  # MVP labour, hours
    ("База знаний: 16 документов, очистка, разметка", 10),
    ("Промпт v2, эталон 15 входов, 4 прогона, кэш", 10),
    ("RAG: индекс FAISS, поиск, ответ по схеме, тесты", 12),
    ("Интерфейс Streamlit и выкладка демо", 8),
    ("Telegram-бот для боевой версии", 8),
    ("Пилот 2 недели с поддержкой, правки", 10),
    ("Инструкция для сотрудников", 4),
]
S = {  # SaaS inputs
    "price": ("Цена тарифа для магазина", 7990, "₽/мес", "≈ 40% от экономии клиента"),
    "setup": ("Подключение (разово)", 5000, "₽", "загрузка базы магазина, 3 ч работы"),
    "onboard_h": ("Часы на подключение клиента", 3, "ч", ""),
    "acq": ("Комиссия эквайринга", 0.03, "доля", "допущение"),
    "sup_client_h": ("Поддержка одного клиента", 1, "ч/мес", ""),
    "cac": ("Привлечение клиента (CAC)", 10000, "₽", "Авито, демо, созвоны; допущение"),
    "fixed_vps": ("Сервер для всех клиентов", 1000, "₽/мес", "VPS побольше"),
    "fixed_h": ("Развитие продукта и общая поддержка", 12, "ч/мес", ""),
    "saas_dev_h": ("Доработка MVP в мультиклиентский сервис", 40, "ч", "отдельные базы, биллинг, кабинет"),
    "growth": ("Новых клиентов в месяц (со 2-го месяца)", 2, "шт.", "допущение"),
}

wb = Workbook()
bold = Font(bold=True)
head = PatternFill("solid", fgColor="E5E7EB")
inp = PatternFill("solid", fgColor="FEF3C7")


def sheet_header(ws, title, widths):
    ws.append([title])
    ws["A1"].font = Font(bold=True, size=13)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


# ---- sheet 1: inputs ----
ws = wb.active
ws.title = "Допущения"
sheet_header(ws, "Допущения (жёлтые ячейки можно менять, остальные листы пересчитаются)", [52, 12, 14, 60])
ws.append(["Параметр", "Значение", "Ед.", "Откуда"])
for c in ws[2]:
    c.font, c.fill = bold, head
ref = {}
for k, (label, v, unit, src) in list(A.items()) + list(S.items()):
    ws.append([label, v, unit, src])
    r = ws.max_row
    ws.cell(r, 2).fill = inp
    if unit == "доля":
        ws.cell(r, 2).number_format = "0.0%"
    ref[k] = f"Допущения!$B${r}"
ws.append([])
ws.append(["Трудозатраты MVP", "часов"])
ws.cell(ws.max_row, 1).font = bold
dev_first = ws.max_row + 1
for name, h in DEV:
    ws.append([name, h])
    ws.cell(ws.max_row, 2).fill = inp
dev_last = ws.max_row
ws.append(["Итого часов", f"=SUM(B{dev_first}:B{dev_last})"])
ws.cell(ws.max_row, 1).font = bold
ref["dev_h"] = f"Допущения!$B${ws.max_row}"

# ---- sheet 2: MVP budget for one store ----
b = wb.create_sheet("Бюджет MVP")
sheet_header(b, "Бюджет MVP для одного магазина («Лавка Тепла»), основной вариант: RAG, Haiku 4.5 с кэшем (столбец D)",
             [58, 16, 16, 16, 16])
b.append(["Показатель", "PEf04: вся база", "RAG, Haiku 4.5", "RAG, Haiku 4.5 + кэш", "RAG, Haiku 5.5"])
for c in b[2]:
    c.font, c.fill = bold, head
R = ref
W = f"({R['writes_day']}/({R['users']}*{R['req_day']}))"  # share of requests that write the cache
COLS = "BCDE"


def each(tpl: str) -> list[str]:
    """The same formula for every scenario column; {c} is the column letter."""
    return [tpl.format(c=c) for c in COLS]


rows = [
    ("Запросов в месяц", f"={R['users']}*{R['req_day']}*{R['days']}", "=B3", "=B3", "=B3"),
    ("Стоимость запроса (в среднем за месяц), $",
     f"=({R['tin_full']}*{R['p_in']}+{R['tout_full']}*{R['p_out']})/1000000",
     f"=({R['tin']}*{R['p_in']}+{R['tout']}*{R['p_out']})/1000000",
     f"=(({R['tin_c']}-{R['cached']})*{R['p_in']}+{R['tout_c']}*{R['p_out']})/1000000"
     f"+{R['cached']}*{R['p_in']}/1000000*((1-{W})*{R['k_read']}+{W}*{R['k_write']})",
     f"=({R['tin']}*{R['p55_in']}+{R['tout']}*{R['p55_out']})/1000000"),
    ("API в месяц, $", *each("={c}3*{c}4")),
    ("API в месяц с комиссией, ₽", *each(f"={{c}}5*{R['fx']}*(1+{R['fee']})")),
    ("Инфраструктура (VPS для бота; демо и Telegram бесплатно), ₽/мес", *each(f"={R['vps']}")),
    ("Поддержка, ₽/мес", *each(f"={R['support_h']}*{R['rate']}")),
    ("Итого в месяц, ₽", *each("={c}6+{c}7+{c}8")),
    ("Итого в месяц с буфером, ₽", *each(f"={{c}}9*(1+{R['buffer']})")),
    ("Разработка MVP (разово), ₽", *each(f"={R['dev_h']}*{R['rate']}")),
    ("Бюджет первого года с буфером, ₽", *each(f"=({{c}}11+12*{{c}}9)*(1+{R['buffer']})")),
    ("", None, None, None, None),
    ("Экономия магазина, ₽/мес", f"={R['saved_h']}*{R['days']}*{R['hour_cost']}", "=B14", "=B14", "=B14"),
    ("Чистый эффект в месяц (экономия − расходы с буфером), ₽", *each("={c}14-{c}10")),
    ("Окупаемость разработки, мес", *each(f"={{c}}11*(1+{R['buffer']})/{{c}}15")),
]
for label, *fs in rows:
    b.append([label, *fs])
for r in range(3, b.max_row + 1):
    for c in range(2, 6):
        cell = b.cell(r, c)
        cell.number_format = "0.0000" if r == 4 else ("#,##0.00" if r == 5 else ("0.0" if r == 16 else "#,##0"))
for r in (9, 10, 12, 15, 16):
    b.cell(r, 1).font = bold

# ---- sheet 3: SaaS ----
s = wb.create_sheet("Монетизация SaaS")
sheet_header(s, "B2B SaaS для небольших магазинов: юнит-экономика и выход в плюс", [52] + [11] * 13)
s.append(["Юнит-экономика одного клиента", "₽/мес"])
for c in s[2]:
    c.font, c.fill = bold, head
unit = [
    ("Цена тарифа", f"={R['price']}"),
    ("API на клиента (RAG, Haiku 4.5 + кэш)", "='Бюджет MVP'!D6"),
    ("Эквайринг", f"={R['price']}*{R['acq']}"),
    ("Поддержка клиента", f"={R['sup_client_h']}*{R['rate']}"),
    ("Маржинальный доход с клиента", "=B3-B4-B5-B6"),
    ("Постоянные расходы сервиса", f"={R['fixed_vps']}+{R['fixed_h']}*{R['rate']}"),
    ("Точка безубыточности, клиентов", "=ROUNDUP(B8/B7,0)"),
    ("Инвестиции до запуска (MVP + доработка, с буфером)", f"=({R['dev_h']}+{R['saas_dev_h']})*{R['rate']}*(1+{R['buffer']})"),
    ("Экономия клиента в месяц", "='Бюджет MVP'!B14"),
    ("Окупаемость для клиента (экономия / цена), раз", "=B11/B3"),
]
for label, f in unit:
    s.append([label, f])
    s.cell(s.max_row, 2).number_format = "0.0" if "раз" in label else "#,##0"
for r in (7, 9, 10):
    s.cell(r, 1).font = bold

s.append([])
s.append(["Помесячный план, первый год"] + [f"М{m}" for m in range(1, 13)])
hr = s.max_row
for c in s[hr]:
    c.font, c.fill = bold, head
lines = ["Новых клиентов", "Клиентов на конец месяца", "Выручка (подписка + подключения)",
         "Переменные расходы", "Постоянные расходы", "Привлечение и подключение", "Результат месяца",
         "Нарастающий итог (с инвестициями)"]
for i, name in enumerate(lines):
    s.append([name])
r0 = hr + 1
for m in range(1, 13):
    col = get_column_letter(m + 1)
    prev = get_column_letter(m)
    s[f"{col}{r0}"] = 1 if m == 1 else f"={R['growth']}"  # M1: pilot store
    s[f"{col}{r0+1}"] = f"={col}{r0}" if m == 1 else f"={prev}{r0+1}+{col}{r0}"
    s[f"{col}{r0+2}"] = f"={col}{r0+1}*$B$3+{col}{r0}*{R['setup']}"
    s[f"{col}{r0+3}"] = f"={col}{r0+1}*($B$4+$B$5+$B$6)"
    s[f"{col}{r0+4}"] = "=$B$8"
    s[f"{col}{r0+5}"] = f"={col}{r0}*({R['cac']}+{R['onboard_h']}*{R['rate']})"
    s[f"{col}{r0+6}"] = f"={col}{r0+2}-{col}{r0+3}-{col}{r0+4}-{col}{r0+5}"
    s[f"{col}{r0+7}"] = f"=-$B$10+{col}{r0+6}" if m == 1 else f"={prev}{r0+7}+{col}{r0+6}"
    for k in range(2, 8):
        s[f"{col}{r0+k}"].number_format = "#,##0"
s.cell(r0 + 7, 1).font = bold
s.append([])
s.append(["Месяц выхода в плюс по нарастающему итогу",
          f'=IFERROR(MATCH(TRUE,INDEX(B{r0+7}:M{r0+7}>=0,0),0),"позже 12 мес")'])
s.cell(s.max_row, 1).font = bold
s.append(["Первый месяц с положительным результатом",
          f'=IFERROR(MATCH(TRUE,INDEX(B{r0+6}:M{r0+6}>=0,0),0),"позже 12 мес")'])
s.cell(s.max_row, 1).font = bold
for ws_ in (b, s, ws):
    for row in ws_.iter_rows():
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
wb.save(OUT)

# ---------------- same numbers in Python (to report and to cross-check the sheet) ----------------
v = {k: x[1] for k, x in list(A.items()) + list(S.items())}
dev_h = sum(h for _, h in DEV)
q = v["users"] * v["req_day"] * v["days"]
per_req = (v["tin"] * v["p_in"] + v["tout"] * v["p_out"]) / 1e6
api_usd = {
    "full": q * (v["tin_full"] * v["p_in"] + v["tout_full"] * v["p_out"]) / 1e6,
    "rag": q * per_req,
    "cache": None,
    "h55": q * (v["tin"] * v["p55_in"] + v["tout"] * v["p55_out"]) / 1e6,
}
writes = v["writes_day"] * v["days"]
base_c = ((v["tin_c"] - v["cached"]) * v["p_in"] + v["tout_c"] * v["p_out"]) / 1e6
read_req = base_c + v["cached"] * v["p_in"] * v["k_read"] / 1e6
write_req = base_c + v["cached"] * v["p_in"] * v["k_write"] / 1e6
api_usd["cache"] = (q - writes) * read_req + writes * write_req
print(f"cache: read request ${read_req:.4f}, write request ${write_req:.4f}, {writes} writes/month")
support = v["support_h"] * v["rate"]
dev = dev_h * v["rate"]
saving = v["saved_h"] * v["days"] * v["hour_cost"]
print(f"requests/month {q}, per request ${per_req:.4f}, dev {dev_h} h = {dev:,.0f}")
mvp = {}
for k, usd in api_usd.items():
    rub = usd * v["fx"] * (1 + v["fee"])
    month = rub + v["vps"] + support
    year = (dev + 12 * month) * (1 + v["buffer"])
    net = saving - month * (1 + v["buffer"])
    mvp[k] = rub
    print(f"{k:8} API ${usd:6.2f} = {rub:7,.0f} ₽ | month {month:8,.0f} | +buf {month*(1+v['buffer']):8,.0f} | "
          f"year {year:10,.0f} | net {net:8,.0f} | payback {dev*(1+v['buffer'])/net:4.1f} mo")
print(f"saving per store {saving:,.0f} ₽/mo")
contrib = v["price"] - mvp["cache"] - v["price"] * v["acq"] - v["sup_client_h"] * v["rate"]
fixed = v["fixed_vps"] + v["fixed_h"] * v["rate"]
inv = (dev_h + v["saas_dev_h"]) * v["rate"] * (1 + v["buffer"])
print(f"SaaS: contribution {contrib:,.0f}, fixed {fixed:,.0f}, break-even {-(-fixed // contrib):.0f} clients, invest {inv:,.0f}")
cum, clients, first_pos, payback = -inv, 0, None, None
for m in range(1, 13):
    new = 1 if m == 1 else v["growth"]
    clients += new
    res = (clients * v["price"] + new * v["setup"]
           - clients * (mvp["cache"] + v["price"] * v["acq"] + v["sup_client_h"] * v["rate"])
           - fixed - new * (v["cac"] + v["onboard_h"] * v["rate"]))
    cum += res
    first_pos = first_pos or (m if res >= 0 else None)
    payback = payback or (m if cum >= 0 else None)
    print(f"M{m:2} clients {clients:2} result {res:8,.0f} cum {cum:9,.0f}")
print("first positive month", first_pos, "payback month", payback)
