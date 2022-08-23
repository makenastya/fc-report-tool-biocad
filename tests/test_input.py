import pandas as pd

from pathlib import Path

from fctool.main import comp_cv, process_tables

def test_main():
    import tests.dsFACS as ds
    process_tables(ds.cytometer, ds.populations, ds.test, ds.testcv, ds.testmin, ds.min_events, ds.points)
