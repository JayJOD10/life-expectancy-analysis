"""Life Expectancy (WHO) analysis - Pandas, NumPy, SciPy, Matplotlib only."""
import re, os
import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

CSV = "Life Expectancy Data.csv"   # file downloaded from Kaggle
os.makedirs("graphs", exist_ok=True)
df = pd.read_csv(CSV)

# clean column names with a regular expression (Unit II): "Adult Mortality " -> "Adult_Mortality"
GOOD = ["Country","Year","Status","Life_expectancy","Adult_Mortality","Infant_deaths","Alcohol",
        "Percentage_expenditure","Hepatitis_B","Measles","BMI","Under_five_deaths","Polio",
        "Total_expenditure","Diphtheria","HIV_AIDS","GDP","Population","Thinness_1_19_years",
        "Thinness_5_9_years","Income_composition_of_resources","Schooling"]
lookup = {g.lower(): g for g in GOOD}
df.columns = [lookup.get(re.sub(r"[^0-9a-zA-Z]+", "_", c).strip("_").lower(), c) for c in df.columns]
LE = "Life_expectancy"

# missing values summary
miss = df.isna().sum().sort_values(ascending=False)
miss = miss[miss > 0]
print("MISSING\n", miss)

# cleaning: fill numeric gaps with each country's median, then overall median
num = df.select_dtypes("number").columns.drop("Year")
df[num] = df.groupby("Country")[num].transform(lambda s: s.fillna(s.median()))
df[num] = df[num].fillna(df[num].median())
print("remaining NaN:", df.isna().sum().sum())

# Fig1 missing
fig, ax = plt.subplots(figsize=(7,4))
ax.barh(miss.index[::-1], miss.values[::-1], color="#c0504d")
ax.set_xlabel("Missing values"); ax.set_title("Missing values per column (before cleaning)")
plt.tight_layout(); plt.savefig("graphs/f1_missing.png", dpi=150); plt.close()

# Fig2 histogram
fig, ax = plt.subplots(figsize=(7,4))
ax.hist(df[LE], bins=25, color="#4f81bd", edgecolor="white")
ax.axvline(df[LE].mean(), color="red", ls="--", label=f"Mean = {df[LE].mean():.1f}")
ax.set_xlabel("Life expectancy (years)"); ax.set_ylabel("Number of records"); ax.legend()
ax.set_title("Distribution of life expectancy")
plt.tight_layout(); plt.savefig("graphs/f2_hist.png", dpi=150); plt.close()
print("LE mean/median/std/min/max", df[LE].mean(), df[LE].median(), df[LE].std(), df[LE].min(), df[LE].max())

# Fig3 boxplot by status
dev = df[df.Status=="Developed"][LE]; dvg = df[df.Status=="Developing"][LE]
fig, ax = plt.subplots(figsize=(6,4))
bp = ax.boxplot([dvg, dev], patch_artist=True)
ax.set_xticklabels(["Developing","Developed"])
for p,c in zip(bp["boxes"],["#f79646","#4f81bd"]): p.set_facecolor(c)
ax.set_ylabel("Life expectancy (years)"); ax.set_title("Life expectancy by country status")
plt.tight_layout(); plt.savefig("graphs/f3_box.png", dpi=150); plt.close()
t,p = stats.ttest_ind(dev, dvg, equal_var=False)
print("STATUS means", dev.mean(), dvg.mean(), "t",t,"p",p, "n", len(dev), len(dvg))

# Fig4 trend
tr = df.groupby(["Year","Status"])[LE].mean().unstack()
allyr = df.groupby("Year")[LE].mean()
fig, ax = plt.subplots(figsize=(7,4))
ax.plot(allyr.index, allyr.values, "k-o", label="All countries")
ax.plot(tr.index, tr["Developed"], "-s", color="#4f81bd", label="Developed")
ax.plot(tr.index, tr["Developing"], "-^", color="#f79646", label="Developing")
ax.set_xlabel("Year"); ax.set_ylabel("Average life expectancy (years)"); ax.legend(); ax.grid(alpha=.3)
ax.set_title("Average life expectancy, 2000-2015")
plt.tight_layout(); plt.savefig("graphs/f4_trend.png", dpi=150); plt.close()
print("TREND all", allyr.iloc[0], allyr.iloc[-1]); print(tr.iloc[[0,-1]])

# Fig5 correlation heatmap
cols = [LE,"Adult_Mortality","HIV_AIDS","Schooling","Income_composition_of_resources","BMI","GDP","Alcohol","Polio","Diphtheria","Hepatitis_B","Total_expenditure","Under_five_deaths"]
cm = df[cols].corr()
fig, ax = plt.subplots(figsize=(8,6.5))
im = ax.imshow(cm, cmap="coolwarm", vmin=-1, vmax=1)
ax.set_xticks(range(len(cols))); ax.set_yticks(range(len(cols)))
ax.set_xticklabels(cols, rotation=60, ha="right", fontsize=8); ax.set_yticklabels(cols, fontsize=8)
for i in range(len(cols)):
    for j in range(len(cols)): ax.text(j,i,f"{cm.iloc[i,j]:.2f}",ha="center",va="center",fontsize=6)
plt.colorbar(im, fraction=.046); ax.set_title("Correlation heatmap")
plt.tight_layout(); plt.savefig("graphs/f5_heat.png", dpi=150); plt.close()
print("CORR with LE\n", cm[LE].sort_values())

# Fig6/7 scatter + regression
def scat(x, name, fn, color, logx=False):
    d = df[[x,LE]].dropna()
    xv = np.log10(d[x]+1) if logx else d[x]
    r = stats.linregress(xv, d[LE])
    fig, ax = plt.subplots(figsize=(6.5,4.2))
    ax.scatter(xv, d[LE], s=8, alpha=.35, color=color)
    xs = np.linspace(xv.min(), xv.max(), 50); ax.plot(xs, r.intercept+r.slope*xs, "r-", lw=2)
    ax.set_xlabel(("log10 " if logx else "")+name); ax.set_ylabel("Life expectancy (years)")
    ax.set_title(f"{name} vs life expectancy (r = {r.rvalue:.2f})")
    plt.tight_layout(); plt.savefig(fn, dpi=150); plt.close()
    print(x, "slope",r.slope,"r",r.rvalue,"r2",r.rvalue**2,"p",r.pvalue)
scat("Schooling","Schooling (years)","graphs/f6_school.png","#4f81bd")
scat("Adult_Mortality","Adult mortality (per 1000)","graphs/f7_adult.png","#9bbb59")
scat("GDP","GDP (USD)","graphs/f8_gdp.png","#8064a2", logx=True)

# Fig9 top/bottom countries
cavg = df.groupby("Country")[LE].mean().sort_values()
sel = pd.concat([cavg.head(10), cavg.tail(10)])
fig, ax = plt.subplots(figsize=(7,6))
ax.barh(sel.index, sel.values, color=["#c0504d"]*10+["#4f81bd"]*10)
ax.set_xlabel("Average life expectancy (years)"); ax.set_title("Lowest 10 and highest 10 countries (2000-2015 average)")
plt.tight_layout(); plt.savefig("graphs/f9_top.png", dpi=150); plt.close()
print("BOTTOM\n", cavg.head(10)); print("TOP\n", cavg.tail(10))

# Fig10 immunization
imm = df.groupby("Status")[["Polio","Diphtheria","Hepatitis_B"]].mean()
fig, ax = plt.subplots(figsize=(6.5,4)); w=.35; x=np.arange(3)
ax.bar(x-w/2, imm.loc["Developing"], w, label="Developing", color="#f79646")
ax.bar(x+w/2, imm.loc["Developed"], w, label="Developed", color="#4f81bd")
ax.set_xticks(x); ax.set_xticklabels(["Polio","Diphtheria","Hepatitis B"]); ax.set_ylabel("Average coverage (%)"); ax.legend()
ax.set_title("Immunization coverage by status"); ax.set_ylim(0,100)
plt.tight_layout(); plt.savefig("graphs/f10_imm.png", dpi=150); plt.close()
print(imm)
print("COUNTRIES by status", df.groupby("Status")["Country"].nunique())
