import pandas as pd

from fctool.main import comp_cv


cv_inp1 = pd.DataFrame({
    "child": [1, 1, 1],
    "parent": [7, 7, 7]
})

def test_comp_cv():
   actual_res = comp_cv(cv_inp1, "child", "parent")

   # print(actual_res)

   assert actual_res > 90


