import streamlit as st
import pandas as pd
import random

@st.cache_data
def load_papers():
    try:
        df = pd.read_csv("data/papers.csv")
        return df
    except Exception as e:
        st.error(f"Could not load papers.csv: {e}")
        return pd.DataFrame()

papers_df = load_papers()

if papers_df.empty:
    st.warning("No paper data found.")
else:
    num_suggestions = random.randint(2, 3)
    suggested_papers = papers_df.sample(n=num_suggestions)

    st.markdown("### 🔍 Suggested papers you may like:")
    for _, row in suggested_papers.iterrows():
        st.markdown(f"**📝 {row['title']}**")
        st.markdown(f"- 👨‍🔬 Authors: {row['authors'].replace(";", ", ")}")
        if 'year' in row:
            st.markdown(f"- 📅 Year: {int(row['year']) if pd.notna(row['year']) else 'N/A'}")
        if 'ranking' in row:
            st.markdown(f"- 🏅 Ranking: {row['ranking']}")
        if 'link' in row and pd.notna(row['link']) and str(row['link']).strip():
            st.markdown(f"- 🔗 Link: [Click here]({row['link']})")
        st.markdown("---")
