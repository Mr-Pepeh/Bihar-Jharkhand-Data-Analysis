"""
Gender disparities in employment structure: research plotting script.

Input:
  Project 1 Occupation.xlsx

Run:
  python employment_gender_gap_plots.py

The script filters Bihar and Jharkhand, male/female, PS+SS and the
four mutually exclusive employment categories. It creates gender-gap,
trend, rural-urban, composition bar, pie, heatmap and state-comparison
figures at 300 dpi, plus tidy analysis tables.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

INPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "Project 1 Occupation.xlsx"
OUT = Path("employment_gender_gap_analysis")
FIG = OUT / "figures"
FIG.mkdir(parents=True, exist_ok=True)
OUT.mkdir(exist_ok=True)

df = pd.read_excel(INPUT_FILE)
for c in ["state","gender","sector","weekly_status","broad_status_employment","indicator"]:
    df[c] = df[c].astype(str).str.strip()
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["value"] = pd.to_numeric(df["value"], errors="coerce")

states = ["Bihar", "Jharkhand"]
cat_map = {
 "1.self-employed: own account worker, employer": "Own-account worker / employer",
 "2.self-employed: helper in household enterprise": "Helper in household enterprise",
 "4.regular wage/salary": "Regular wage / salary",
 "5.casual labour": "Casual labour"
}
cats = list(cat_map.values())
d = df[df.state.isin(states) & df.gender.isin(["male","female"])
       & (df.weekly_status=="PS+SS")
       & (df.indicator.str.lower()=="percentage distribution of workers")
       & df.broad_status_employment.isin(cat_map)
       & df.year.notna() & df.value.notna()].copy()
d["category"] = d.broad_status_employment.map(cat_map)
d["year"] = d.year.astype(int)
overall = d[d.sector.str.lower()=="rural + urban"].copy()
ru = d[d.sector.str.lower().isin(["rural","urban"])].copy()

g = overall.pivot_table(index=["year","state","category"], columns="gender",
                        values="value", aggfunc="mean").reset_index()
g["gap"] = g["female"] - g["male"]
rg = ru.pivot_table(index=["year","state","sector","category"], columns="gender",
                    values="value", aggfunc="mean").reset_index()
rg["gap"] = rg["female"] - rg["male"]
overall.to_csv(OUT/"cleaned_overall_PS_SS.csv", index=False)
ru.to_csv(OUT/"cleaned_rural_urban_PS_SS.csv", index=False)
g.to_csv(OUT/"gender_gap_overall.csv", index=False)
rg.to_csv(OUT/"gender_gap_rural_urban.csv", index=False)

colors = {"blue":"#1565C0","red":"#C62828","black":"#222222","orange":"#EF6C00"}
cat_colors = dict(zip(cats,[colors["blue"],colors["orange"],colors["black"],colors["red"]]))
plt.rcParams.update({"font.family":"DejaVu Sans","axes.titlesize":13,
 "axes.titleweight":"bold","axes.labelweight":"bold","figure.dpi":150,
 "savefig.dpi":300,"axes.spines.top":False,"axes.spines.right":False,
 "pdf.fonttype":42})
yr = int(g.year.max())

def save(fig, name):
    fig.savefig(FIG/name, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)

# 1. Diverging gender-gap bars
fig, axs = plt.subplots(1,2,figsize=(14,6),sharex=True)
for ax, st in zip(axs,states):
    z=g[(g.state==st)&(g.year==yr)].set_index("category").reindex(cats)
    v=z.gap.fillna(0).values
    ax.barh(np.arange(len(cats)),v,color=[colors["red"] if x>0 else colors["blue"] for x in v])
    ax.axvline(0,color=colors["black"],lw=1)
    ax.set_yticks(np.arange(len(cats)),cats); ax.invert_yaxis()
    ax.set_title(st); ax.set_xlabel("Female share − male share (percentage points)")
    ax.grid(axis="x",alpha=.4)
    for i,x in enumerate(v):
        ax.text(x+(0.2 if x>=0 else -0.2),i,f"{x:+.1f}",va="center",
                ha="left" if x>=0 else "right",fontweight="bold")
fig.suptitle(f"Gender gaps in employment composition ({yr})",fontweight="bold")
fig.tight_layout(); save(fig,"01_gender_gap_diverging_bars.png")

# 2. Gender-gap trends; line style differs by category
fig,axs=plt.subplots(1,2,figsize=(15,6),sharey=True)
styles=["-","--","-.",":"]
for ax,st in zip(axs,states):
    z=g[g.state==st]
    for i,cat in enumerate(cats):
        q=z[z.category==cat].sort_values("year")
        ax.plot(q.year,q.gap,color=cat_colors[cat],ls=styles[i],marker="o",
                lw=2.1,label=cat)
    ax.axhline(0,color=colors["black"],lw=.9)
    ax.set_title(st); ax.set_xlabel("Year"); ax.grid(alpha=.4)
axs[0].set_ylabel("Gender gap (percentage points)")
h,l=axs[0].get_legend_handles_labels()
fig.legend(h,l,loc="lower center",ncol=2,frameon=False)
fig.suptitle("Annual change in gender gaps",fontweight="bold")
fig.tight_layout(rect=[0,.08,1,.95]); save(fig,"02_gender_gap_trends.png")

# 3. Rural-urban gaps
fig,axs=plt.subplots(2,2,figsize=(14,10),sharex=True,sharey=True)
for i,st in enumerate(states):
    for j,sec in enumerate(["rural","urban"]):
        ax=axs[i,j]
        z=rg[(rg.state==st)&(rg.sector.str.lower()==sec)&(rg.year==yr)]
        z=z.set_index("category").reindex(cats); v=z.gap.fillna(0).values
        ax.barh(np.arange(len(cats)),v,color=[colors["red"] if x>0 else colors["blue"] for x in v])
        ax.axvline(0,color=colors["black"],lw=.9)
        ax.set_yticks(np.arange(len(cats)),cats); ax.invert_yaxis()
        ax.set_title(f"{st} — {sec.title()}"); ax.grid(axis="x",alpha=.4)
        if i==1: ax.set_xlabel("Gender gap (percentage points)")
        for k,x in enumerate(v):
            ax.text(x+(0.2 if x>=0 else -0.2),k,f"{x:+.1f}",va="center",
                    ha="left" if x>=0 else "right",fontweight="bold",fontsize=8)
fig.suptitle(f"Rural–urban comparison of gender gaps ({yr})",fontweight="bold")
fig.tight_layout(); save(fig,"03_rural_urban_gender_gaps.png")

# 4. Composition bar charts
fig,axs=plt.subplots(2,2,figsize=(14,9),sharey=True)
for i,st in enumerate(states):
    for j,sex in enumerate(["male","female"]):
        ax=axs[i,j]
        z=overall[(overall.state==st)&(overall.gender==sex)&(overall.year==yr)]
        z=z.set_index("category").reindex(cats)
        ax.bar(range(len(cats)),z.value.fillna(0),
               color=[cat_colors[c] for c in cats])
        ax.set_xticks(range(4),["Own-account","Household\\nhelper","Regular\\nwage","Casual"])
        ax.set_title(f"{st} — {sex.title()} workers")
        ax.set_ylabel("Share of workers (%)"); ax.grid(axis="y",alpha=.4)
fig.suptitle(f"Employment composition by gender ({yr})",fontweight="bold")
fig.tight_layout(); save(fig,"04_employment_composition_bars.png")

# 5. Pie charts (supporting visual only)
fig,axs=plt.subplots(2,2,figsize=(13,10))
for i,st in enumerate(states):
    for j,sex in enumerate(["male","female"]):
        ax=axs[i,j]
        z=overall[(overall.state==st)&(overall.gender==sex)&(overall.year==yr)]
        z=z.set_index("category").reindex(cats)
        v=z.value.fillna(0).clip(lower=0).values
        ax.pie(v,colors=[cat_colors[c] for c in cats],startangle=90,
               autopct=lambda p:f"{p:.1f}%" if p>=3 else "",
               wedgeprops={"edgecolor":"white","linewidth":1})
        ax.set_title(f"{st} — {sex.title()} workers")
fig.legend([plt.Rectangle((0,0),1,1,color=cat_colors[c]) for c in cats],cats,
           loc="lower center",ncol=2,frameon=False)
fig.suptitle(f"Employment composition: category shares ({yr})",fontweight="bold")
fig.tight_layout(rect=[0,.08,1,.95]); save(fig,"05_employment_composition_pies.png")

# 6. Heatmap
heat=rg[rg.year==yr].copy()
heat["state_sector"]=heat.state+" — "+heat.sector.str.title()
hp=heat.pivot_table(index="category",columns="state_sector",values="gap",aggfunc="mean").reindex(cats)
order=["Bihar — Rural","Bihar — Urban","Jharkhand — Rural","Jharkhand — Urban"]
hp=hp.reindex(columns=[x for x in order if x in hp.columns])
fig,ax=plt.subplots(figsize=(11,5.5))
a=hp.values.astype(float); lim=max(1,np.nanmax(np.abs(a)))
im=ax.imshow(a,cmap="RdBu_r",aspect="auto",vmin=-lim,vmax=lim)
ax.set_xticks(range(len(hp.columns)),hp.columns,rotation=15,ha="right")
ax.set_yticks(range(len(hp.index)),hp.index); ax.set_title(f"Gender-gap heatmap ({yr})")
for i in range(a.shape[0]):
    for j in range(a.shape[1]):
        if np.isfinite(a[i,j]): ax.text(j,i,f"{a[i,j]:+.1f}",ha="center",va="center",fontweight="bold")
cb=fig.colorbar(im,ax=ax); cb.set_label("Female share − male share (percentage points)",fontweight="bold")
fig.tight_layout(); save(fig,"06_gender_gap_heatmap.png")

# 7. State comparison
p=g[g.year==yr].pivot_table(index="category",columns="state",values="gap").reindex(cats)
fig,ax=plt.subplots(figsize=(11,6)); x=np.arange(4); w=.34
for off,st,col in [(-w/2,"Bihar",colors["blue"]),(w/2,"Jharkhand",colors["orange"])]:
    v=p[st].values
    bars=ax.bar(x+off,v,w,label=st,color=col)
    for b,y in zip(bars,v):
        ax.text(b.get_x()+b.get_width()/2,y+(0.2 if y>=0 else -.2),f"{y:+.1f}",
                ha="center",va="bottom" if y>=0 else "top",fontweight="bold",fontsize=8)
ax.axhline(0,color=colors["black"],lw=1)
ax.set_xticks(x,["Own-account","Household helper","Regular wage","Casual labour"])
ax.set_ylabel("Gender gap (percentage points)"); ax.set_title(f"Bihar–Jharkhand gender-gap comparison ({yr})")
ax.legend(frameon=False); ax.grid(axis="y",alpha=.4)
fig.tight_layout(); save(fig,"07_state_comparison_gender_gaps.png")

with pd.ExcelWriter(OUT/"gender_gap_analysis_tables.xlsx") as writer:
    overall.to_excel(writer,sheet_name="Overall_PS_SS",index=False)
    ru.to_excel(writer,sheet_name="Rural_Urban_PS_SS",index=False)
    g.to_excel(writer,sheet_name="Overall_Gender_Gaps",index=False)
    rg.to_excel(writer,sheet_name="Rural_Urban_Gaps",index=False)

print("Analysis complete. Figures and tables saved in:", OUT.resolve())
