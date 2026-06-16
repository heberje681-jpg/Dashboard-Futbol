"""
⚽ Soccer Analytics — Team Performance Report
Source: football-data.org API — FREE tier (10 req/min, no credit card)
Get your free key at: e35cdcf868224099b728fa29f9ecebfd
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests, datetime

st.set_page_config(page_title="⚽ Soccer Analytics", page_icon="⚽", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
.stApp{background:#0d1117;color:#e6edf3;}
section[data-testid="stSidebar"]{background:#161b22;border-right:1px solid #21262d;}
section[data-testid="stSidebar"] *{color:#c9d1d9!important;}
h1,h2,h3{font-family:'IBM Plex Mono',monospace!important;color:#e6edf3!important;}
.kpi{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:14px 18px;text-align:center;}
.kpi-val{font-family:'IBM Plex Mono',monospace;font-size:26px;font-weight:600;color:#58a6ff;}
.kpi-lbl{font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:.08em;margin-top:3px;}
.kpi-sub{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#3fb950;margin-top:2px;}
.sec{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:.1em;border-bottom:1px solid #21262d;padding-bottom:6px;margin-bottom:14px;}
.stTabs [data-baseweb="tab-list"]{background:#161b22;border-bottom:1px solid #21262d;}
.stTabs [data-baseweb="tab"]{font-family:'IBM Plex Mono',monospace;font-size:12px;color:#8b949e;}
.stTabs [aria-selected="true"]{color:#58a6ff!important;}
.block-container{padding-top:1.5rem;}
div[data-testid="stSelectbox"] label,div[data-testid="stSlider"] label{color:#8b949e!important;font-size:11px!important;text-transform:uppercase;letter-spacing:.06em;}
.match-card{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:10px 16px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;}
</style>""", unsafe_allow_html=True)

PT = dict(paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="#c9d1d9",
          font_family="IBM Plex Sans",
          colorway=["#58a6ff","#3fb950","#f0883e","#d2a8ff","#ffa657"],
          xaxis=dict(gridcolor="#21262d",linecolor="#30363d"),
          yaxis=dict(gridcolor="#21262d",linecolor="#30363d"))

COMPETITIONS = {
    "Premier League 2024/25":          {"id":2021,"season":2024},
    "La Liga 2024/25":                  {"id":2014,"season":2024},
    "Bundesliga 2024/25":               {"id":2002,"season":2024},
    "Serie A 2024/25":                  {"id":2019,"season":2024},
    "Ligue 1 2024/25":                  {"id":2015,"season":2024},
    "Champions League 2024/25":         {"id":2001,"season":2024},
    "MLS 2025":                         {"id":2096,"season":2025},
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚽ Soccer Analytics")
    st.markdown("---")
    api_key = st.text_input("football-data.org API Key", type="password",
                             placeholder="Paste your free key here",
                             help="Free at football-data.org/client/register — takes 30 seconds")
    st.markdown("---")
    comp_name = st.selectbox("Competition", list(COMPETITIONS.keys()))
    comp = COMPETITIONS[comp_name]
    st.markdown("---")
    st.markdown('<div style="font-size:10px;color:#8b949e;">Get free key at:<br>football-data.org</div>', unsafe_allow_html=True)

if not api_key:
    st.markdown("# ⚽ Soccer Analytics Dashboard")
    st.markdown("""
    <div style="background:#161b22;border:1px solid #1f6feb;border-radius:10px;padding:24px 28px;margin-top:1rem;">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:15px;color:#58a6ff;margin-bottom:12px;">🔑 Setup — 30 seconds</div>
      <ol style="color:#c9d1d9;font-size:14px;line-height:2;">
        <li>Go to <a href="https://www.football-data.org/client/register" target="_blank" style="color:#58a6ff;">football-data.org/client/register</a></li>
        <li>Enter your email — free, no credit card</li>
        <li>Copy the API key from your email</li>
        <li>Paste it in the sidebar → done</li>
      </ol>
      <div style="font-size:12px;color:#8b949e;margin-top:12px;">✅ Free tier includes: Premier League, La Liga, Bundesliga, Serie A, MLS, Champions League</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── API helpers ────────────────────────────────────────────────────────────────
HEADERS = {"X-Auth-Token": api_key}

@st.cache_data(ttl=300, show_spinner=False)
def api(endpoint, params=None, key=None):
    try:
        r = requests.get(f"https://api.football-data.org/v4/{endpoint}",
                         headers={"X-Auth-Token": key or ""}, params=params, timeout=10)
        if r.status_code == 403:
            return {"error": "Invalid API key or competition not in free tier"}
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=300, show_spinner=False)
def load_standings(comp_id, season, key):
    data = api(f"competitions/{comp_id}/standings", {"season":season}, key)
    if "error" in data: return pd.DataFrame(), data["error"]
    rows = []
    for group in data.get("standings", []):
        if group.get("type") == "TOTAL":
            for t in group.get("table",[]):
                rows.append({
                    "Pos":  t["position"],
                    "Team": t["team"]["name"],
                    "P":    t["playedGames"],
                    "W":    t["won"],
                    "D":    t["draw"],
                    "L":    t["lost"],
                    "GF":   t["goalsFor"],
                    "GA":   t["goalsAgainst"],
                    "GD":   t["goalDifference"],
                    "Pts":  t["points"],
                    "Form": t.get("form",""),
                })
    return pd.DataFrame(rows), None

@st.cache_data(ttl=300, show_spinner=False)
def load_scorers(comp_id, season, key, limit=20):
    data = api(f"competitions/{comp_id}/scorers", {"season":season,"limit":limit}, key)
    if "error" in data: return pd.DataFrame(), data["error"]
    rows = []
    for s in data.get("scorers",[]):
        rows.append({
            "Player":    s["player"]["name"],
            "Team":      s["team"]["name"],
            "Goals":     s.get("goals",0),
            "Assists":   s.get("assists",0),
            "Penalties": s.get("penalties",0),
        })
    return pd.DataFrame(rows), None

@st.cache_data(ttl=120, show_spinner=False)
def load_matches(comp_id, season, key, status="FINISHED", limit=10):
    data = api(f"competitions/{comp_id}/matches", {"season":season,"status":status}, key)
    if "error" in data: return [], data["error"]
    matches = []
    for m in data.get("matches",[])[-limit:]:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        score = m.get("score",{})
        ft = score.get("fullTime",{})
        hg = ft.get("home","–")
        ag = ft.get("away","–")
        date = m.get("utcDate","")[:10]
        matches.append({"Date":date,"Home":home,"HG":hg,"AG":ag,"Away":away,
                        "Status":m.get("status","")})
    return list(reversed(matches)), None

# ── Main app ───────────────────────────────────────────────────────────────────
st.markdown(f"# ⚽ {comp_name}")
st.caption(f"Updated: {datetime.datetime.now().strftime('%H:%M:%S')}")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Standings","🥅 Top scorers","📅 Recent results","📈 Team analysis"])

with tab1:
    with st.spinner("Loading standings…"):
        df_st, err = load_standings(comp["id"], comp["season"], api_key)
    if err:
        st.error(f"API error: {err}")
    elif df_st.empty:
        st.warning("No standings data available yet.")
    else:
        c1,c2,c3,c4 = st.columns(4)
        leader = df_st.iloc[0]
        for col,label,val in [(c1,"Leader",leader["Team"]),(c2,"Points",str(leader["Pts"])),
                               (c3,"Goals For",str(leader["GF"])),(c4,"Goal Diff",f"+{leader['GD']}" if leader['GD']>0 else str(leader['GD']))]:
            with col:
                st.markdown(f'<div class="kpi"><div class="kpi-val">{val}</div><div class="kpi-lbl">{label}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Form color coding
        def color_form(form):
            if not form: return ""
            icons = {"W":"🟢","D":"🟡","L":"🔴"}
            return " ".join(icons.get(c,"⚪") for c in form.split(",") if c)

        df_st["Form_display"] = df_st["Form"].apply(color_form)
        st.dataframe(df_st[["Pos","Team","P","W","D","L","GF","GA","GD","Pts","Form_display"]].rename(columns={"Form_display":"Form"}),
                     use_container_width=True, hide_index=True,
                     column_config={"Pos":st.column_config.NumberColumn(width="small"),
                                    "Pts":st.column_config.NumberColumn(width="small")})

        st.markdown('<div class="sec" style="margin-top:1rem;">Points distribution</div>', unsafe_allow_html=True)
        top10 = df_st.head(10)
        fig = px.bar(top10, x="Team", y="Pts", color="Pts",
                     color_continuous_scale=["#1f3a5f","#58a6ff","#cae8ff"])
        fig.update_layout(**PT, height=320, coloraxis_showscale=False, margin=dict(l=0,r=0,t=10,b=0))
        fig.update_xaxes(tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    with st.spinner("Loading top scorers…"):
        df_sc, err = load_scorers(comp["id"], comp["season"], api_key)
    if err:
        st.error(f"API error: {err}")
    elif df_sc.empty:
        st.warning("No scorer data available.")
    else:
        c1,c2,c3 = st.columns(3)
        for col,i in zip([c1,c2,c3],[0,1,2]):
            if i < len(df_sc):
                r = df_sc.iloc[i]
                with col:
                    st.markdown(f'<div class="kpi"><div class="kpi-val">{r["Goals"]} ⚽</div><div class="kpi-lbl">#{i+1} top scorer</div><div class="kpi-sub">{r["Player"]}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        fig = make_subplots(rows=1,cols=2,subplot_titles=["Goals","Goals + Assists"])
        fig.add_trace(go.Bar(x=df_sc["Player"], y=df_sc["Goals"], marker_color="#58a6ff", name="Goals"), row=1,col=1)
        fig.add_trace(go.Bar(x=df_sc["Player"], y=df_sc["Goals"]+df_sc["Assists"].fillna(0), marker_color="#3fb950", name="G+A"), row=1,col=2)
        fig.update_layout(**PT, height=380, showlegend=False, margin=dict(l=0,r=0,t=40,b=0))
        fig.update_xaxes(tickangle=-40)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_sc, use_container_width=True, hide_index=True)

with tab3:
    with st.spinner("Loading recent matches…"):
        matches, err = load_matches(comp["id"], comp["season"], api_key, limit=15)
    if err:
        st.error(f"API error: {err}")
    elif not matches:
        st.info("No finished matches yet.")
    else:
        for m in matches:
            hg, ag = str(m["HG"]), str(m["AG"])
            home_w = hg.isdigit() and ag.isdigit() and int(hg) > int(ag)
            away_w = hg.isdigit() and ag.isdigit() and int(ag) > int(hg)
            hs = "color:#e6edf3;font-weight:600;" if home_w else "color:#8b949e;"
            as_ = "color:#e6edf3;font-weight:600;" if away_w else "color:#8b949e;"
            st.markdown(f"""
            <div class="match-card">
              <div style="font-size:11px;color:#8b949e;min-width:80px;">{m['Date']}</div>
              <div style="font-size:13px;{hs}text-align:right;flex:1;">{m['Home']}</div>
              <div style="font-family:'IBM Plex Mono',monospace;font-size:16px;color:#58a6ff;padding:0 16px;">{hg} – {ag}</div>
              <div style="font-size:13px;{as_}flex:1;">{m['Away']}</div>
            </div>""", unsafe_allow_html=True)

with tab4:
    with st.spinner("Loading data…"):
        df_st2, err = load_standings(comp["id"], comp["season"], api_key)
    if err or df_st2.empty:
        st.warning("Load standings first.")
    else:
        teams = df_st2["Team"].tolist()
        selected_teams = st.multiselect("Select teams to compare", teams, default=teams[:6])
        if selected_teams:
            sub = df_st2[df_st2["Team"].isin(selected_teams)]
            fig = go.Figure()
            metrics = ["W","D","L","GF","GA"]
            colors = ["#3fb950","#ffa657","#f0883e","#58a6ff","#d2a8ff"]
            for metric, color in zip(metrics, colors):
                fig.add_trace(go.Bar(name=metric, x=sub["Team"], y=sub[metric], marker_color=color))
            fig.update_layout(**PT, barmode="group", height=400, margin=dict(l=0,r=0,t=20,b=0))
            fig.update_xaxes(tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)

            # Attack vs Defense scatter
            st.markdown('<div class="sec">Attack vs Defense</div>', unsafe_allow_html=True)
            fig2 = px.scatter(sub, x="GA", y="GF", text="Team", color="Pts",
                              color_continuous_scale=["#1f3a5f","#58a6ff","#3fb950"],
                              size="Pts", size_max=30,
                              labels={"GA":"Goals Allowed","GF":"Goals Scored"})
            fig2.update_traces(textposition="top center", textfont_size=11)
            fig2.update_layout(**PT, height=420, margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig2, use_container_width=True)
