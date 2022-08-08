
import numpy as np
import pandas as pd


def read_file() -> pd.DataFrame:
    data_path = 'C:\\Users\\makeevaa\\2021-04-24_BCD132-4_Bmem2_406-1_408-1_411-1.csv'
    data = pd.read_csv(data_path, sep = ';')
    data = data.drop(labels = 0, axis = 0) #это можно вернуть как изначальные данные если склеить с другими таблицами
    #print('Первичные данные', data, sep = '\n')
    temp = data.copy()
    temp.columns = temp.iloc[0]
    temp = temp.drop(labels = 1, axis=0)#таблица без названия эксперимента, все расчеты дальше с ней
    names = ['1-3 B-cells Events', '1-5 Plasm 1 Events', '1-4 Bmem Events', 'naive Events'] #дочерние популяции, считывать из входных данных
    parent = '1-4 Lymph Events'
    temp[parent] = temp[parent].astype('int')
    for i in names:
        temp[i] = temp[i].astype('int')
    return(temp, names, parent)

def biotable(temp): #таблица учета биообразцов
    table = pd.DataFrame(columns=('PD-1', 'PD-2', 'PD-3', 'PD-4', 'PD-5', 'PD-6', 'PD-7'))  # надо будет задавать количество столбцов
    table.index.name = 'ЛОТ'
    for i in range(len(temp)):
        id = temp['Sample ID:'].iloc[i]
        lot_pd = id.split('-')
        PD = 'PD-' + lot_pd[1]
        table.loc[int(lot_pd[0]), PD] = '+'
    return(table)

def comp_cv(df: pd.DataFrame, child, parent): #может возвращать cv, а может сразу результат пригодности(сравнить с limit)
    df[child] = df[child] / df[parent] * 100
    mean = df[child].mean()
    sd = df[child].std()
    return(sd / mean * 100)

def krit(df : pd.DataFrame, names, parent): #собирает таблицу из всех критериев
    table = pd.DataFrame(columns=('ЛОТ', 'Точка PD', '%CV 1-3 B-cells Events', '%CV 1-4 Bmem Events', '%CV 1-5 Plasm 1 Events', '%CV naive Events'))#пока что нужно, чтобы названия колонок содержали названия популяций, потом можно будет это как-то проверять или сделать таблицу соответствий
    df = df.loc[df['Tube Name:'].str.contains('rep')]
    group = df.groupby('Sample ID:')
    list_group = list(group)
    for i in list_group:
        lot_pd = i[0].split('-')
        PD = 'PD-' + lot_pd[1]
        table.loc[int(lot_pd[0]) * 10 + int(lot_pd[1]), 'ЛОТ'] = lot_pd[0]
        table.loc[int(lot_pd[0]) * 10 + int(lot_pd[1]), 'Точка PD'] = lot_pd[1]
        for j in names:
            cv = comp_cv(i[1], j, parent)
            for col in table.columns:
                if j in col:
                    table.loc[int(lot_pd[0]) * 10 + int(lot_pd[1]), col] = cv #индексы странные зато уникальные
    table = table.set_index(['ЛОТ', 'Точка PD'])
    return(table)

def compute(temp, names, parent): #запускает все функции подсчета таблиц и выводит их
    temp = temp.sort_values(by = 'Sample ID:')
    table = biotable(temp)
    print('Учет биообразцов', table, sep = '\n')
    for i in names:  #если не нужно хранить 4 отдельных датафрейма, или же можно записать их в общую структуру
        table = comp_percentgb(temp, i, parent)
        print('Mean %', i, 'in', parent)
        print(table)
    krit_table = krit(temp, names, parent)
    print('Критерии пригодности', krit_table, sep = '\n')
def comp_percentgb(df : pd.DataFrame, child, parent): #считает процент дочерних клеток в родительских
    df = df.loc[df['Tube Name:'].str.contains('rep')]
    group = df.groupby('Sample ID:')
    list_group = list(group)
    table = pd.DataFrame(columns=('PD-1', 'PD-2', 'PD-3', 'PD-4', 'PD-5', 'PD-6', 'PD-7'))
    table.index.name = 'ЛОТ'
    for i in list_group:
        i[1][child] = i[1][child] / i[1][parent] * 100
        lot_pd = i[0].split('-')
        PD = 'PD-' + lot_pd[1]
        table.loc[int(lot_pd[0]), PD] = i[1][child].mean()
    return(table)

data = read_file()
compute(data[0], data[1], data[2])
