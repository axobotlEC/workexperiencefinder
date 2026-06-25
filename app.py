#This file is for the UI done with streamlit.

import streamlit as st
from src.database import load_opportunities

st.title("Student Opportunity Finder")
rows = load_opportunities()
st.dataframe(rows)