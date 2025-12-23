import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Rescoring Dashboard", layout="wide")
st.title("📊 Rescoring Quality Dashboard")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file is None:
    st.stop()

df = pd.read_excel(uploaded_file)

# -----------------------------
# CONSTANTS
# -----------------------------
PART_COL = 11        # Column L (A / B)
RESCORE_FLAG_COL = 76  # Column BX/BY where value 12 means rescored

SCORER1_ID_COL = 45   # AT
SCORER2_ID_COL = 60   # BI

# Part A columns
PA_FINAL = [20, 21, 22, 23]       # TA1, TA2, Style, Accuracy
PA_S1 = [35, 36, 37, 38]
PA_S2 = [50, 51, 52, 53]
PA_AI = [95, 96, 97, 98]

# Part B columns
PB_FINAL = [20, 21, 22, 23, 24]   # GA1, GA2, V, G, O
PB_S1 = [35, 36, 37, 38, 39]
PB_S2 = [50, 51, 52, 53, 54]
PB_AI = [95, 96, 97, 98, 99]

# -----------------------------
# SPLIT PARTS
# -----------------------------
part_a = df[df.iloc[:, PART_COL].astype(str).str.strip() == "A"]
part_b = df[df.iloc[:, PART_COL].astype(str).str.strip() == "B"]

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def is_rescored(row):
    return row.iloc[RESCORE_FLAG_COL] == 12


def compare_simple(final, scored):
    if pd.isna(scored):
        return False
    return final != scored


def compare_vgo(final_vals, scored_vals):
    if any(pd.isna(scored_vals)):
        return False
    return abs(sum(final_vals) - sum(scored_vals)) > 1


def build_human_table(data, part="A"):
    records = []

    scorer_ids = pd.concat([
        data.iloc[:, SCORER1_ID_COL],
        data.iloc[:, SCORER2_ID_COL]
    ]).dropna().unique()

    for sid in scorer_ids:
        rows = data[
            (data.iloc[:, SCORER1_ID_COL] == sid) |
            (data.iloc[:, SCORER2_ID_COL] == sid)
        ]

        total_scored = len(rows)
        total_rescored = rows.apply(is_rescored, axis=1).sum()

        if part == "A":
            labels = ["TA1", "TA2", "Style", "Accuracy"]
            final_cols = PA_FINAL
            s1_cols = PA_S1
            s2_cols = PA_S2
        else:
            labels = ["GA1", "GA2", "V", "G", "O"]
            final_cols = PB_FINAL
            s1_cols = PB_S1
            s2_cols = PB_S2

        incorrect = {k: 0 for k in labels}

        for _, r in rows.iterrows():
            if r.iloc[SCORER1_ID_COL] == sid:
                for i, k in enumerate(labels):
                    if part == "B" and k in ["V", "G", "O"]:
                        break
                    if compare_simple(r.iloc[final_cols[i]], r.iloc[s1_cols[i]]):
                        incorrect[k] += 1

                if part == "B":
                    if compare_vgo(
                        r.iloc[final_cols[2:5]],
                        r.iloc[s1_cols[2:5]]
                    ):
                        incorrect["V"] += 1
                        incorrect["G"] += 1
                        incorrect["O"] += 1

            if r.iloc[SCORER2_ID_COL] == sid:
                for i, k in enumerate(labels):
                    if part == "B" and k in ["V", "G", "O"]:
                        break
                    val = r.iloc[s2_cols[i]]
                    if pd.isna(val):
                        val = r.iloc[PA_AI[i] if part == "A" else PB_AI[i]]
                    if compare_simple(r.iloc[final_cols[i]], val):
                        incorrect[k] += 1

                if part == "B":
                    scored_vals = r.iloc[s2_cols[2:5]]
                    if scored_vals.isna().all():
                        scored_vals = r.iloc[PB_AI[2:5]]
                    if compare_vgo(
                        r.iloc[final_cols[2:5]],
                        scored_vals
                    ):
                        incorrect["V"] += 1
                        incorrect["G"] += 1
                        incorrect["O"] += 1

        row = {
            "Scorer ID": sid,
            "Total Scored": total_scored,
            "Total Rescored": total_rescored,
            "Rescoring %": round((total_rescored / total_scored) * 100, 2) if total_scored else 0
        }

        for k in labels:
            row[f"Incorrect {k}"] = incorrect[k]

        records.append(row)

    return pd.DataFrame(records)


def build_ai_table(data, part="A"):
    total_scored = len(data)
    total_rescored = data.apply(is_rescored, axis=1).sum()

    if part == "A":
        labels = ["TA1", "TA2", "Style", "Accuracy"]
        final_cols = PA_FINAL
        ai_cols = PA_AI
    else:
        labels = ["GA1", "GA2", "V", "G", "O"]
        final_cols = PB_FINAL
        ai_cols = PB_AI

    incorrect = {k: 0 for k in labels}

    for _, r in data.iterrows():
        for i, k in enumerate(labels):
            if part == "B" and k in ["V", "G", "O"]:
                break
            if compare_simple(r.iloc[final_cols[i]], r.iloc[ai_cols[i]]):
                incorrect[k] += 1

        if part == "B":
            if compare_vgo(
                r.iloc[final_cols[2:5]],
                r.iloc[ai_cols[2:5]]
            ):
                incorrect["V"] += 1
                incorrect["G"] += 1
                incorrect["O"] += 1

    row = {
        "Total Scored by AI": total_scored,
        "Total Rescored": total_rescored,
        "Rescoring %": round((total_rescored / total_scored) * 100, 2) if total_scored else 0
    }

    for k in labels:
        row[f"Incorrect {k}"] = incorrect[k]

    return pd.DataFrame([row])


# -----------------------------
# DASHBOARD
# -----------------------------
st.subheader("Part A – Human Scorers")
st.dataframe(build_human_table(part_a, "A"))

st.subheader("Part B – Human Scorers")
st.dataframe(build_human_table(part_b, "B"))

st.subheader("Part A – AI")
st.dataframe(build_ai_table(part_a, "A"))

st.subheader("Part B – AI")
st.dataframe(build_ai_table(part_b, "B"))
