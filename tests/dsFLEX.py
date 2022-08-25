cytometer = 'cytoFLEX'
populations = {}  # задать названия нужных для анализа столбцов и желаемое название в отчете
populations['1-4 Lymph'] = 'Lymph'
populations['1-3 B-cells'] = 'B-cells'
populations['1-5 Plasm 1'] = 'Plasm'
populations['1-4 Bmem'] = 'B-mem'
populations['naive'] = 'Naive'
testcv = {}  # CV
testcv['B-cells'] = ['Lymph', 'no more than', 20]
testcv['Plasm'] = ['Lymph', 'no more than', 35]
testcv['B-mem'] = ['Lymph', 'no more than', 20]
testcv['Naive'] = ['Lymph', 'no more than', 20]
test = {}
test['Naive'] = 'Lymph'
test['B-cells'] = 'Lymph'
test['Plasm'] = 'Lymph'
test['B-mem'] = 'Lymph'
testmin = {}
testmin['B-cells'] = ['Lymph', 'not less than', 0.124]
testmin['Plasm'] = ['Lymph', 'not less than', 0.025]
testmin['B-mem'] = ['Lymph', 'not less than', 0.059]
testmin['Naive'] = ['Lymph', 'not less than', 0]
for i in test:
    if i not in testmin:
        testmin[i] = [test[i], 'not less than', 0]
min_events = {}
min_events['Lymph'] = 25000
points = 7