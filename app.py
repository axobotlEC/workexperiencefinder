# app.py
import sys
from pathlib import Path

import streamlit as st
import pandas as pd

# Ensure project root is on sys.path so `src` imports work when Streamlit
# changes the current working directory or when running inside a venv.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import importlib
    import src.database as _db
    importlib.reload(_db)
    load_opportunities = getattr(_db, "load_opportunities")
except Exception as _e:
    # Provide a graceful fallback so the UI can start and show an error
    import pandas as _pd
    def load_opportunities():
        # empty DataFrame with expected columns
        return _pd.DataFrame(
            columns=[
                "title",
                "company",
                "location",
                "deadline",
                "sector",
                "description",
                "link",
                "source",
                "is_student_opportunity",
            ]
        )
    load_error = _e

st.set_page_config(page_title="Student Opportunity Finder", layout="wide")
st.title("Student Opportunity Finder")

if "load_error" in globals():
    st.error(f"Database import error: {load_error}")

try:
    df = load_opportunities()
except Exception as e:
    df = pd.DataFrame(
        columns=[
            "title",
            "company",
            "location",
            "deadline",
            "sector",
            "description",
            "link",
            "source",
            "is_student_opportunity",
        ]
    )
    load_error = e

# Parse deadlines to datetimes when possible for sorting/filtering
if not df.empty and "deadline" in df.columns:
    try:
        df["deadline_parsed"] = pd.to_datetime(df["deadline"], errors="coerce")
    except Exception:
        df["deadline_parsed"] = pd.NaT

if df.empty:
    st.info("No opportunities found. Run the scrapers or seed demo data.")
else:
    # quick filters
    cols = st.columns([2,2,1,1])
    with cols[0]:
        q = st.text_input("Search title / description")
    with cols[1]:
        company = st.text_input("Company")
    with cols[2]:
        sector = st.selectbox("Sector", options=["All"] + sorted(df["sector"].dropna().unique().tolist()))
    with cols[3]:
        student_only = st.checkbox("Student opportunities only", value=True)
    validated_only = st.checkbox("Show only validated opportunities", value=False)
    # Sorting controls
    sort_col = st.selectbox("Sort by", options=["None", "deadline", "sector", "company"], index=0)
    sort_asc = st.checkbox("Ascending", value=True)

    filtered = df.copy()
    if q:
        ql = q.lower()
        filtered = filtered[filtered.apply(lambda r: ql in str(r.title).lower() or ql in str(r.description).lower(), axis=1)]
    if company:
        filtered = filtered[filtered["company"].str.contains(company, case=False, na=False)]
    if sector and sector != "All":
        filtered = filtered[filtered["sector"] == sector]
    if student_only and "is_student_opportunity" in filtered.columns:
        filtered = filtered[filtered["is_student_opportunity"] == True]
    if validated_only and "scrape_validation_passed" in filtered.columns:
        filtered = filtered[filtered["scrape_validation_passed"] == True]

    if sort_col and sort_col != "None":
        if sort_col == "deadline" and "deadline_parsed" in filtered.columns:
            filtered = filtered.sort_values(by=["deadline_parsed"], ascending=sort_asc)
        elif sort_col in filtered.columns:
            filtered = filtered.sort_values(by=[sort_col], ascending=sort_asc)

    st.write(f"Showing {len(filtered)} opportunities")
    st.dataframe(filtered.reset_index(drop=True), use_container_width=True)

    csv = filtered.to_csv(index=False)
    st.download_button("Download CSV", csv, "opportunities.csv", "text/csv")
