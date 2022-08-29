
import numpy as np
import pandas as pd
import jinja2
from pathlib import Path
import os, sys
import datetime
from datetime import datetime


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)

def table_FACS(data: pd.DataFrame, populations):
    """Принимает таблицу с исходными данными из config.yaml, возвращает обработанную таблицу с нужными столбцами и их названиями для прибора FACS Canto II.
    :param data: таблица, прочитанная из входного вайла
    :type data: pd.Dataframe
    """
    temp = data.copy()
    columns = {}  # словарь соответсвий для замены названий колонок
    actual = {}
    actual['Experiment Name'] = 'Experiment Name'
    actual['Specimen Name'] = 'Specimen Name'
    actual['Tube Name'] = 'Tube Name'
    actual['Record Date'] = 'Record Date'
    columns['Tube Name'] = 'Tube Name:'
    columns['Specimen Name'] = 'Sample ID:'
    names = []
    for i in populations:
        names.append(populations[i])
        key = i + ' #Events'
        columns[key] = populations[i]
        actual[key] = populations[i]
    for i in columns:
        if i not in temp.columns:
            return ([pd.DataFrame(), data])
    temp = temp.loc[:, list(columns.keys())]
    data = data.loc[:, list(actual.keys())]
    temp.rename(columns=columns, inplace=True)
    temp = remove_control(temp, 'Tube Name:', 'rep')
    for i in names:
        temp[i] = temp[i].astype('int')
    return([temp, data])

def table_FLEX(data, populations):
    """Принимает таблицу с исходными данными из config.yaml, возвращает обработанную таблицу с нужными столбцами и их названиями для прибора cytoFLEX.
        :param data: таблица, прочитанная из входного вайла
        :type data: pd.Dataframe
    """
    temp = data.copy()
    columns = {}  # словарь соответсвий для замены названий колонок
    columns['Tube Name:'] = 'Tube Name:'
    columns['Sample ID:'] = 'Sample ID:'
    names = []
    for i in populations:
        names.append(populations[i])
        key = i + ' Events'
        columns[key] = populations[i]
    for i in columns:
        if i not in temp.columns:
            return([pd.DataFrame(), data])
    temp = temp.loc[:, list(columns.keys())]
    data = data.loc[:, list(columns.keys())]
    temp.rename(columns=columns, inplace=True)
    temp = remove_control(temp, 'Tube Name:', 'rep')
    for i in names:
        temp[i] = temp[i].astype('int')
    return([temp, data])

def process_tables(data_path, out_path, cytometer, populations, percent, cv, lloq, min_events, points, round_key):
    """Принимает данные из config.yaml, возвращает обработанные и склеенные таблицы.
    :param data_path: путь до папки с исходными данными
    :type data_path: Path
    :param out_path: путь до папки с обработанными данными
    :type out_path: Path
    :param cytometer: название прибора
    :type cytometer: str
    :param populations: словарь соответствий названий популяций в исходных данных и желаемых названий
    :type populations: dict
    :param percent: словарь, в каждой ячейке ключу соответствует популяция, относительно которой нужно считать процент
    :type percent: dict
    :param cv: словарь, в каждой ячейке ключу соответствует список из популяции(относительно которой считается cv), оператора, значения cv
    :type cv: dict
    :param lloq: словарь, в каждой ячейке ключу соответствует список из популяции(относительно которой считается процент), оператора, значения lloq
    :type lloq: dict
    :param min_events: минимальное количество событий(значение) для популяций(ключ)
    :type min_events: dict
    :param points: количество точек забора
    :type: int
    """

    dirs = os.listdir(data_path)
    k = 0
    file_lot = {}
    data = []
    for file in dirs:
        if file.endswith(".csv"):
            k += 1
            p = Path(data_path, file)
            if cytometer == 'FACS Canto II':
                fl = pd.read_csv(p, sep = ',', nrows=0)
                head = " ".join(fl.columns)
                if ';' in head:
                    table = pd.read_csv(p, sep=';')
                else:
                    table = pd.read_csv(p, sep=',')
                tpl = table_FACS(table, populations)
            else:
                table = pd.read_csv(p, sep=';', skiprows=2)
                tpl = table_FLEX(table, populations)
                name = pd.read_csv(p, sep = ';', nrows=0)
                head = " ".join(name.columns)

            temp = tpl[0]
            table = tpl[1]
            if temp.empty:
                raise ValueError(f'Неверное название столбца:{file}')
            s = set(temp['Sample ID:'])
            for i in s:
                if i not in file_lot:
                    file_lot[i] = []
                file_lot[i].append(file)
            if k == 1:
                res = temp
            else:
                res = pd.concat([res, temp])
            if cytometer == 'FACS Canto II':
                empty = pd.DataFrame(columns=table.columns, data=[[None] * len(table.columns)])
                table = pd.concat([empty, table], axis=0)
            else:
                empty = pd.DataFrame(columns=table.columns, data=[[None] * len(table.columns)])
                empty['Tube Name:'] = head
                table = pd.concat([empty, table], axis=0)
            data.append(table)
    primary = pd.concat(data, ignore_index=True)
    msg = ''
    for i in file_lot:
        if len(file_lot[i]) > 1:
            s = ''
            for j in file_lot[i]:
                s += '\n' + j
            msg += f'Одинаковые образцы {i}: {s}' + '\n'
    if msg != '':
        raise ValueError(msg)

    current_time = datetime.now()
    timestamp = current_time.strftime('%Y-%m-%d_%H-%M-%S')
    file = f'Output_{timestamp}'
    out_path = Path(out_path, file)
    os.mkdir(out_path)
    p = Path(out_path, f'Первичные данные.xlsx')
    primary.to_excel(p, index=False)
    p = Path(out_path, 'log.txt')
    text = open(p, "w+")
    text.write(f'Количество прочитанных файлов: {k} \n')
    for file in dirs:
        if file.endswith(".csv"):
            text.write(f'{file} \n')
    print(f'Количество прочитанных файлов: {k} \n')
    compute(out_path, res, cv, lloq, min_events, points, percent, round_key)

def biotable(temp, points):
    """Принимает исходную таблицу данных(без контроля, названия экспепримента и с нужными столбцами) и кол-во точек забора, возвращает таблицу учета биообразцов.
    :param temp: таблица данных (без контроля, названия экспепримента и с обработанными названиями столбцов)
    :type temp: pd.Dataframe
    :param points: количество точек забора
    :type points:int
    """
    s = []
    for i in range(1, points + 1):
        c = 'PD-' + str(i)
        s.append(c)
    table = pd.DataFrame(columns = s)
    table.index.name = 'ЛОТ'
    for i in range(len(temp)):
        id = temp['Sample ID:'].iloc[i]
        lot_pd = id.split('-')
        PD = 'PD-' + lot_pd[1]
        table.loc[int(lot_pd[0]), PD] = '+'
    return(table)

def comp_cv(df, child, parent):
    """Принимает датафрейм от одного образца, названия столбцов для расчета cv, возвращает cv.
    :param df: датафрейм с одним образцом
    :type df: pd.Dataframe
    :param child: название популяции, для которой считается cv
    :type child: str
    :param parent: название популяции, относительно которой считается cv
    :type parent: str
    """
    data = df.copy()
    data[child] = data[child] / data[parent] * 100
    mean = data[child].mean()
    sd = data[child].std()
    if mean == 0 or sd == 0:
        return(None)
    return(sd / mean * 100)

def remove_control(df, column, rep):
    """Принимает датафрейм, возвращает датафрейм без строк с контролем"""
    df = df.loc[df[column].str.contains(rep)]
    return(df)
def find_col(df, name, fl):
    """Принимает таблицу критериев пригодности, название популяции и критерия, возвращает соответствующий столбец в таблице критериев пригодности.
    :param df: таблица с критериями пригодности
    :type df: pd.Dataframe
    :param name: Название популяции
    :type name: str
    :param fl: Название критерия в таблице критериев пригодности(%CV или min)
    :type fl: str
    """
    for i in df.columns:
        if (name in i) and (fl in i):
            return(i)
def check(number: int, oper: str, ref: int):
    """Принимает значение(cv либо events), оператор, возвращает результат сравнения."""
    if oper == 'no more than':
        if number > ref:
            return(0)
        else:
            return(1)
    if oper == 'not less than':
        if number < ref:
            return(0)
        else:
            return(1)
    if oper == 'min events':
        if number < ref:
            return(0)
        else:
            return(1)

def krit(df : pd.DataFrame, cv, min_events, round_key):
    """Принимает исходную таблицу и словари с критериями пригодности, собирает таблицу из всех критериев пригодности(cv и min events).
    :param df: таблица с данными
    :type df: pd.Dataframe
    :param cv: Словарь для проверки критерия пригодности CV
    :type cv: dict
    :param min_events: Словарь для проверки критерия пригодности - минимальное количество событий
    :type min_events: dict
    """
    s = []
    s.append('ЛОТ')
    s.append('Точка PD')
    for i in min_events:
        c = 'min ' + i
        s.append(c)
    for i in cv:
        c = '%CV ' + i + ' in ' + cv[i][0]
        s.append(c)
    table = pd.DataFrame(columns = s)
    res_krit = pd.DataFrame(columns = s)
    group = df.groupby('Sample ID:')
    list_group = list(group)
    table = table.set_index(['ЛОТ', 'Точка PD'])
    res_krit = res_krit.set_index(['ЛОТ', 'Точка PD'])
    for i in list_group:
        lot_pd = i[0].split('-')
        PD = 'PD-' + lot_pd[1]
        for j in cv:
            val = comp_cv(i[1], j, cv[j][0])
            col = find_col(table, j, '%CV')
            if val != None:
                if round_key:
                    if val < 10:
                        table.loc[(int(lot_pd[0]), int(lot_pd[1])), col] = round(val, 3)
                    else:
                        table.loc[(int(lot_pd[0]), int(lot_pd[1])), col] = round(val, 2)
                else:
                    table.loc[(int(lot_pd[0]), int(lot_pd[1])), col] = val
                res_krit.loc[(int(lot_pd[0]), int(lot_pd[1])), col] = check(val, cv[j][1], cv[j][2])
            else:
                table.loc[(int(lot_pd[0]), int(lot_pd[1])), col] = val
        for j in min_events:
            col = find_col(table, j, 'min')
            if round_key:
                if i[1][j].min() < 10:
                    table.loc[(int(lot_pd[0]), int(lot_pd[1])), col] = round(i[1][j].min(), 3)
                else:
                    table.loc[(int(lot_pd[0]), int(lot_pd[1])), col] = round(i[1][j].min(), 2)
            else:
                table.loc[(int(lot_pd[0]), int(lot_pd[1])), col] = i[1][j].min()
            res_krit.loc[(int(lot_pd[0]), int(lot_pd[1])), col] = check(i[1][j].min(), 'min events', min_events[j])
    return(table, res_krit)

def compute(out_path, temp, cv, lloq, min_events, points, percent, round_key):
    """Принимает обработанные входные данные из process_tables, запускает все функции подсчета таблиц и генерирует excel-файлы(см.описание process_tables)."""

    temp = temp.sort_values(by = 'Sample ID:')
    biodata = {}
    krit_data = {}
    table = biotable(temp, points)
    biodata['Учет биообразцов'] = table
    for i in percent:
        if i in lloq:
            table = comp_percentgb(temp, i, percent[i], lloq[i], points, round_key)
        else:
            table = comp_percentgb(temp, i, percent[i], [], points, round_key)
        key = f'Mean % {i} in {percent[i]}'
        krit_data[key] = table
    table = krit(temp, cv, min_events, round_key)
    df = table[0]
    df1 = table[1]
    df.sort_index(inplace=True)
    df1.sort_index(inplace=True)
    df = table[0].reset_index()
    df1 = table[1].reset_index()
    krit_data['Критерии пригодности'] = [df, df1]
    for i in biodata:
        styled = (biodata[i].style.applymap(lambda v: 'background-color: %s' % 'red' if v != '+' else ''))
        p = Path(out_path, f'{i}.xlsx')
        styled.to_excel(p, engine='openpyxl')
    for i in krit_data:
        style_df = (
            krit_data[i][1] == 0
        ).replace({
            True: 'color:red',
            False: ''
        })
        p = Path(out_path, f'{i}.xlsx')
        if i != 'Критерии пригодности':
            krit_data[i][0].style.apply(lambda _: style_df, axis = None).to_excel(p, engine='openpyxl')
        else:
            krit_data[i][0].style.apply(lambda _: style_df, axis=None).to_excel(p, engine='openpyxl', index=False)

    print(f'Файлы сохранены в {out_path}')
def comp_percentgb(df : pd.DataFrame, child, parent, krit: list, points, round_key):
    """Принимает таблицу с исходными данными, критерий пригодности lloq, считает процент дочерних клеток в родительских, возвращает датафрейм с посчитанными процентами и датафрейм с результатом применения критерия.
    :param df: таблица с исходными даннымиэ
    :type df: pd.Dataframe
    :param child: Популяция, для которой расчитывается процентное содержание
    :type child: str
    :param parent: Популяция, относительно которой расчитывается процентное содержание
    :type parent: str
    :param krit: Список с популяцией parent, оператором сравнения и значением lloq, пустой, если для данной популяции нет lloq
    :type krit: list
    """
    df = remove_control(df, 'Tube Name:', 'rep')
    group = df.groupby('Sample ID:')
    list_group = list(group)
    s = []
    for i in range(1, points + 1):
        c = 'PD-' + str(i)
        s.append(c)
    table = pd.DataFrame(columns = s)
    res_krit = pd.DataFrame(columns = s)
    table.index.name = 'ЛОТ'
    for i in list_group:
        i[1][child] = i[1][child] / i[1][parent] * 100
        lot_pd = i[0].split('-')
        PD = 'PD-' + lot_pd[1]
        if round_key:
            if i[1][child].mean() != None:
                if i[1][child].mean() < 10:
                    table.loc[int(lot_pd[0]), PD] = round(i[1][child].mean(), 3)
                else:
                    table.loc[int(lot_pd[0]), PD] = round(i[1][child].mean(), 2)
        else:
            table.loc[int(lot_pd[0]), PD] = i[1][child].mean()
        if len(krit) > 0:
            res_krit.loc[int(lot_pd[0]), PD]  = check(i[1][child].mean(), krit[1], krit[2])
        else:
            res_krit.loc[int(lot_pd[0]), PD] = 1
    return(table, res_krit)
