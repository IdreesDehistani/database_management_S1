#idrees Dehistani (500992020)

#the stats tests for H2. we read the gap_analysis.csv that main.py made.
#install beforehand: pip install statsmodels scipy pandas numpy
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf

#read the file main.py exported
df = pd.read_csv("gap_analysis.csv")

#test 1 - does the gap change between the rating groups?
#we use kruskal because the numbers are not nicely spread (skewed)
groups = [g["abs_gap"].values for _, g in df.groupby("rating_group")]
h, p = stats.kruskal(*groups)
print(f"\n[1] Kruskal-Wallis, abs_gap by rating: H={h:.2f}, p={p:.4g}")

#test 2 - does the gap go up or down with runtime and budget?
#spearman looks at the order of the numbers, not the exact value
for col in ["runtime", "budget"]:
    d = df[["abs_gap", col]].dropna()         #drop the rows with no value
    r, p = stats.spearmanr(d["abs_gap"], d[col])
    print(f"[2] Spearman abs_gap vs {col}: rho={r:.3f}, p={p:.4g}, n={len(d)}")

#test 3 - put all three things (rating, runtime, budget) in one regression
#we take the log of budget because the budget numbers are very big and uneven
m = df.dropna(subset=["runtime", "budget"]).copy()
m["log_budget"] = np.log(m["budget"])
model = smf.ols("abs_gap ~ runtime + log_budget + I(log_budget**2) + C(rating_group, Treatment('R'))",
                data=m).fit(cov_type="HC3")   #HC3 just makes the errors more safe
print(f"\n[3] OLS regression (n={int(model.nobs)})")
print(model.summary().tables[1])
print(f"R-squared = {model.rsquared:.3f}  (how much of the gap the 3 things explain)")
