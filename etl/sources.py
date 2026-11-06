"""Реестр источников: имя -> URL архива. Все — открытые данные «Если быть точным» (CC BY 4.0)."""

TOCHNO = "https://storage.yandexcloud.net/tochno-st-catalog"
BDMO = f"{TOCHNO}/Rosstat/data_bdmo_118_v20260928/indicators"

SOURCES = {
    # магистральная матрица 180 городов: авто / ЖД / авиа
    "intercity": f"{TOCHNO}/Geo/data_intercity_connectivity_162_v20260629/data_intercity_connectivity_162_v20260629_parquet.zip",
    # все н.п. РФ: население (перепись 2021), координаты, ОКТМО
    "settlements": f"{TOCHNO}/Rosstat/data_settlements_156_v20260925/data_allsettlements_anon_156_v20260925_parquet.zip",
    # БД ПМО — выбранные показатели
    "bdmo_no_regular_transport": f"{BDMO}/section41/data_Y48155002_112_v20260928.zip",  # доля населения без регулярного сообщения с адм. центром
    "bdmo_roads_substandard": f"{BDMO}/section41/data_Y48106005_112_v20260928.zip",     # доля местных дорог вне нормативов
    "bdmo_roads_length": f"{BDMO}/section6/data_Y48006005_112_v20260928.zip",           # протяжённость местных дорог
    "bdmo_budget_income": f"{BDMO}/section13/data_Y48013001_112_v20260928.zip",         # доходы местного бюджета
    "bdmo_budget_spend": f"{BDMO}/section13/data_Y48013002_112_v20260928.zip",          # расходы местного бюджета
}
