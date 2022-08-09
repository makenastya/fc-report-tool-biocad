
import numpy as np
import pandas as pd
#pd.set_option('display.max_rows', None)
#pd.set_option('display.max_columns', None)
#pd.set_option('display.max_colwidth', None)

def read_file(

) -> pd.DataFrame:
    data_path = 'C:\\Users\\makeevaa\\2021-04-24_BCD132-4_Bmem2_406-1_408-1_411-1.csv'
    data = pd.read_csv(data_path, sep = ';')
    data = data.drop(labels = 0, axis = 0) #это можно вернуть как изначальные данные если склеить с другими таблицами, проверить на минимальное количество клеток
    #print('Первичные данные', data, sep = '\n')
    testcv = {}  # пока вбила руками, будет считываться из входного файла
    testcv['1-3 B-cells Events'] = ['1-4 Lymph Events', 'no more than', 20]
    testcv['1-5 Plasm 1 Events'] = ['1-4 Lymph Events', 'no more than', 35]
    testcv['1-4 Bmem Events'] = ['1-4 Lymph Events', 'no more than', 20]
    testcv['naive Events'] = ['1-4 Lymph Events', 'no more than', 20]
    testmin = {}  # пока вбила руками, будет считываться из входного файла
    testmin['1-3 B-cells Events'] = ['1-4 Lymph Events', 'not less than', 0.124]
    testmin['1-5 Plasm 1 Events'] = ['1-4 Lymph Events', 'not less than', 0.025]
    testmin['1-4 Bmem Events'] = ['1-4 Lymph Events', 'not less than', 0.059]
    testmin['naive Events'] = ['1-4 Lymph Events', 'not less than', 0] #надо вбить значение
    min_events = {}
    min_events['1-4 Lymph Events'] = 25000
    min_events['naive Events'] = 12000
    points = 7
    test = {}
    test['naive Events'] = '1-4 Lymph Events'
    test['1-3 B-cells Events'] = '1-4 Lymph Events'
    test['1-5 Plasm 1 Events'] = '1-4 Lymph Events'
    test['1-4 Bmem Events'] = '1-4 Lymph Events'
    temp = data.copy()
    temp.columns = temp.iloc[0]
    temp = temp.drop(labels = 1, axis = 0)#таблица без названия эксперимента, все расчеты дальше с ней
    names = ['1-3 B-cells Events', '1-5 Plasm 1 Events', '1-4 Bmem Events', 'naive Events'] #дочерние популяции, считывать из входных данных
    parent = '1-4 Lymph Events'
    temp[parent] = temp[parent].astype('int')
    for i in names:
        temp[i] = temp[i].astype('int')
    return(temp, testcv, testmin, min_events, points, test)

def biotable(temp, points): #таблица учета биообразцов
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

def comp_cv(df, child, parent): #может возвращать cv, а может сразу результат пригодности(сравнить с limit)
    data = df.copy()
    data[child] = data[child] / data[parent] * 100
    mean = data[child].mean()
    sd = data[child].std() #несмещенная
    return(sd / mean * 100)

def remove_control(df, column, rep):
    df = df.loc[df[column].str.contains(rep)]
    return(df)
def find_col(df, name, fl):
    for i in df.columns:
        if (name in i) and (fl in i):
            return(i)
def check(number: int, oper: str, ref: int):
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

def krit(df : pd.DataFrame, testcv, min_events): #собирает таблицу из всех критериев
    s = []
    s.append('ЛОТ')
    s.append('Точка PD')
    for i in min_events:
        c = 'min ' + i
        s.append(c)
    for i in testcv:
        c = '%CV ' + i
        s.append(c)
    table = pd.DataFrame(columns = s)
    res_krit = pd.DataFrame(columns = s)
    df = remove_control(df, 'Tube Name:', 'rep')
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
            table.loc[(lot_pd[0], lot_pd[1]), col] = cv
            res_krit.loc[(lot_pd[0], lot_pd[1]), col] = check(cv, testcv[j][1], testcv[j][2])
        for j in min_events:
            col = find_col(table, j, 'min')
            table.loc[(lot_pd[0], lot_pd[1]), col] = i[1][j].min()
            res_krit.loc[(lot_pd[0], lot_pd[1]), col] = check(i[1][j].min(), 'min events', min_events[j])
    return(table, res_krit)

def compute(temp, testcv, testmin, min_events, points, test): #запускает все функции подсчета таблиц и выводит их
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
    krit_data['Критерии пригодности'] = table

def comp_percentgb(df : pd.DataFrame, child, parent, krit: list, points): #считает процент дочерних клеток в родительских
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
        res_krit.loc[int(lot_pd[0]), PD] = check(i[1][child].mean(), krit[1], krit[2])
    return(table, res_krit)

data = read_file()
compute(data[0], data[1], data[2], data[3], data[4], data[5])

