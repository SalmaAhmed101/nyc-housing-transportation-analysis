from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

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


@st.cache_data
def zip_surge():
    p = load("member1_housing/rq_panel_zip_month.csv").sort_values(["zip_code", "year_month"])
    p["ksi_next"] = sum(p.groupby("zip_code").ksi.shift(-k) for k in range(1, 7))
    p = p[p.year >= 2022]
    p["z"] = p.groupby("zip_code").new_building_filings.transform(lambda x: (x - x.mean()) / x.std())
    p["ratio"] = p.ksi_next / p.groupby("zip_code").ksi_next.transform("mean")
    p = p.replace([float("inf"), float("-inf")], float("nan")).dropna(subset=["z", "ratio"])
    inf = float("inf")
    p["activity"] = pd.cut(p.z, [-inf, -0.5, 0.5, 1.5, inf], labels=["Below usual", "Usual", "Above usual", "Surge"])
    return p


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
    st.button("Generate Report", disabled=True, help="Coming from Member 6")

col, HARM = SEVERITY[severity]
in_borough = in_borough.assign(ksi=in_borough[col])
d = in_borough[in_borough.is_large_pipeline_month] if housing == HOUSING[1] else in_borough
if year != "All":
    d = d[d.year == year]
if cd != "All":
    d = d[d.cd_label == cd]


def by_borough(frame):
    return frame if borough == "All" else frame[frame.borough == borough]


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
    z = by_borough(load("member1_housing/rq1_zip_changes.csv"))
    z_fig = px.scatter(z, x="filing_change", y="ksi_change", hover_name="zip_code", color_discrete_sequence=[GREY],
                       labels={"filing_change": "Change in building applications (2023 to 2024)",
                               "ksi_change": "Change in people killed or<br>seriously hurt (2023 to 2024)"}).add_hline(y=0, line_dash="dot")

    s = by_borough(zip_surge())
    s = s if year == "All" else s[s.year == year]
    g = s.groupby("activity", observed=True).ratio.agg(["mean", "sem", "count"]).reset_index()
    g["ci"] = 1.96 * g["sem"]
    g["surge"] = g.activity.eq("Surge")
    surge_fig = (px.bar(g, x="activity", y="mean", error_y="ci", color="surge", text=g["count"].map("n={:,}".format),
                        color_discrete_map={True: ACCENT, False: GREY},
                        labels={"activity": "Applications that month vs the ZIP's usual",
                                "mean": "Serious harm in the next<br>6 months (1 = usual)"})
                 .add_hline(y=1, line_dash="dot").update_traces(insidetextanchor="middle").update_layout(showlegend=False))

    pair("Member 1 · Housing data",
         ("ZIP codes where building applications grew did not see serious harm grow",
          "Did ZIP codes with more new building applications see a bigger change in serious harm?", z_fig,
          "Each dot is a ZIP code. Fixed to 2023 vs 2024, the two full years. Only the borough filter applies."),
         ("After a surge in building applications, serious harm stays at its usual level",
          "After a month with unusually many applications, does serious harm rise over the next 6 months?", surge_fig,
          "Each ZIP code is compared with its own usual level, so busy areas don't skew the result. Borough and year filters apply."))

    c = by_borough(load("member2_transportation/rq_cd_panel.csv"))
    repeat_fig = (px.scatter(c[c.history_known >= 50], x="log_new_units", y="repeat_share", size="history_known", hover_name="cd_label",
                             color_discrete_sequence=[ACCENT],
                             labels={"log_new_units": "New housing units (log scale: 2 = 100, 3 = 1,000, 4 = 10,000)",
                                     "repeat_share": "Share of crashes at spots<br>with a serious-crash history"})
                  .update_yaxes(tickformat=".0%"))

    w = by_borough(load("member2_transportation/rq2_crashes_by_tier.csv"))
    w = w if year == "All" else w[w.year == year]
    if cd != "All":
        w = w[w.community_district == df.loc[df.cd_label == cd, "community_district"].iloc[0]]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    tiers = ["Lower development", "Higher development"]
    grids = []
    for tier in tiers:
        grid = w[w.dev_tier == tier].groupby(["weekday", "hour"]).size().unstack(fill_value=0)
        grid = grid.reindex(index=days, columns=range(24), fill_value=0)
        grids.append(100 * grid / max(grid.values.sum(), 1))
    heat_fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.14,
                             subplot_titles=[f"{t} (n={(w.dev_tier == t).sum():,} crashes)" for t in tiers])
    for i, grid in enumerate(grids, 1):
        heat_fig.add_trace(go.Heatmap(z=grid.values, x=list(range(24)), y=days, zmin=0, zmax=max(g_.values.max() for g_ in grids),
                                      colorscale="Oranges", showscale=i == 2, colorbar={"title": "% of crashes"},
                                      hovertemplate="%{y} %{x}:00<br>%{z:.2f}% of crashes<extra></extra>"), row=i, col=1)
    heat_fig.update_xaxes(title_text="Hour of day", dtick=3, row=2, col=1)
    heat_fig.update_yaxes(autorange="reversed").update_layout(height=620)

    pair("Member 2 · Transportation data",
         ("Neighborhoods with more new housing have more crashes at spots that were already dangerous",
          "Do neighborhoods with more new housing have more crashes at spots that were already dangerous?", repeat_fig,
          "A spot counts as dangerous if a similar serious crash happened there in the previous 3 years. "
          "Dot size is the number of crashes. Neighborhoods with fewer than 50 crashes are left out. Only the borough filter applies."),
         ("Serious crashes happen at the same times of the week, whether or not a neighborhood is building a lot",
          "Do serious crashes happen at different times of the week in neighborhoods that are building a lot?", heat_fig,
          "Neighborhoods are split in half by how much new housing they have. Each square is the share of that half's crashes. "
          "Borough, year and district filters apply."))

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
         ("Staten Island has the most serious crashes for each new housing unit",
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

    st.divider()
    st.header("Member 6 · Reports and deployment")
    for column, n in zip(st.columns(2), (1, 2)):
        column.info(f"**Question {n}:** chart goes here. At least one of Member 6's charts links housing and transportation.")

with action:
    st.subheader("What to do next")
    cards([("1 · Check four neighborhoods first", "Queens 12, Brooklyn 1, Brooklyn 5 and Bronx 1 have a lot of new building and a lot of serious crashes."),
           ("2 · Look at high-crash areas with little building", "Neighborhoods such as Queens 7 and Brooklyn 18 have serious crashes that construction doesn't explain."),
           ("3 · Watch Staten Island", "It has the most serious crashes per new housing unit.")])

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
