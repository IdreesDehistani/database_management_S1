# H2 statistical tests on gap_analysis.csv (exported by main.py)
# Install once: pip install statsmodels scipy
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf

df = pd.read_csv("gap_analysis.csv")

# 1) Rating: does abs_gap differ across rating groups? (Kruskal-Wallis = ANOVA for skewed data)
groups = [g["abs_gap"].values for _, g in df.groupby("rating_group")]
h, p = stats.kruskal(*groups)
print(f"\n[1] Kruskal-Wallis, abs_gap by rating: H={h:.2f}, p={p:.4g}")

# 2) Runtime & budget: Spearman correlation (rank-based, catches non-straight trends)
for col in ["runtime", "budget"]:
    d = df[["abs_gap", col]].dropna()
    r, p = stats.spearmanr(d["abs_gap"], d[col])
    print(f"[2] Spearman abs_gap vs {col}: rho={r:.3f}, p={p:.4g}, n={len(d)}")

# 3) OLS regression: all three H2 variables together (controls for their overlap)
#    log(budget) because budget is hugely skewed; budget^2 term tests the inverted-U
m = df.dropna(subset=["runtime", "budget"]).copy()
m["log_budget"] = np.log(m["budget"])
model = smf.ols("abs_gap ~ runtime + log_budget + I(log_budget**2) + C(rating_group, Treatment('R'))",
                data=m).fit(cov_type="HC3")  # HC3 = robust standard errors
print(f"\n[3] OLS regression (n={int(model.nobs)})")
print(model.summary().tables[1])
print(f"R-squared = {model.rsquared:.3f}  (share of gap variation the 3 variables explain)")
