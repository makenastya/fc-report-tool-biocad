
import numpy as np
import pandas as pd
import jinja2
from pathlib import Path
import os, sys

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)

def table_FACS(data: pd.DataFrame, populations):
    temp = data.copy()
    columns = {}  # словарь соответсвий для замены названий колонок
    actual = {}
    actual['Experiment Name'] = 'Experiment Name'
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
    data.rename(columns=columns, inplace=True)
    temp = remove_control(temp, 'Tube Name:', 'rep')
    for i in names:
        temp[i] = temp[i].astype('int')
    return([temp, data])

def process_tables(cytometer, populations, test, testcv, testmin, min_events, points):
    #print('Первичные данные', data, sep = '\n')
    cur_file = Path(__file__)
    data_path = cur_file.parent.parent / 'data'
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
                print(table)
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
    primary= pd.concat(data, ignore_index=True)
    msg = ''
    for i in file_lot:
        if len(file_lot[i]) > 1:
            s = ''
            for j in file_lot[i]:
                s += '\n' + j
            msg += f'Одинаковые образцы {i}: {s}' + '\n'

    if msg != '':
        raise ValueError(msg)
    compute(res, testcv, testmin, min_events, points, test,primary)

def biotable(temp, points): #таблица учета биообразцов, принимает исходную таблицу(без контроля и названия эксперимента) и кол-во точек забора
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

def comp_cv(df, child, parent): #принимает датафрейм от одного образца, названия столбцов для расчета cv, возвращает cv
    data = df.copy()
    data[child] = data[child] / data[parent] * 100
    mean = data[child].mean()
    sd = data[child].std()
    return(sd / mean * 100)

def remove_control(df, column, rep):#убирает из таблицы строки с контролем
    df = df.loc[df[column].str.contains(rep)]
    return(df)
def find_col(df, name, fl):#возвращает столбец в таблице критериев пригодности, принимает таблицу крит.приг., название популяции и критерия
    for i in df.columns:
        if (name in i) and (fl in i):
            return(i)
def check(number: int, oper: str, ref: int):#принимает значение(cv либо events), оператор, возвращает результат сравнения
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

def krit(df : pd.DataFrame, testcv, min_events): #собирает таблицу из всех критериев пригодности(cv и min events), принимает исходную таблицу и словари с критериями
    s = []
    s.append('ЛОТ')
    s.append('Точка PD')
    for i in min_events:
        c = 'min ' + i
        s.append(c)
    for i in testcv:
        c = '%CV ' + i + ' in ' + testcv[i][0]
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
        for j in testcv:
            cv = comp_cv(i[1], j, testcv[j][0])
            col = find_col(table, j, '%CV')
            table.loc[(int(lot_pd[0]), int(lot_pd[1])), col] = cv
            res_krit.loc[(int(lot_pd[0]), int(lot_pd[1])), col] = check(cv, testcv[j][1], testcv[j][2])
        for j in min_events:
            col = find_col(table, j, 'min')
            table.loc[(int(lot_pd[0]), int(lot_pd[1])), col] = i[1][j].min()
            res_krit.loc[(int(lot_pd[0]), int(lot_pd[1])), col] = check(i[1][j].min(), 'min events', min_events[j])
    return(table, res_krit)

def compute(temp, testcv, testmin, min_events, points, test, primary): #запускает все функции подсчета таблиц и генерирует excel-файлы
    temp = temp.sort_values(by = 'Sample ID:')
    biodata = {}
    krit_data = {}
    table = biotable(temp, points)
    biodata['Учет биообразцов'] = table
    for i in test:
        table = comp_percentgb(temp, i, test[i], testmin[i], points)
        key = f'Mean % {i} in {test[i]}'
        krit_data[key] = table
    table = krit(temp, testcv, min_events)
    df = table[0]
    df1 = table[1]
    df.sort_index(inplace=True)
    df1.sort_index(inplace=True)
    df = table[0].reset_index()
    df1 = table[1].reset_index()

    krit_data['Критерии пригодности'] = [df, df1]
    for i in biodata:
        biodata[i].to_excel(f'{i}.xlsx')
    primary.to_excel('Первичные данные.xlsx', index=False)
    for i in krit_data:
        style_df = (
            krit_data[i][1] == 0
        ).replace({
            True: 'color:red',
            False: ''
        })
        if i != 'Критерии пригодности':
            krit_data[i][0].style.apply(lambda _: style_df, axis = None).to_excel(f'{i}.xlsx', engine='openpyxl')
        else:
            krit_data[i][0].style.apply(lambda _: style_df, axis=None).to_excel(f'{i}.xlsx', engine='openpyxl', index=False)

def comp_percentgb(df : pd.DataFrame, child, parent, krit: list, points): #считает процент дочерних клеток в родительских, принимает критерии lloq и применяет их
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
        table.loc[int(lot_pd[0]), PD] = i[1][child].mean()
        res_krit.loc[int(lot_pd[0]), PD]  = check(i[1][child].mean(), krit[1], krit[2])
    return(table, res_krit)
