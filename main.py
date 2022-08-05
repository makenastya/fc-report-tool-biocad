
import numpy as np
import pandas as pd


def read_file():
    data_path = 'C:\\Users\\makeevaa\\2021-04-24_BCD132-4_Bmem2_406-1_408-1_411-1.csv'
    data = pd.read_csv(data_path, sep = ';')
    data = data.drop(labels = 0, axis = 0) #это можно вернуть как изначальные данные если склеить с другими таблицами
    #print('Первичные данные', data, sep = '\n')
    temp = data.copy()
    temp.columns = temp.iloc[0]
    temp = temp.drop(labels = 1, axis=0)#таблица без названия эксперимента, все расчеты дальше с ней
    compute(temp) #считает все таблицы

def biotable(temp): #таблица учета биообразцов
    table = pd.DataFrame(columns=('PD-1', 'PD-2', 'PD-3', 'PD-4', 'PD-5', 'PD-6', 'PD-7'))  # надо будет задавать количество столбцов
    for i in range(len(temp)):
        id = temp['Sample ID:'].iloc[i]
        lot_pd = id.split('-')
        PD = 'PD-' + lot_pd[1]
        table.loc[int(lot_pd[0]), PD] = '+'
    return(table)

def comp_percent(temp, child, parent): #возвращает таблицу с % дочерней в родительской популяции
    table = pd.DataFrame(columns=('PD-1', 'PD-2', 'PD-3', 'PD-4', 'PD-5', 'PD-6', 'PD-7'))
    i = 0
    while i < len(temp):
        row = temp.iloc[i]
        if row['Sample ID:'] in table.index:
            continue
        else:
            ID = row['Sample ID:']
            sum = 0
            kol = 0
            while (row['Sample ID:'] == ID and i < len(temp)):
                if 'rep' in row['Tube Name:']:
                    ans = (int(row[child]) / int(row[parent])) * 100
                    sum += ans
                    kol += 1
                i += 1
                if i < len(temp):
                    row = temp.iloc[i]
            lot_pd = ID.split('-')
            PD = 'PD-' + lot_pd[1]
            table.loc[int(lot_pd[0]), PD] = sum / kol
    return(table)

def krit(temp):
    table = pd.DataFrame(columns=('% CV B-cells', '% CV B-mem', '% CV Plasm', '% CV naive'))
    i = 0
    while i < len(temp):
        row = temp.iloc[i]
        if row['Sample ID:'] in table.index:
            continue
        else:
            ID = row['Sample ID:']
            sum = 0
            kol = 0
            while (row['Sample ID:'] == ID and i < len(temp)):
                if 'rep' in row['Tube Name:']:
                    ans = (int(row[child]) / int(row[parent])) * 100
                    sum += ans
                    kol += 1
                    #посчитать std для всех и mean для всех
                i += 1
                if i < len(temp):
                    row = temp.iloc[i]
            lot_pd = ID.split('-')
            PD = 'PD-' + lot_pd[1]
            table.loc[int(lot_pd[0]), PD] = sum / kol
    return (table)


def compute(temp): #запускает все функции подсчета таблиц и выводит их
    temp = temp.sort_values(by = 'Sample ID:')
    table = biotable(temp)
    print('Учет биообразцов', table, sep = '\n')
    b_cells = comp_percent(temp, '1-3 B-cells Events', '1-4 Lymph Events')
    plasm = comp_percent(temp, '1-5 Plasm 1 Events', '1-4 Lymph Events')
    Bmem = comp_percent(temp, '1-4 Bmem Events', '1-4 Lymph Events')
    naive = comp_percent(temp, 'naive Events', '1-4 Lymph Events')
    print('Mean % 1-3 B-cells in 1-4 Lymph', b_cells, sep = '\n') #Mean % 1-3 B-cells in 1-4 Lymph
    print('Mean % 1-5 Plasm 1 in 1-4 Lymph', plasm, sep = '\n') #Mean % 1-5 Plasm 1 in 1-4 Lymph
    print('Mean % 1-4 Bmem in 1-4 Lymph', Bmem, sep = '\n') #Mean % 1-4 Bmem in 1-4 Lymph
    print('Mean % naïve in 1-4 Lymph', naive, sep = '\n')  #Mean % naïve in 1-4 Lymph'''

read_file()