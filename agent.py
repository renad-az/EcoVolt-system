import os
import time
import requests
import pandas as pd
import streamlit as st

# ─── مفتاح Gemini: يقرأ من .env أو متغير البيئة ───
api_key = st.secrets.get("GEMINI_API_KEY", "")

def get_agent_response(user_input: str, df_agent: pd.DataFrame) -> str:
    query = user_input.strip().lower()

    # 1. رد السلام
    if any(w in query for w in ["السلام", "سلام", "عليكم", "هلا", "مرحبا", "مرحباً", "حياك", "صباح", "مساء"]):
        return (
            "وعليكم السلام ورحمة الله وبركاته، ويا هلا ومسهلا! ⚡ "
            "أرحبِ في مستشار إيكوفولت الذكي. "
            "البيانات والأرقام قدامي وأمورنا زين الحمد لله، سمّي وش بغيتِ تسألين عنه؟ "
            "أقدر أطلع لك المباني عالية الخطورة، أو أعطيكِ ملخص حالة الامتثال، "
            "أو تحليل وتوصيات شاملة للمشروع."
        )

    # 2. المباني عالية الخطورة
    elif any(w in query for w in ["خطورة", "عالي", "عالية", "urgent", "high risk", "عاجل"]):
        if "Action_Priority" in df_agent.columns:
            high_risk = df_agent[df_agent["Action_Priority"] == "Urgent Action Required"]
            if not high_risk.empty:
                reply = f"🚨 **سويت لك فحص سريع ولقيت {len(high_risk)} منشآت تتطلب تدخل عاجل:**\n\n"
                for _, row in high_risk.iterrows():
                    reply += (
                        f"- **نوع المبنى:** {row['PrimaryPropertyType']} | "
                        f"**EUI:** `{row['SiteEUI(kBtu/sf)']}` "
                        f"(تجاوز: {row['Exceedance_Percentage']}%)\n"
                    )
                reply += "\n💡 *الشور الهندسي: جولة تدقيق طاقة ميدانية لهذه المباني بأسرع وقت.*"
                return reply
            return "✅ ما فيه أي مبنى في نطاق الخطورة العالية حالياً."
        return "⚠️ عمود Action_Priority مهوب موجود في البيانات."

    # 3. ملخص الامتثال
    elif any(w in query for w in ["حالة", "ملخص", "امتثال", "status", "summary", "كود", "sbc"]):
        if "SBC_Status" in df_agent.columns:
            stats     = df_agent["SBC_Status"].value_counts()
            total     = len(df_agent)
            compliant = stats.get("Compliant", 0)
            non_c     = stats.get("Non-Compliant", 0)
            pct       = round(compliant / total * 100) if total else 0
            reply  = "📊 **ملخص حالة الامتثال لكود البناء السعودي (SBC):**\n\n"
            reply += f"- ✅ الممتثلة: `{compliant}` مباني\n"
            reply += f"- ⚠️ المخالفة: `{non_c}` مباني\n"
            reply += f"- 📈 نسبة الامتثال: `{pct}%`\n"
            if non_c > 0:
                reply += "\n💡 *المباني المخالفة تحتاج مراجعة فورية لأنظمة التكييف والعزل الحراري.*"
            return reply
        return "📊 عمود SBC_Status مهوب متوفر في البيانات."

    # 4. انبعاثات الكربون
    elif any(w in query for w in ["كربون", "انبعاث", "co2", "بيئة", "carbon"]):
        if "CO2_Emissions_kg" in df_agent.columns:
            total_co2 = df_agent["CO2_Emissions_kg"].sum()
            top3 = df_agent.nlargest(3, "CO2_Emissions_kg")[["PrimaryPropertyType", "CO2_Emissions_kg"]]
            reply  = f"🌿 **تقرير انبعاثات الكربون:**\n\n"
            reply += f"- إجمالي الانبعاثات: `{total_co2:,.0f}` كجم CO₂\n\n"
            reply += "**أعلى 3 مباني:**\n"
            for _, row in top3.iterrows():
                reply += f"- {row['PrimaryPropertyType']}: `{row['CO2_Emissions_kg']:,.0f}` كجم\n"
            reply += "\n💡 *تركيب ألواح شمسية وتحسين التكييف يخفض الانبعاثات 25-40%.*"
            return reply
        return "🌿 بيانات انبعاثات الكربون مهوب متوفرة."

    # 5. إحصائيات عامة
    elif any(w in query for w in ["إحصائيات", "احصائيات", "كم", "عدد", "statistics", "total", "مجموع"]):
        total = len(df_agent)
        reply = f"📋 **إحصائيات المشروع:**\n\n- إجمالي المباني: `{total}` مبنى\n"
        if "SBC_Status" in df_agent.columns:
            c  = len(df_agent[df_agent["SBC_Status"] == "Compliant"])
            nc = total - c
            reply += f"- الممتثلة: `{c}` | المخالفة: `{nc}`\n"
        if "Risk_Level" in df_agent.columns:
            hr = len(df_agent[df_agent["Risk_Level"] == "High Risk"])
            reply += f"- عالية الخطورة: `{hr}` مبنى\n"
        if "SiteEUI(kBtu/sf)" in df_agent.columns:
            avg_eui = df_agent["SiteEUI(kBtu/sf)"].mean()
            reply += f"- متوسط EUI: `{avg_eui:.1f}` kBtu/sf\n"
        return reply

    # 6. Gemini API للأسئلة المفتوحة
    else:
        if not api_key:
            return (
                "❌ مفتاح Gemini مهوب موجود.\n\n"
                "افتحي ملف `agent.py` وحطي مفتاحك مباشرة في السطر:\n"
                "`api_key = 'AIzaSy...مفتاحك_هنا'`"
            )

        v_total  = len(df_agent)
        v_fail   = len(df_agent[df_agent["SBC_Status"].str.contains("Non-Compliant", na=False)]) if "SBC_Status" in df_agent.columns else "غير متوفر"
        v_co2    = df_agent["CO2_Emissions_kg"].sum() if "CO2_Emissions_kg" in df_agent.columns else 0
        v_urgent = len(df_agent[df_agent["Action_Priority"] == "Urgent Action Required"]) if "Action_Priority" in df_agent.columns else 0

        prompt = (
            f"أنت المستشار الفني الذكي لمشروع EcoVolt، خبير طاقة سعودي.\n"
            f"تحدث بلهجة سعودية بيضاء مهنية (أبشري، يا هلا، أمورنا زين).\n"
            f"بيانات المشروع: إجمالي المباني={v_total}، المخالفة={v_fail}، "
            f"الانبعاثات={v_co2:.0f} كجم، العاجلة={v_urgent}.\n"
            f"اربط الأرقام بحلول هندسية (تكييف، عزل، طاقة شمسية).\n"
            f"الرد مختصر 4-5 أسطر.\n\n"
            f"سؤال المستخدم: '{user_input}'"
        )

        url     = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        for attempt in range(5):
            try:
                r = requests.post(url, json=payload, headers=headers, timeout=30)
                if r.status_code == 200:
                    return r.json()["candidates"][0]["content"]["parts"][0]["text"]
                elif r.status_code == 503:
                    time.sleep(5)
                    continue
                else:
                    return f"⚠️ خطأ من واجهة Gemini ({r.status_code}): {r.text}"
            except Exception as e:
                return f"❌ خطأ بالاتصال: {e}"

        return "⚠️ ما قدرت أوصل لـ Gemini بعد 5 محاولات."