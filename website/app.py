from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from scipy import stats

HERE = Path(__file__).parent
OUT = HERE.parent / "outputs"
GREY, ACCENT = "#9aa0a6", "#e8590c"
SEVERITY = {"All serious harm": ("ksi", "People killed or seriously hurt"),
            "Severe injuries only": ("severe_inj", "People seriously hurt"),
            "Deaths only": ("fatalities", "People killed")}
HOUSING = ["All months", "Large-building months only"]
CSS = """
<style>
[data-testid="stTab"] p {font-size: 1.7rem; font-weight: 600;}
.grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin: .5rem 0 1.5rem;}
.card {border: 1px solid rgba(128,128,128,.3); border-top: 5px solid #e8590c; border-radius: 12px;
       padding: 1rem 1.2rem; background: rgba(128,128,128,.07);}
.card h4 {margin: 0 0 .4rem; font-size: 1.25rem; color: #e8590c;}
.card p {margin: 0; font-size: 1.05rem;}
.num {font-size: 2.8rem; font-weight: 700; line-height: 1.1;}
.hero .num {color: #e8590c;}
.label {opacity: .75;}
.idea {border-left: 6px solid #e8590c; background: rgba(232,89,12,.1); padding: 1rem 1.4rem;
       border-radius: 8px; font-size: 1.25rem; margin: .5rem 0 1.5rem;}
</style>
"""

st.set_page_config(page_title="NYC Housing & Traffic Safety Story", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data
def load(path="member3_integration/cd_month.csv"):
    return pd.read_csv(OUT / path)


df = load()
boroughs = sorted(df.borough.unique())
years = sorted(df.year.unique().tolist())


def reset_cd():
    st.session_state.cd = "All"


def reset():
    st.session_state.update(q="", borough="All", year="All", cd="All", severity=list(SEVERITY)[0], housing=HOUSING[0])


def search():
    q, ss = st.session_state.q.lower(), st.session_state
    for b in boroughs:
        if b.lower() in q:
            ss.borough = b
            reset_cd()
    for y in years:
        if str(y) in q:
            ss.year = y
    for cd in df.cd_label.unique():
        if cd.lower() in q:
            ss.borough, ss.cd = df.loc[df.cd_label == cd, "borough"].iloc[0], cd
    if "death" in q or "fatal" in q:
        ss.severity = "Deaths only"
    elif "severe" in q:
        ss.severity = "Severe injuries only"
    if "large" in q:
        ss.housing = HOUSING[1]


with st.sidebar:
    st.header("Filters")
    st.text_input("Search", key="q", on_change=search, placeholder="e.g. Bronx 2023 or BK 01")
    borough = st.selectbox("Borough", ["All"] + boroughs, key="borough", on_change=reset_cd)
    year = st.selectbox("Year", ["All"] + years, key="year")
    in_borough = df if borough == "All" else df[df.borough == borough]
    cd = st.selectbox("Community district", ["All"] + sorted(in_borough.cd_label.unique()), key="cd")
    severity = st.selectbox("Harm (transportation)", list(SEVERITY), key="severity")
    housing = st.selectbox("Housing activity", HOUSING, key="housing",
                           help="Large-building months are months when a district's planned units were unusually high.")
    st.button("Reset filters", on_click=reset)
    # Member 6: Generate Report Button
    if st.button("Generate Report"):
        st.session_state.show_report = True
    if st.session_state.get("show_report", False):
        st.sidebar.success("Report Generated! Check the Action tab.")

col, HARM = SEVERITY[severity]
in_borough = in_borough.assign(ksi=in_borough[col])
d = in_borough[in_borough.is_large_pipeline_month] if housing == HOUSING[1] else in_borough
if year != "All":
    d = d[d.year == year]
if cd != "All":
    d = d[d.cd_label == cd]


def by_borough(frame):
    return frame if borough == "All" else frame[frame.borough == borough]


def spearman(x, y):
    return stats.spearmanr(x, y)[0] if len(x) > 2 else float("nan")


def partial_spearman(x, y, control):
    rx, ry, rc = (stats.rankdata(v) for v in (x, y, control))
    res_x = rx - np.polyval(np.polyfit(rc, rx, 1), rc)
    res_y = ry - np.polyval(np.polyfit(rc, ry, 1), rc)
    return stats.pearsonr(res_x, res_y)[0]


def show(fig):
    st.plotly_chart(fig.update_layout(font_size=15, legend_title_text=""), width="stretch")


def cards(items, extra=""):
    html = "".join(f'<div class="card {extra}">{f"<h4>{t}</h4>" if t else ""}<p>{b}</p></div>' for t, b in items)
    st.markdown(f'<div class="grid">{html}</div>', unsafe_allow_html=True)


def callout(text):
    st.markdown(f'<div class="idea">{text}</div>', unsafe_allow_html=True)


def pair(member, left, right):
    st.divider()
    st.header(member)
    for top in (True, False):
        for column, n, (title, question, fig, note) in zip(st.columns(2), (1, 2), (left, right)):
            with column:
                if top:
                    st.subheader(title)
                    st.caption(f"**Question {n}:** {question}")
                else:
                    show(fig)
                    st.caption(note)


st.title("New housing and serious crashes mostly don't go together: only 4 of 59 neighborhoods rank in the top 10 for both")
overview, insight, action = st.tabs(["Overview", "Insight", "Action"])

with overview:
    kpis = [(HARM + " in traffic", f"{d.ksi.sum():,}", "hero"), ("New housing units planned", f"{d.new_units.sum():,.0f}", ""),
            ("New building applications", f"{d.new_filings.sum():,}", "")]
    html = "".join(f'<div class="card {c}"><div class="label">{label}</div><div class="num">{num}</div></div>' for label, num, c in kpis)
    st.markdown(f'<div class="grid">{html}</div>', unsafe_allow_html=True)
    callout("NYC planners and traffic safety teams need to know that new housing and serious crashes mostly don't rise together, "
            "but a few neighborhoods are high on both, so they can check those first.")
    cards([("1 · What?", "Months with more planned housing are not the months with more serious crashes. Only 4 of the 59 neighborhoods are in the top 10 for both."),
           ("2 · So what?", "Building activity alone doesn't show where people get hurt, so safety money shouldn't just follow construction."),
           ("3 · Now what?", "Check the 4 neighborhoods that rank top 10 for both new housing and serious crashes first (Queens 12, Brooklyn 1, Brooklyn 5, Bronx 1), then high-crash areas with little building.")])

with insight:
    totals = d.groupby(["cd_label", "borough"])[["new_filings", "crashes", "ksi"]].sum().reset_index()
    totals = totals[totals.crashes > 0]
    totals["ksi_per_crash"] = totals.ksi / totals.crashes
    r1_fig = px.scatter(totals, x="new_filings", y="ksi_per_crash", hover_name="cd_label", color_discrete_sequence=[GREY],
                        labels={"new_filings": "New building applications", "ksi_per_crash": "People killed or seriously<br>hurt per crash"})
    if len(totals) > 2:
        slope, icpt = np.polyfit(totals.new_filings, totals.ksi_per_crash, 1)
        xs = np.array([totals.new_filings.min(), totals.new_filings.max()])
        r1_fig.add_scatter(x=xs, y=slope * xs + icpt, mode="lines", line_color=ACCENT, showlegend=False)
        r1_fig.add_annotation(x=0.02, y=0.98, xref="paper", yref="paper", showarrow=False, bordercolor="gray", bgcolor="white",
                              font_color="black", text=f"Pearson r = {totals.new_filings.corr(totals.ksi_per_crash):.3f}")

    yoy = in_borough[in_borough.year.between(2022, 2026)].groupby(["borough", "year"]).ksi.sum().groupby("borough").diff().dropna().reset_index()
    yoy_fig = (px.line(yoy, x="year", y="ksi", facet_col="borough", facet_col_wrap=3, markers=True, color_discrete_sequence=[ACCENT],
                       labels={"ksi": "Year-over-year change", "year": ""})
               .add_hline(y=0, line_dash="dot").update_xaxes(dtick=1).for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1])))

    pair("Member 1 · Housing data",
         ("Neighborhoods with more building applications tend to have more serious harm per crash",
          "Do community districts with more new building applications have more severe crashes?", r1_fig,
          "Each dot is a neighborhood, 2022 to 2026. The link is modest and is not proof of cause. Borough, year, housing and district filters apply."),
         ("Serious harm fell in most boroughs from 2022 to 2024, then rose in 2025",
          "How does the year-over-year change in people killed or seriously hurt differ by borough?", yoy_fig,
          "2026 is a partial year, so its drop is not a real fall. Borough and harm filters apply."))

    c = by_borough(load("member2_transportation/rq_cd_panel.csv"))
    c = c.assign(log_new_units=np.log10(c.new_units.clip(lower=1)))
    c = c[c.history_known >= 50]
    overall = c.repeat_location.sum() / max(c.history_known.sum(), 1)
    repeat_fig = (px.scatter(c, x="new_units", y="repeat_share", hover_name="cd_label", color_discrete_sequence=[ACCENT],
                             hover_data=["new_filings", "history_known", "repeat_location"],
                             title=f"Spearman ρ = {spearman(c.new_units, c.repeat_share):.2f}",
                             labels={"new_units": "Total proposed new housing units",
                                     "repeat_share": "Share of crashes at<br>repeat-risk locations"})
                  .update_yaxes(tickformat=".0%")
                  .add_hline(y=overall, line_dash="dot", line_color="gray", annotation_text=f"Overall share: {overall:.1%}"))

    h = by_borough(load("member2_transportation/rq2_halves_panel.csv"))
    halves_fig = px.scatter(h, x="ksi_early", y="new_units_late", size="new_units_early", size_max=28, color="borough", hover_name="cd_label",
                            hover_data={"ksi_early": ":,.0f", "new_units_early": ":,.0f", "new_units_late": ":,.0f"},
                            title=(f"ρ = {spearman(h.ksi_early, h.new_units_late):.2f}; {partial_spearman(h.ksi_early, h.new_units_late, h.new_units_early):.2f} "
                                   "after controlling for earlier housing") if len(h) > 3 else None,
                            labels={"ksi_early": "KSI in the first half of the period",
                                    "new_units_late": "Proposed new housing units<br>in the second half", "new_units_early": "Proposed units in the first half", "borough": "Borough"})

    pair("Member 2 · Transportation data",
         ("Neighborhoods with more new housing have more crashes at spots that were already dangerous",
          "Do neighborhoods with more new housing have more crashes at spots that were already dangerous?", repeat_fig,
          "A spot counts as dangerous if a similar serious crash happened there in the previous 3 years. "
          "Dot size is the number of crashes. Neighborhoods with fewer than 50 crashes are left out. Only the borough filter applies."),
         ("New housing does not follow past serious crashes: it stays where it was already planned",
          "Is new housing being steered toward or away from neighborhoods with a record of serious crashes?", halves_fig,
          "Dot size is the housing planned in the first half; the first number in the chart title is the raw link, the second removes the effect of earlier housing. Once earlier housing is accounted for, the link with past harm almost disappears. "
          "Only the borough filter applies."))

    t = by_borough(load("member3_integration/cd_total.csv"))
    t = t.assign(ksi=t[col])
    both = set(t.nlargest(10, "new_units").cd_label) & set(t.nlargest(10, "ksi").cd_label)
    t["group"] = t.cd_label.map(lambda x: "Top 10 for both housing and harm" if x in both else "Other")
    t["label"] = t.cd_label.where(t.cd_label.isin(both), "")
    link_fig = (px.scatter(t, x="log_new_units", y="ksi", color="group", text="label", hover_name="cd_label",
                           color_discrete_map={"Top 10 for both housing and harm": ACCENT, "Other": GREY},
                           labels={"log_new_units": "New housing units (log scale: 2 = 100, 3 = 1,000, 4 = 10,000)", "ksi": HARM})
                .update_traces(textposition="top center"))

    q = in_borough.sort_values(["community_district", "year_month"])
    q["ksi_gap"] = q.ksi - q.groupby("community_district").ksi.transform("mean")
    lags = []
    for lag in range(7):
        f = q.groupby("community_district").new_filings.shift(lag)
        ok = f.notna()
        x = f[ok] - f[ok].groupby(q.community_district[ok]).transform("mean")
        lags.append({"months_after": lag, "link": x.corr(q.ksi_gap[ok], method="spearman")})
    lag_fig = (px.bar(pd.DataFrame(lags), x="months_after", y="link", color_discrete_sequence=[GREY],
                      labels={"months_after": "Months after the applications were filed", "link": "Link with serious<br>harm (0 = none)"})
               .update_yaxes(range=[-0.5, 0.5]))

    pair("Member 3 · Data integration",
         ("Neighborhoods with more new housing see somewhat more serious harm, but clearly so only in Manhattan",
          "Do neighborhoods with more new housing also have more people killed or seriously hurt?", link_fig,
          "Across all 59 neighborhoods the link is weak. Inside Manhattan it is strong; in the other boroughs it is not clear. "
          "Only 4 neighborhoods are in the top 10 for both new housing and serious harm. Borough and harm filters apply."),
         ("Serious crashes don't rise in the months after building applications are filed",
          "Are months with more building applications followed by more serious crashes in the same neighborhood?", lag_fig,
          "Each neighborhood is compared with its own usual level. Bars near 0 mean no link. Borough and harm filters apply."))

    r = d.groupby("borough")[["new_units", "ksi"]].sum()
    r = r[r.new_units > 0]
    r["per_1000"] = 1000 * r.ksi / r.new_units
    r = r.sort_values("per_1000").reset_index()
    r["top"] = r.per_1000 == r.per_1000.max()
    rate_fig = (px.bar(r, x="per_1000", y="borough", orientation="h", color="top", text=r.per_1000.round(1),
                       color_discrete_map={True: ACCENT, False: GREY},
                       labels={"per_1000": f"{HARM} per 1,000 new housing units", "borough": ""}).update_layout(showlegend=False))

    k = d.groupby(["cd_label", "borough"])[["new_filings", "new_units", "ksi"]].sum().reset_index()
    k = k[k.new_filings >= 5]
    k["units_per_filing"] = k.new_units / k.new_filings
    k["ksi_per_filing"] = k.ksi / k.new_filings
    k["label"] = k.cd_label.where(k.ksi_per_filing >= k.ksi_per_filing.nlargest(5).min(), "")
    size_fig = (px.scatter(k, x="units_per_filing", y="ksi_per_filing", text="label", hover_name="cd_label",
                           labels={"units_per_filing": "Average housing units per building application",
                                   "ksi_per_filing": f"{HARM}<br>per application"})
                .update_traces(textposition="top center", marker_color=ACCENT, textfont_color=ACCENT))

    pair("Member 4 · Research and story",
         ("Staten Island has the highest rate of people killed or seriously hurt per new housing unit",
          "Which boroughs have the most people killed or seriously hurt per new housing unit?", rate_fig,
          "Serious harm in each borough divided by its planned new housing units. Staten Island's rate rests on only 3 districts. All filters apply."),
         ("Neighborhoods with bigger projects tend to see more serious harm per application",
          "Do neighborhoods with bigger projects see more serious harm per building application?", size_fig,
          "Only neighborhoods with at least 5 applications are shown, since ratios from fewer are unreliable. All filters apply."))

    m = d.groupby(["borough", "year_month"])[["new_units", "ksi"]].sum().reset_index()
    for c_ in ["new_units", "ksi"]:
        smooth = m.groupby("borough")[c_].transform(lambda x: x.rolling(6, min_periods=1).mean())
        m[c_] = 100 * smooth / m.groupby("borough")[c_].transform("mean")
    m = m.melt(["borough", "year_month"], var_name="series", value_name="index")
    m["series"] = m.series.map({"new_units": "New units", "ksi": HARM})
    months_fig = (px.line(m, x="year_month", y="index", color="series", facet_col="borough", facet_col_wrap=1,
                          color_discrete_map={"New units": GREY, HARM: ACCENT}, labels={"index": "", "year_month": ""})
                  .for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
                  .update_layout(height=780, legend_orientation="h", legend_y=1.05))

    n = d.groupby("cd_label")[["new_units", "ksi"]].sum()
    cum = pd.DataFrame({name: 100 * n[c_].sort_values(ascending=False).cumsum().reset_index(drop=True) / n[c_].sum()
                        for c_, name in [("new_units", "New housing units"), ("ksi", HARM)]})
    cum.index += 1
    cum_fig = (px.line(cum, color_discrete_sequence=[ACCENT, GREY],
                       labels={"index": "Neighborhoods, from most to least", "value": "Cumulative share of the total (%)", "variable": ""})
               .add_hline(y=50, line_dash="dot").update_layout(height=780, legend_orientation="h", legend_y=1.05))

    pair("Member 5 · Website and filters",
         ("Busy building months are not the months with more serious crashes",
          "Do months with more planned housing also have more serious crashes?", months_fig,
          "Each line is smoothed over 6 months, and 100 is that borough's own average. Applications are plans, not finished buildings."),
         ("New housing is packed into fewer neighborhoods than serious crashes: half of it is in 13, half of the harm takes 22",
          "Is serious harm packed into a few neighborhoods the way new housing is?", cum_fig,
          "Neighborhoods are ranked from most to least, and each line is the running total. These are raw counts, not adjusted for population."))

        # --- MEMBER 6 CHARTS ---
    st.divider()
    st.header("Member 6 · Reports and deployment")
    
    # RQ1 Chart (Concentration)
    city_units = d.new_units.sum()
    city_ksi = d.ksi.sum()
    m6_t = d.groupby(["cd_label", "borough"]).agg(new_units=("new_units", "sum"), ksi=("ksi", "sum")).reset_index()
    m6_t["share_units"] = (m6_t["new_units"] / city_units) * 100 if city_units > 0 else 0
    m6_t["share_ksi"] = (m6_t["ksi"] / city_ksi) * 100 if city_ksi > 0 else 0

    m6_fig1 = px.scatter(
        m6_t, x="share_units", y="share_ksi", color="borough", hover_name="cd_label", size="new_units",
        labels={"share_units": "Share of NYC New Units (%)", "share_ksi": f"Share of NYC {HARM} (%)", "borough": "Borough"}
    ).add_hline(y=100/59, line_dash="dot", line_color="gray").add_vline(x=100/59, line_dash="dot", line_color="gray").update_layout(showlegend=False, margin=dict(t=30))

    # RQ2 Chart (YoY change 2022-2025)
    b_comp = in_borough[in_borough.year.isin([2022, 2025])]
    if len(b_comp.year.unique()) == 2:
        b_comp = b_comp.groupby(["borough", "year"]).agg(new_filings=("new_filings", "sum"), crashes=("crashes", "sum")).reset_index()
        b_pivot = b_comp.pivot(index="borough", columns="year", values=["new_filings", "crashes"]).reset_index()
        b_pivot.columns = ["borough", "filings_2022", "filings_2025", "crashes_2022", "crashes_2025"]
        b_pivot["filings_pct"] = ((b_pivot["filings_2025"] - b_pivot["filings_2022"]) / b_pivot["filings_2022"].replace(0, np.nan)) * 100
        b_pivot["crash_pct"] = ((b_pivot["crashes_2025"] - b_pivot["crashes_2022"]) / b_pivot["crashes_2022"].replace(0, np.nan)) * 100
        b_pivot = b_pivot.dropna(subset=["filings_pct", "crash_pct"])

        m6_fig2 = px.scatter(
            b_pivot, x="filings_pct", y="crash_pct", color="borough", text="borough",
            labels={"filings_pct": "Change in Filings (2022-2025) %", "crash_pct": "Change in Total Crashes (2022-2025) %", "borough": "Borough"}
        ).add_hline(y=0, line_dash="dot", line_color="gray").add_vline(x=0, line_dash="dot", line_color="gray").update_traces(textposition="top center").update_layout(showlegend=False, margin=dict(t=30))
    else:
        m6_fig2 = px.scatter(title="Please select 'All' Years in the sidebar to view the 2022-2025 comparison.")

    pair("Member 6 · Interactive Reports and Testing",
         ("New housing is highly concentrated, but serious crashes are more spread out across districts",
          "Do districts with a higher share of new housing also have a higher share of serious crashes?",
          m6_fig1,
          "Compares the % share of citywide units vs % share of citywide KSI. All filters apply to the data totals."),
         ("Boroughs with the biggest growth in housing filings did not necessarily see total crashes rise proportionally",
          "In boroughs where building filings increased most, did total crashes also increase proportionally?",
          m6_fig2,
          "Compares the percentage change from 2022 to 2025. Borough and year filters apply."))
    
with action:
    st.subheader("What to do next")
    cards([("1 · Check four neighborhoods first", "Queens 12, Brooklyn 1, Brooklyn 5 and Bronx 1 have a lot of new building and a lot of serious crashes."),
           ("2 · Look at high-crash areas with little building", "Neighborhoods such as Queens 7 and Brooklyn 18 have serious crashes that construction doesn't explain."),
           ("3 · Watch Staten Island", "It has the most serious crashes per new housing unit.")])

    # --- MEMBER 6 GENERATE REPORT LOGIC ---
    st.divider()
    st.subheader("Generated Report Summary")
    if st.session_state.get("show_report", False):
        st.success(f"Report Generated for: {borough} | {year} | {cd}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Housing Units Planned", f"{d.new_units.sum():,.0f}")
        col2.metric("Total New Building Applications", f"{d.new_filings.sum():,}")
        col3.metric(f"Total {HARM}", f"{d.ksi.sum():,}")
        
        st.write("You can download the filtered data below to use in your own reports:")
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=d.to_csv(index=False).encode('utf-8'),
            file_name=f'nyc_data_{borough}_{year}.csv',
            mime='text/csv',
        )
    else:
        st.info("Click the 'Generate Report' button in the sidebar to view a summary of the current filters and download data.")

    story = (HERE / "story.md").read_text(encoding="utf8")
    sections = {s.split("\n", 1)[0]: s.split("\n", 1)[1].strip() for s in story.split("\n## ")[1:]}
    bullets = lambda text: [escape(line[2:]) for line in text.splitlines() if line.startswith("- ")]

    st.subheader("The story")
    callout(escape(sections["The question"]))
    st.subheader("What we found")
    cards([(f"Finding {i}", b) for i, b in enumerate(bullets(sections["What we found"]), 1)])
    st.subheader("Limitations")
    cards([("", b) for b in bullets(sections["Limitations"])])
    st.subheader("Why it matters for NYC")
    callout(escape(sections["Why it matters for NYC"]))
