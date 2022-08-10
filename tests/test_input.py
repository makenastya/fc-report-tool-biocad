import pandas as pd

from pathlib import Path

from fctool.main import comp_cv



def p_root() -> Path:
    cur_file = Path(__file__)

    return cur_file.parent.parent


def test_proot():
    print(p_root() / "my.csv")

cv_inp1 = pd.DataFrame({
    "child": [1, 1, 1],
    "parent": [7, 7, 7]
})

def test_comp_cv():
   actual_res = comp_cv(cv_inp1, "child", "parent")

   # print(actual_res)

   assert actual_res > 90


