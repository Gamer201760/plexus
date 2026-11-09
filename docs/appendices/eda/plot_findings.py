import collections
import csv
import json
import pathlib
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


OUT = pathlib.Path(__file__).resolve().parent
ROOT = OUT.parents[1]
FIGURES = OUT / 'figures'
PALETTE = dict(re.findall(r'--([\w-]+):\s*(#[0-9a-fA-F]+)', (ROOT / 'frontend/src/shared/styles/tokens/palette.css').read_text()))
ACCENT = PALETTE['accent-500']
GREY = PALETTE['neutral-300']
TEXT = PALETTE['neutral-900']
MUTED = PALETTE['neutral-600']
GRID = PALETTE['neutral-100']
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'text.color': TEXT,
                     'axes.labelcolor': MUTED, 'xtick.color': MUTED, 'ytick.color': TEXT,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.spines.left': False, 'axes.spines.bottom': False})


def rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def save(fig, name):
    for suffix in ['png', 'svg']:
        fig.savefig(FIGURES / f'{name}.{suffix}', dpi=170, facecolor='white')
    plt.close(fig)


def modal_coverage():
    data = json.loads((OUT / 'graph/results/summary.json').read_text())['modes']
    names = [('road', 'Автомобиль'), ('rail', 'Железная дорога'), ('air', 'Авиация')]
    values = [100 * data[key]['observed'] / data[key]['rows'] for key, _ in names]
    fig, ax = plt.subplots(figsize=(10.5, 4.7))
    fig.subplots_adjust(left=.24, right=.94, top=.77, bottom=.29)
    ax.barh([name for _, name in names], values, color=[GREY, GREY, ACCENT], height=.55)
    ax.invert_yaxis()
    ax.set_xlim(0, 105)
    ax.set_xticks([0, 25, 50, 75, 100], ['0%', '25%', '50%', '75%', '100%'])
    ax.grid(axis='x', color=GRID)
    ax.set_axisbelow(True)
    for i, value in enumerate(values):
        ax.text(value+1, i, f'{value:.1f}%', va='center', color=TEXT, fontweight='bold')
    fig.suptitle('В авиационном слое заполнена лишь пятая часть пар', x=.04, y=.94, ha='left', fontsize=16, fontweight='bold')
    fig.text(.04, .075, '32 220 пар на режим; заполнено = найдено моделью Точно.\nЭто не расписание. Пропуск не подтверждает отсутствие транспортной связи.', fontsize=10, color=MUTED)
    save(fig, 'modal_coverage')


def representation():
    data = sorted(rows(OUT / 'region_sample_coverage.csv'), key=lambda row: float(row['sample_population_share_pct']))
    selected = data[:10] + data[-5:]
    values = [float(row['sample_population_share_pct']) for row in selected]
    labels = [f"{row['region'].replace('Республика ', 'Респ. ')} · {row['sample_cities']} гор." for row in selected]
    fig, ax = plt.subplots(figsize=(12, 8.7))
    fig.subplots_adjust(left=.43, right=.92, top=.83, bottom=.16)
    ax.barh(labels, values, height=.64, color=[ACCENT]+[GREY]*(len(selected)-1))
    ax.invert_yaxis()
    ax.set_xlim(0, 110)
    ax.set_xticks([0, 25, 50, 75, 100], ['0%', '25%', '50%', '75%', '100%'])
    ax.grid(axis='x', color=GRID)
    ax.set_axisbelow(True)
    ax.tick_params(axis='y', labelsize=9.5)
    for i, value in enumerate(values):
        ax.text(value+1, i, f'{value:.1f}%', va='center', fontsize=10)
    fig.suptitle('180 городов представляют регионы очень неравномерно', x=.04, y=.96, ha='left', fontsize=17, fontweight='bold')
    fig.text(.04, .90, 'Доля жителей выбранных городов в населении своего региона по переписи 2021\nПоказаны 10 наименьших и 5 наибольших долей; это не индекс связанности.', color=MUTED, fontsize=11)
    fig.text(.04, .06, 'Вся городская выборка: 77,4 млн жителей, 52,6% населения РФ в файле переписи.\n48 из 85 региональных меток представлены одним городом; Московская область — 22 городами.', color=MUTED, fontsize=10)
    save(fig, 'region_representation')


def municipal_coverage():
    data = rows(OUT / 'territories/municipal-paired-completeness.csv')
    by_year = collections.defaultdict(lambda: [0, 0])
    for row in data:
        if row['mun_level'] != 'Муниципальное образование верхнего уровня':
            continue
        year = int(row['year'])
        if 2015 <= year <= 2025:
            by_year[year][0] += int(row['observed_union'])
            by_year[year][1] += int(row['paired_valid'])
    years = sorted(by_year)
    union = [by_year[year][0] for year in years]
    pairs = [by_year[year][1] for year in years]
    fig, ax = plt.subplots(figsize=(10.5, 5.7))
    fig.subplots_adjust(left=.09, right=.94, top=.79, bottom=.25)
    ax.plot(years, union, color=GREY, linewidth=2)
    ax.plot(years, pairs, color=ACCENT, linewidth=2.7, marker='o', markersize=4)
    ax.set_ylim(0, max(union)*1.15)
    ax.set_xticks(years)
    ax.grid(axis='y', color=GRID)
    ax.set_axisbelow(True)
    ax.text(2020, max(union)*1.02, 'Есть хотя бы один показатель', color=MUTED, fontsize=10)
    ax.text(2015, pairs[0]+110, 'Есть оба показателя', color=ACCENT, fontsize=10)
    for year in [2023, 2024, 2025]:
        value = by_year[year][1]
        ax.annotate(f'{value:,}'.replace(',', ' '), (year, value), xytext=(0, 12), textcoords='offset points', ha='center', color=ACCENT, fontsize=11, fontweight='bold')
    fig.suptitle('За 2025 год совместных данных пока слишком мало', x=.04, y=.95, ha='left', fontsize=17, fontweight='bold')
    fig.text(.04, .87, 'Муниципалитеты верхнего уровня: дороги и население без регулярного сообщения', fontsize=11, color=MUTED)
    fig.text(.04, .065, 'Это опубликованные коды с валидными значениями, а не перечень всех МО страны.\nОтсутствующую запись нельзя считать нулевым дефицитом. Срез 2024: 1 455 пар.', fontsize=10, color=MUTED)
    save(fig, 'municipal_joint_coverage')


if __name__ == '__main__':
    FIGURES.mkdir(exist_ok=True)
    modal_coverage()
    representation()
    municipal_coverage()
