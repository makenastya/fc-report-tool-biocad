
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
    columns['Tube Name'] = 'Tube Name:'  # это я уже сама внутри программы делаю для удобства
    columns['Specimen Name'] = 'Sample ID:'
    names = []
    for i in populations:
        names.append(populations[i])
        key = i + ' #Events'
        columns[key] = populations[i]
        if key not in temp.columns:
            print("Неверное название колонки")

            return (pd.DataFrame())
    temp = temp.loc[:, list(columns.keys())]
    temp.rename(columns=columns, inplace=True)
    temp = remove_control(temp, 'Tube Name:', 'rep')
    for i in names:
        temp[i] = temp[i].astype('int')
    return(temp)

def table_FLEX(data, populations):
    temp = data.copy()
    columns = {}  # словарь соответсвий для замены названий колонок
    columns['Tube Name:'] = 'Tube Name:'  # это я уже сама внутри программы делаю для удобства
    columns['Sample ID:'] = 'Sample ID:'
    names = []
    for i in populations:
        names.append(populations[i])
        key = i + ' Events'
        columns[key] = populations[i]
        if key not in temp.columns:
            return(pd.DataFrame())
    temp.columns = temp.iloc[1]
    temp = temp.drop(labels=0, axis=0)  # таблица без названия эксперимента, все расчеты дальше с ней
    temp = temp.drop(labels=1, axis=0)
    temp = temp.loc[:, list(columns.keys())]
    temp.rename(columns=columns, inplace=True)
    temp = remove_control(temp, 'Tube Name:', 'rep')
    for i in names:
        temp[i] = temp[i].astype('int')
    return(temp)

def process_tables(cytometer, populations, test, testcv, testmin, min_events, points):
    #print('Первичные данные', data, sep = '\n')
    cur_file = Path(__file__)
    data_path = cur_file.parent.parent / 'data'
    dirs = os.listdir(data_path)
    k = 0
    file_lot = {}
    for file in dirs:
        if file.endswith(".csv"):
            k += 1
            p = Path(data_path, file)
            table = pd.read_csv(p, sep=',')
            if cytometer == 'FACS Canto II':
                temp = table_FACS(table, populations)
                if temp.empty:
                    raise ValueError(f'Неверное название столбца:{file}')
            else:
                temp = table_FLEX(table, populations)
                if temp.empty:
                    raise ValueError(f'Неверное название столбца:{file}')
            if k == 1:
                res = temp
            else:
                if not pd.merge(res, temp, how = 'inner').empty:
                    raise ValueError(f'Два одинаковых файла:{file}')
                if not pd.merge(res, temp, on =['Sample ID:', 'Tube Name:'], how = 'inner').empty:
                    raise ValueError(f'Два одинаковых образца:{file}')
                res = pd.concat([res, temp])
    print(k)
    compute(res, testcv, testmin, min_events, points, test)

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
    sd = data[child].std() #несмещенная
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
            table.loc[(lot_pd[0], int(lot_pd[1])), col] = cv
            res_krit.loc[(lot_pd[0], int(lot_pd[1])), col] = check(cv, testcv[j][1], testcv[j][2])
        for j in min_events:
            col = find_col(table, j, 'min')
            table.loc[(lot_pd[0], int(lot_pd[1])), col] = i[1][j].min()
            res_krit.loc[(lot_pd[0], int(lot_pd[1])), col] = check(i[1][j].min(), 'min events', min_events[j])
    return(table, res_krit)

def compute(temp, testcv, testmin, min_events, points, test): #запускает все функции подсчета таблиц и генерирует excel-файлы
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
    for i in krit_data:
        style_df = (
            krit_data[i][1] == 0
        ).replace({
            True: 'color:red',
            False: ''
        })
        #print(i, krit_data[i][0])
        krit_data[i][0].style.apply(lambda _: style_df, axis = None).to_excel(f'{i}.xlsx', engine='openpyxl', index = False)

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
