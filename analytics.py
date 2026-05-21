import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import os
from xhtml2pdf import pisa

def show_analytics(df_agent):
    st.subheader("📈 Statistical Analysis & Reports")
    
    ch1, ch2 = st.columns(2)
    with ch1:
        st.write("#### Energy Intensity Distribution")
        f1 = px.bar(df_agent, x="PrimaryPropertyType", y="SiteEUI(kBtu/sf)", color="SBC_Status", barmode="group",
                    color_discrete_map={"Compliant": "#00ff87", "Non-Compliant": "#ff4b4b"}, template="plotly_dark")
        st.plotly_chart(f1, use_container_width=True)
        
    with ch2:
        st.write("#### Carbon Footprint Relative to Size")
        f2 = px.scatter(df_agent, x="PropertyGFATotal", y="CO2_Emissions_kg", size="SiteEUI(kBtu/sf)", color="Risk_Level",
                        color_discrete_map={"Low Risk": "#00ff87", "Medium Risk": "#00adb5", "High Risk": "#ff4b4b"}, template="plotly_dark")
        st.plotly_chart(f2, use_container_width=True)
        
    st.markdown("---")
    
    fig, ax = plt.subplots(figsize=(6, 3))
    sns.countplot(data=df_agent, x="Action_Priority", palette=["#00ff87", "#00adb5", "#ff4b4b"], ax=ax)
    plt.title("Action Priority Distribution", color="black")
    fig.savefig("analytics_chart.png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    
    with open("analytics_chart.png", "rb") as img_file:
        st.download_button(label="📥 Download Generated Analytics Chart (PNG)", data=img_file, file_name="EcoVolt_Priority_Dist.png", mime="image/png")

    st.subheader("📋 Executive Sustainability Report (PDF)")
    
    f1.update_layout(paper_bgcolor="#121820", plot_bgcolor="#121820")
    f2.update_layout(paper_bgcolor="#121820", plot_bgcolor="#121820")
    
    f1.write_image("temp_chart1.png", width=700, height=350, scale=2)
    f2.write_image("temp_chart2.png", width=700, height=350, scale=2)
    
    with open("temp_chart1.png", "rb") as f: c1_b64 = base64.b64encode(f.read()).decode('utf-8')
    with open("temp_chart2.png", "rb") as f: c2_b64 = base64.b64encode(f.read()).decode('utf-8')
    
    html_report = f"""
    <!DOCTYPE html><html><head><style>
        @page {{ size: a4; margin: 2cm; background-color: #0b0f14; }}
        body {{ font-family: sans-serif; color: #ffffff; }}
        .header {{ border-bottom: 2px solid #1f293d; padding-bottom: 15px; margin-bottom: 30px; }}
        .title {{ color: #00f2fe; font-size: 24px; font-weight: bold; }}
        .chart-box {{ background-color: #121820; border: 1px solid #1f293d; padding: 10px; margin: 15px 0; }}
    </style></head><body>
        <div class="header"><div class="title">📋 Executive Analytics Report — EcoVolt</div></div>
        <div class="chart-box"><img src="data:image/png;base64,{c1_b64}" style="width:100%;"></div>
        <div class="chart-box"><img src="data:image/png;base64,{c2_b64}" style="width:100%;"></div>
    </body></html>
    """
    
    with open("EcoVolt_Executive_Report.pdf", "w+b") as result_file:
        pisa.pisaDocument(html_report, dest=result_file)
    
    if os.path.exists("temp_chart1.png"): os.remove("temp_chart1.png")
    if os.path.exists("temp_chart2.png"): os.remove("temp_chart2.png")

    with open("EcoVolt_Executive_Report.pdf", "rb") as pdf_file:
        st.download_button("📥 Download PDF Report", pdf_file, "EcoVolt_Sustainability_Report.pdf", mime="application/pdf")