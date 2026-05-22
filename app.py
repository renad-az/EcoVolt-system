import os
import base64
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

try:
    import joblib
    JOBLIB_OK = True
except ImportError:
    JOBLIB_OK = False

from agent import get_agent_response

# ─────────────────────────────────────────
# إعدادات الصفحة
# ─────────────────────────────────────────
st.set_page_config(
    page_title="EcoVolt – Intelligent Energy Agent",
    page_icon="⚡",
    layout="wide",
)

# ─────────────────────────────────────────
# CSS الثيم الكامل
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Space+Mono:wght@400;700&display=swap');

.main, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #0a1628 !important;
    background-image:
        radial-gradient(ellipse 60% 50% at 10% 10%, rgba(0,200,150,0.07) 0%, transparent 60%),
        radial-gradient(ellipse 50% 40% at 90% 90%, rgba(0,173,181,0.06) 0%, transparent 60%) !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stSidebar"] { background-color: #0d1f35 !important; }
[data-testid="stHeader"], .stDeployButton { display: none !important; }
[data-testid="stMainBlockContainer"] {
    padding-top: 0.5rem !important;
    padding-bottom: 1rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
}
[data-testid="stImage"] img {
    max-height: 130px !important;
    object-fit: contain !important;
}
h1, h2, h3, h4, h5 {
    color: #ffffff !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stButton > button {
    background: linear-gradient(135deg, #00c896, #00adb5) !important;
    color: #0a1628 !important;
    border-radius: 25px !important;
    font-weight: 600 !important;
    border: none !important;
    padding: 0.5rem 2rem !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #00ff87, #00d4aa) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 20px rgba(0,200,150,0.4) !important;
}

/* Navigation Pills */
div[data-testid="stRadio"] > div {
    display: flex !important;
    flex-direction: row !important;
    gap: 8px !important;
    flex-wrap: wrap !important;
    background: transparent !important;
}
div[data-testid="stRadio"] label {
    background-color: rgba(13,32,64,0.9) !important;
    color: #8ba5c4 !important;
    padding: 8px 22px !important;
    border-radius: 50px !important;
    border: 1px solid rgba(0,200,150,0.25) !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}
div[data-testid="stRadio"] label [data-testid="stWidgetCaption"] { display: none !important; }
div[data-testid="stRadio"] [data-baseweb="radio"] > div:first-child { display: none !important; }
div[data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(135deg, #00c896, #00adb5) !important;
    color: #0a1628 !important;
    border-color: transparent !important;
    font-weight: 700 !important;
}

/* Cards */
.ev-card {
    background: linear-gradient(145deg, #0d2040, #0a1a35);
    padding: 28px;
    border-radius: 20px;
    min-height: 200px;
    border: 1px solid rgba(0,200,150,0.2);
    transition: transform 0.3s, border-color 0.3s, box-shadow 0.3s;
    height: 100%;
}
.ev-card:hover {
    transform: translateY(-5px);
    border-color: rgba(0,255,135,0.5);
    box-shadow: 0 8px 30px rgba(0,200,150,0.13);
}
.ev-card-icon  { font-size: 30px; margin-bottom: 14px; display: block; }
.ev-card-title { color: #ffffff; font-size: 19px; font-weight: 600; margin-bottom: 8px; }
.ev-card-text  { color: #8ba5c4; font-size: 13px; line-height: 1.65; }

/* Metrics */
[data-testid="metric-container"] {
    background-color: #0d2040 !important;
    border: 1px solid rgba(0,200,150,0.2) !important;
    border-radius: 15px !important;
    padding: 15px !important;
}
[data-testid="stMetricValue"] { color: #00ff87 !important; font-family: 'Space Mono', monospace !important; }
[data-testid="stMetricLabel"] { color: #8ba5c4 !important; }

/* Chat */
[data-testid="stChatMessageContainer"] { direction: rtl !important; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
    text-align: right !important;
    direction: rtl !important;
}
[data-testid="stChatInput"] textarea {
    direction: rtl !important;
    text-align: right !important;
    background-color: #0d2040 !important;
    border: 1px solid rgba(0,200,150,0.3) !important;
    color: #ffffff !important;
    border-radius: 15px !important;
}
[data-testid="stChatMessage"] { flex-direction: row-reverse !important; }

/* Inputs */
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input {
    background-color: #0d2040 !important;
    border: 1px solid rgba(0,200,150,0.3) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
}
[data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden !important; }
hr { border-color: rgba(0,200,150,0.15) !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# Plotly dark theme helper
# ─────────────────────────────────────────
DARK_LAYOUT = dict(
    paper_bgcolor="#0d2040",
    plot_bgcolor="#0d2040",
    font_color="#8ba5c4",
    title_font_color="#ffffff",
    legend_font_color="#8ba5c4",
)
COLOR_SBC  = {"Compliant": "#00ff87", "Non-Compliant": "#ff4b4b"}
COLOR_RISK = {"Low Risk": "#00ff87", "Medium Risk": "#00adb5", "High Risk": "#ff4b4b"}

# ─────────────────────────────────────────
# اللوقو
# ─────────────────────────────────────────
logo_candidates = ["logo.png", os.path.join("Sec", "logo.png"), os.path.join("assets", "logo.png")]
logo_path = next((p for p in logo_candidates if os.path.exists(p)), None)

if logo_path:
    _, col_logo, _ = st.columns([0.8, 3, 0.8])
    with col_logo:
        st.image(logo_path, use_container_width=True)
else:
    st.markdown(
        "<h1 style='text-align:center;color:#00ff87;font-family:Space Mono,monospace;margin-bottom:4px'>⚡ EcoVolt</h1>"
        "<p style='text-align:center;color:#8ba5c4;font-size:13px;letter-spacing:2px;margin-top:0'>INTELLIGENT ENERGY AGENT</p>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────
# تحميل البيانات
# ─────────────────────────────────────────
INPUT_FILE = os.path.join("data", "processed", "agent_results.csv")
MODEL_FILE = os.path.join("models", "compliance_model.pkl")

if os.path.exists(INPUT_FILE):
    df_agent = pd.read_csv(INPUT_FILE)
else:
    df_agent = pd.DataFrame({
        "PrimaryPropertyType":  ["Office", "Hotel", "Warehouse", "Office", "School", "Hospital"],
        "PropertyGFATotal":     [55000, 78000, 110000, 32000, 46000, 95000],
        "SiteEUI(kBtu/sf)":     [72.1, 98.4, 42.0, 120.5, 58.2, 145.0],
        "SiteEnergyUse(kBtu)":  [3965000, 7675200, 4620000, 3856000, 2677200, 13775000],
        "CO2_Emissions_kg":     [14200, 29100, 10500, 24300, 9100, 48000],
        "SBC_Status":           ["Compliant", "Non-Compliant", "Compliant", "Non-Compliant", "Compliant", "Non-Compliant"],
        "Risk_Level":           ["Low Risk", "Medium Risk", "Low Risk", "High Risk", "Low Risk", "High Risk"],
        "Exceedance_Percentage":[0, 18, 0, 48, 0, 65],
        "Action_Priority":      ["Monitor", "Action Recommended", "Monitor", "Urgent Action Required", "Monitor", "Urgent Action Required"],
        "Agent_Explanation":    [
            "Compliant building.",
            "Medium risk. Optimize HVAC.",
            "Compliant.",
            "High risk. Immediate audit required.",
            "Compliant.",
            "Critical risk. Retrofitting needed.",
        ],
    })

# ─────────────────────────────────────────
# التنقل
# ─────────────────────────────────────────
st.markdown(
    "<h4 style='color:#ffffff;margin-bottom:20px;font-size:26px;font-weight:600;'>"
    "Unified Platform Interface</h4>",
    unsafe_allow_html=True,
)
TABS = ["Overview", "AI Chat Agent", "Dashboard", "Predictive Engine", "Analytics"]
selected = st.radio("nav", TABS, horizontal=True, label_visibility="collapsed")
st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════
# 1 ▸ Overview
# ══════════════════════════════════════════
if selected == "Overview":
    c1, c2, c3 = st.columns(3, gap="large")
    for col, (icon, color, title, body) in zip([c1, c2, c3], [
        ("🤖", "#00adb5", "AI Agent",
         "Real-time conversational interface to query buildings, legal frameworks, and consumption metadata."),
        ("📊", "#00ff87", "Smart Dashboard",
         "Digitized data visualized into KPIs for Savings, Carbon Footprint, Compliance, and Alerts."),
        ("⚙️", "#00f2fe", "Predictive Engine",
         "Forecasting energy demand using Regression/Classification models and LLM-driven recommendations."),
    ]):
        with col:
            st.markdown(
                f"<div class='ev-card'>"
                f"<span class='ev-card-icon' style='color:{color}'>{icon}</span>"
                f"<div class='ev-card-title'>{title}</div>"
                f"<div class='ev-card-text'>{body}</div>"
                f"</div>", unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📌 Key Metrics at a Glance")

    total   = len(df_agent)
    comply  = len(df_agent[df_agent["SBC_Status"] == "Compliant"])                           if "SBC_Status"       in df_agent.columns else 0
    urgent  = len(df_agent[df_agent["Action_Priority"] == "Urgent Action Required"])         if "Action_Priority"  in df_agent.columns else 0
    co2_tot = int(df_agent["CO2_Emissions_kg"].sum())                                        if "CO2_Emissions_kg" in df_agent.columns else 0
    avg_eui = round(df_agent["SiteEUI(kBtu/sf)"].mean(), 1)                                 if "SiteEUI(kBtu/sf)" in df_agent.columns else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Buildings",    total)
    m2.metric("Compliant ✅",       comply, delta=f"{round(comply/total*100)}%" if total else None)
    m3.metric("Non-Compliant ⚠️",  total - comply)
    m4.metric("Urgent 🚨",          urgent)
    m5.metric("Total CO₂ (kg)",     f"{co2_tot:,}")


# ══════════════════════════════════════════
# 2 ▸ AI Chat Agent
# ══════════════════════════════════════════
elif selected == "AI Chat Agent":
    st.subheader("🤖 EcoVolt Conversational Chat Agent")

    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": (
                "أرحبِ! يا هلا ومسهلا بك في مستشارك الذكي إيكوفولت ⚡ "
                "البيانات والأرقام قدامي وأمورنا زين الحمد لله، "
                "سمّي وش بغيتِ تسألين عنه في المباني والامتثال؟"
            ),
        }]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_input := st.chat_input("اكتبي سؤالك هنا..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            reply = get_agent_response(user_input, df_agent)
            placeholder.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})


# ══════════════════════════════════════════
# 3 ▸ Dashboard
# ══════════════════════════════════════════
elif selected == "Dashboard":
    st.subheader("📊 Smart Energy Dashboard")

    total  = len(df_agent)
    comply = len(df_agent[df_agent["SBC_Status"] == "Compliant"])                   if "SBC_Status"      in df_agent.columns else 0
    urgent = len(df_agent[df_agent["Action_Priority"] == "Urgent Action Required"]) if "Action_Priority" in df_agent.columns else 0
    co2    = int(df_agent["CO2_Emissions_kg"].sum())                                 if "CO2_Emissions_kg" in df_agent.columns else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Buildings", total)
    k2.metric("Compliant",       comply, delta=f"{round(comply/total*100)}%" if total else None)
    k3.metric("Urgent Action",   urgent)
    k4.metric("Total CO₂ (kg)", f"{co2:,}")

    st.markdown("---")
    ch1, ch2 = st.columns(2)

    with ch1:
        if "SBC_Status" in df_agent.columns:
            fig = px.pie(df_agent, names="SBC_Status", title="SBC Compliance Distribution",
                         color="SBC_Status", color_discrete_map=COLOR_SBC, hole=0.45, template="plotly_dark")
            fig.update_layout(**DARK_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

    with ch2:
        if "Action_Priority" in df_agent.columns:
            fig2 = px.bar(df_agent["Action_Priority"].value_counts().reset_index(),
                          x="Action_Priority", y="count", title="Action Priority Distribution",
                          color="Action_Priority",
                          color_discrete_sequence=["#00ff87", "#00adb5", "#ff4b4b"],
                          template="plotly_dark")
            fig2.update_layout(**DARK_LAYOUT)
            st.plotly_chart(fig2, use_container_width=True)

    if "Risk_Level" in df_agent.columns and "CO2_Emissions_kg" in df_agent.columns:
        fig3 = px.bar(df_agent, x="PrimaryPropertyType", y="CO2_Emissions_kg",
                      color="Risk_Level", title="CO₂ Emissions by Property Type & Risk Level",
                      color_discrete_map=COLOR_RISK, barmode="group", template="plotly_dark")
        fig3.update_layout(**DARK_LAYOUT)
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("### 📋 Full Data Table")
    st.dataframe(df_agent, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════
# 4 ▸ Predictive Engine
# ══════════════════════════════════════════
elif selected == "Predictive Engine":
    st.subheader("🔮 Predictive Compliance Engine")

    col_l, col_r = st.columns(2)
    with col_l:
        ptype = st.selectbox("Property Type", df_agent["PrimaryPropertyType"].unique())
        gfa   = st.number_input("Property GFA (sf)",       min_value=0,   value=60000)
        eui   = st.number_input("Site EUI (kBtu/sf)",      min_value=0.0, value=80.0, step=0.1)
    with col_r:
        use   = st.number_input("Total Energy Use (kBtu)", min_value=0,   value=4000000, step=10000)
        co2   = st.number_input("CO₂ Emissions (kg)",      min_value=0,   value=18000,   step=100)

    if st.button("🚀 Run ML Compliance Forecast"):
        input_df = pd.DataFrame([{
            "PrimaryPropertyType": ptype,
            "PropertyGFATotal":    gfa,
            "SiteEUI(kBtu/sf)":    eui,
            "SiteEnergyUse(kBtu)": use,
            "CO2_Emissions_kg":    co2,
        }])
        input_df = input_df.replace([np.inf, -np.inf], np.nan).fillna(0)

        is_empty    = (eui == 0 or co2 == 0 or gfa == 0)
        is_critical = (eui > 120 or co2 > 40000)
        result = "Non-Compliant"

        if JOBLIB_OK and os.path.exists(MODEL_FILE):
            try:
                model = joblib.load(MODEL_FILE)
                pred  = model.predict(input_df)[0]
                if (pred in ("Compliant", 0)) and not is_empty and not is_critical:
                    result = "Compliant"
            except Exception:
                result = "Non-Compliant" if (is_empty or is_critical) else "Compliant"
        else:
            result = "Non-Compliant" if (is_empty or is_critical) else "Compliant"

        if result == "Compliant":
            st.success(f"🎉 Model Forecast: **{result}** — This building meets SBC requirements.")
        else:
            st.error(f"⚠️ Model Forecast: **{result}** — Immediate review and corrective action required.")


# ══════════════════════════════════════════
# 5 ▸ Analytics
# ══════════════════════════════════════════
elif selected == "Analytics":
    st.subheader("📈 Statistical Analysis & Reports")

    ch1, ch2 = st.columns(2)
    with ch1:
        st.write("#### Energy Intensity Distribution")
        f1 = px.bar(df_agent, x="PrimaryPropertyType", y="SiteEUI(kBtu/sf)", color="SBC_Status",
                    barmode="group", color_discrete_map=COLOR_SBC, template="plotly_dark")
        f1.update_layout(**DARK_LAYOUT)
        st.plotly_chart(f1, use_container_width=True)

    with ch2:
        st.write("#### Carbon Footprint vs. Building Size")
        f2 = px.scatter(df_agent, x="PropertyGFATotal", y="CO2_Emissions_kg",
                        size="SiteEUI(kBtu/sf)", color="Risk_Level",
                        color_discrete_map=COLOR_RISK, template="plotly_dark")
        f2.update_layout(**DARK_LAYOUT)
        st.plotly_chart(f2, use_container_width=True)

    st.markdown("---")

    # Seaborn chart
    fig_sns, ax = plt.subplots(figsize=(7, 3))
    fig_sns.patch.set_facecolor("#0d2040")
    ax.set_facecolor("#0d2040")
    if "Action_Priority" in df_agent.columns:
        sns.countplot(data=df_agent, x="Action_Priority",
                      palette=["#00ff87", "#00adb5", "#ff4b4b"], ax=ax)
    ax.tick_params(colors="#8ba5c4")
    ax.set_title("Action Priority Distribution", color="#ffffff")
    for spine in ax.spines.values():
        spine.set_edgecolor("#1f3a5f")
    plt.tight_layout()
    chart_path = "analytics_chart.png"
    fig_sns.savefig(chart_path, bbox_inches="tight", dpi=150, facecolor="#0d2040")
    plt.close(fig_sns)

    with open(chart_path, "rb") as img_file:
        st.download_button(
            label="📥 Download Priority Chart (PNG)",
            data=img_file,
            file_name="EcoVolt_Priority_Distribution.png",
            mime="image/png",
        )

    st.markdown("---")
    st.subheader("📋 Executive Sustainability Report (PDF)")

    def generate_pdf_report():
        try:
            from xhtml2pdf import pisa
        except ImportError:
            return None
        try:
            f1.write_image("_tmp1.png", width=700, height=350, scale=2)
            f2.write_image("_tmp2.png", width=700, height=350, scale=2)
        except Exception:
            return None

        def b64(p):
            with open(p, "rb") as fh:
                return base64.b64encode(fh.read()).decode()

        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
body{{font-family:Helvetica,Arial,sans-serif;color:#fff;background:#0a1628;margin:0;padding:20px}}
.title{{color:#00c896;font-size:22px;font-weight:bold;border-bottom:2px solid #1f3a5f;padding-bottom:10px;margin-bottom:20px}}
.sec{{color:#00ff87;font-size:15px;font-weight:bold;border-left:4px solid #00ff87;padding-left:8px;margin:20px 0 10px}}
.box{{background:#0d2040;border:1px solid #1f3a5f;border-radius:8px;padding:8px;margin-bottom:12px;text-align:center}}
.note{{background:rgba(0,200,150,0.04);border:1px solid rgba(0,200,150,0.15);border-radius:8px;padding:12px;font-size:12px;line-height:1.6}}
</style></head><body>
<div class="title">📋 Executive Analytics Report — EcoVolt</div>
<div class="sec">1. Energy Intensity Distribution</div>
<div class="box"><img src="data:image/png;base64,{b64('_tmp1.png')}" style="width:100%"></div>
<div class="note"><strong>AI Insight:</strong> Hospitality and Healthcare assets record highest EUI. Prioritized retrofitting and HVAC tuning recommended to meet SBC targets.</div>
<div class="sec">2. Carbon Footprint vs. Building Size</div>
<div class="box"><img src="data:image/png;base64,{b64('_tmp2.png')}" style="width:100%"></div>
<div class="note"><strong>AI Insight:</strong> Direct correlation between GFA and CO₂ emissions. High-risk properties cluster at larger floor areas — intelligent insulation solutions advised.</div>
</body></html>"""

        pdf_path = "EcoVolt_Executive_Report.pdf"
        with open(pdf_path, "w+b") as out:
            pisa.pisaDocument(html, dest=out)
        for tmp in ["_tmp1.png", "_tmp2.png"]:
            if os.path.exists(tmp):
                os.remove(tmp)
        with open(pdf_path, "rb") as pf:
            return pf.read()

    pdf_bytes = generate_pdf_report()
    if pdf_bytes:
        col_i, col_d = st.columns([3, 1])
        col_i.info("📄 Executive PDF report generated and ready for download.")
        col_d.download_button(
            label="📥 Download PDF Report",
            data=pdf_bytes,
            file_name="EcoVolt_Sustainability_Report.pdf",
            mime="application/pdf",
        )
    else:
        st.warning("⚠️ PDF generation requires `xhtml2pdf` and `kaleido`. Run: `pip install xhtml2pdf kaleido`")