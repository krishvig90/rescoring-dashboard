import streamlit as st
import pandas as pd

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="Rescoring Dashboard", layout="wide")

ADMIN_PASSWORD = "admin123"   # 🔐 CHANGE THIS

# -----------------------------
# ADMIN UPLOAD (PASSWORD)
# -----------------------------
st.sidebar.header("Admin Upload")

password = st.sidebar.text_input("Enter admin password", type="password")
is_admin = password == ADMIN_PASSWORD

if "df" not in st.session_state:
    st.session_state["df"] = None

if is_admin:
    uploaded_file = st.sidebar.file_uploader(
        "Upload Excel file", type=["xlsx"]
    )
    if uploaded_file:
        st.session_state["df"] = pd.read_excel(uploaded_file)

if st.session_state["df"] is None:
    st.info("Waiting for admin to upload the Excel file")
    st.stop()

df = st.session_state["df"]

# -----------------------------
# COMMON COLUMNS
# -----------------------------
PART_COL = 11       # L
RESCORED_COL = 76   # BY (12 = rescored)

# Final Scores – Part A
FINAL_A = {
    "TA1": 20, "TA2": 21, "Style": 22, "Accuracy": 23
}

# Scoring 1 – Part A
S1_A = {
    "TA1": 35, "TA2": 36, "Style": 37, "Accuracy": 38
}
S1_ID = 45

# Scoring 2 – Part A
S2_A = {
    "TA1": 50, "TA2": 51, "Style": 52, "Accuracy": 53
}
S2_ID = 60

# AI – Part A
AI_A = {
    "TA1": 95, "TA2": 96, "Style": 97, "Accuracy": 98
}

# -----------------------------
# FILTER PARTS
# -----------------------------
part_a = df[df.iloc[:, PART_COL] == "A"]
part_b = df[df.iloc[:, PART_COL] == "B"]

# -----------------------------
# HELPER FUNCTION
# -----------------------------
def build_human_table(df_part, final_cols, s1_cols, s2_cols, s1_id_col, s2_id_col, viewpoints):
    rows = []

    scorer_ids = pd.concat([
        df_part.iloc[:, s1_id_col],
        df_part.iloc[:, s2_id_col]
    ]).dropna().unique()

    for i, scorer in enumerate(scorer_ids, 1):
        scorer_rows = df_part[
            (df_part.iloc[:, s1_id_col] == scorer) |
            (df_part.iloc[:, s2_id_col] == scorer)
        ]

        total_scored = len(scorer_rows)
        total_rescored = len(scorer_rows[scorer_rows.iloc[:, RESCORED_COL] == 12])

        incorrect = {v: 0 for v in viewpoints}
        total_view = {v: 0 for v in viewpoints}

        for _, r in scorer_rows.iterrows():
            for v in viewpoints:
                final_val = r.iloc[final_cols[v]]

                # Scorer 1
                if r.iloc[s1_id_col] == scorer:
                    total_view[v] += 1
                    if r.iloc[s1_cols[v]] != final_val:
                        incorrect[v] += 1

                # Scorer 2
                if r.iloc[s2_id_col] == scorer:
                    total_view[v] += 1
                    if pd.isna(r.iloc[s2_cols[v]]):
                        if r.iloc[AI_A[v]] != final_val:
                            incorrect[v] += 1
                    else:
                        if r.iloc[s2_cols[v]] != final_val:
                            incorrect[v] += 1

        rows.append({
            "S.No": i,
            "Scorer ID": scorer,
            "Total Scored": total_scored,
            "Total Rescored": total_rescored,
            "Rescoring %": round((total_rescored / total_scored) * 100, 2) if total_scored else 0,
            **{f"Total {v}": total_view[v] for v in viewpoints},
            **{f"Incorrect {v}": incorrect[v] for v in viewpoints}
        })

    return pd.DataFrame(rows)

# -----------------------------
# PART A – HUMAN
# -----------------------------
st.header("📘 Part A – Human Scorers")

part_a_table = build_human_table(
    part_a,
    FINAL_A,
    S1_A,
    S2_A,
    S1_ID,
    S2_ID,
    ["TA1", "TA2", "Style", "Accuracy"]
)

st.dataframe(part_a_table, use_container_width=True)

# -----------------------------
# PART A – AI
# -----------------------------
st.header("🤖 Part A – AI")

ai_total = len(part_a)
ai_rescored = len(part_a[part_a.iloc[:, RESCORED_COL] == 12])

ai_errors = {}
for v, col in AI_A.items():
    ai_errors[v] = (part_a.iloc[:, col] != part_a.iloc[:, FINAL_A[v]]).sum()

ai_df = pd.DataFrame([{
    "Total Scored by AI": ai_total,
    "Total Rescored": ai_rescored,
    "Rescoring %": round((ai_rescored / ai_total) * 100, 2) if ai_total else 0,
    **{f"Incorrect {k}": v for k, v in ai_errors.items()}
}])

st.dataframe(ai_df, use_container_width=True)

# -----------------------------
# PART B PLACEHOLDER
# -----------------------------
st.header("📕 Part B – Human & AI")
st.info("Part B logic can be added here using the same pattern (GA1, GA2, V, G, O)")
