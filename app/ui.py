import streamlit as st
import pandas as pd

# Local imports
from store import get_duck, init_duck
from data_ingest import run_simulator
from retriever import index_corpus, search_docs
from models import detect_anomalies, features_last_window, fit_dummy_predictor, score_risk

st.set_page_config(page_title="IoT RAG", layout="wide")
st.title("🏢 IoT Sensor Data RAG for Smart Buildings")

# ------------------------------------------------------------------
# Buttons for simulation & ingestion
# ------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("▶️ Start Sensor Simulator (5s)"):
        con = get_duck()
        init_duck(con)
        run_simulator(duration_seconds=5)
        st.success("✅ Sensor data generated and stored.")

with col2:
    if st.button("📚 Ingest Manuals & Specs"):
        index_corpus()
        st.success("✅ Documents indexed into Chroma.")

# ------------------------------------------------------------------
# RAG Question Section
# ------------------------------------------------------------------
st.subheader("💬 Ask a Question (RAG over Manuals/Specs)")
query = st.text_input("Enter your question about maintenance or specs:")

if query:
    res = search_docs(query, k=3)
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]

    if docs:
        # ✅ Show synthesized answer
        top = docs[0]
        st.success("**Suggested answer (from retrieved docs):**\n\n" + top[:600])

        with st.expander("Sources & snippets"):
            for d, m in zip(docs, metas):
                st.write(f"- **{m.get('source','unknown')}**: {d[:300]}...")

    else:
        st.warning("⚠️ No relevant docs found. Try ingesting manuals/specs first.")

# ------------------------------------------------------------------
# Sensor Data + Analytics Section
# ------------------------------------------------------------------
st.subheader("📊 Sensor Data & Analytics")

con = get_duck()
try:
    df = con.execute("SELECT * FROM readings ORDER BY ts DESC LIMIT 200").fetchdf()
except Exception:
    df = pd.DataFrame()

if not df.empty:
    st.write("Latest Sensor Data:")
    st.dataframe(df)

    # Anomalies
    anoms = detect_anomalies(df)
    st.write("Anomalies detected:", len(anoms))
    if not anoms.empty:
        st.dataframe(anoms)

    # Risk prediction
    feats = features_last_window(df, window_minutes=30)
    clf = fit_dummy_predictor(feats)
    risk = score_risk(clf, feats)
    st.write("Risk Scores:")
    st.dataframe(risk)

    # ------------------------------------------------------------------
    # Maintenance Recommendations
    # ------------------------------------------------------------------
    def rule_based_recos(df_recent):
        recos = []
        vib = df_recent[(df_recent["metric"] == "vibration")]
        for sid in vib["sensor_id"].unique():
            v = vib[vib["sensor_id"] == sid]["value"].tail(20)
            if not v.empty and (v.mean() > 0.5):
                recos.append(
                    f"Pump {sid}: vibration avg {v.mean():.2f} mm/s > 0.5 → schedule bearing/seal inspection."
                )

        tmp = df_recent[(df_recent["metric"] == "temp")]
        for sid in tmp["sensor_id"].unique():
            t = tmp[tmp["sensor_id"] == sid]["value"].tail(20)
            if not t.empty and (t.mean() < 18 or t.mean() > 24):
                recos.append(
                    f"{sid}: temp avg {t.mean():.1f} °C outside 18–24 °C → check setpoints/filters/valves."
                )

        return recos

    st.subheader("🛠️ Recommended Actions")
    recos = rule_based_recos(df)
    try:
        top_risk = risk.sort_values("risk_score", ascending=False).head(2)["sensor_id"].tolist()
        if top_risk:
            recos.append(
                f"High risk sensors (model): {', '.join(top_risk)} → inspect within next window."
            )
    except Exception:
        pass

    if recos:
        for r in recos:
            st.info("• " + r)
    else:
        st.success("No immediate actions suggested from current data.")
else:
    st.info("ℹ️ No sensor data yet. Click ▶️ Start Sensor Simulator.")
