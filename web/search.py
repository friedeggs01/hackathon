import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data/papers.csv")
    except FileNotFoundError:
        st.error("File `data/papers.csv` not found. Please check the path.")
        return pd.DataFrame()

    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
    else:
        df["year"] = pd.NA

    df["title_lower"] = df["title"].fillna("").str.lower()
    df["keywords_lower"] = df["keywords"].fillna("").str.lower()
    return df

df = load_data()
if df.empty:
    st.stop()

st.write("Enter a keyword and press Enter to find related papers (search in title or keywords).")
keyword_input = st.text_input("Keyword:", "").strip().lower()

if keyword_input:
    mask_title = df["title_lower"].str.contains(keyword_input, na=False)
    mask_keywords = df["keywords_lower"].str.contains(keyword_input, na=False)
    base_filtered = df[mask_title | mask_keywords]

    st.write(f"{len(base_filtered)} paper(s) found after keyword search")

    if base_filtered.empty:
        st.warning("No related papers found.")
        st.stop()

    filter_type = st.selectbox(
        "Filter by",
        ("None", "Year", "Publisher", "Ranking"),
        index=0
    )

    final_filtered = base_filtered.copy()
    if filter_type != "None":
        if filter_type == "Year":
            unique_years = sorted(base_filtered["year"].dropna().astype(int).unique())
            chosen_years = st.multiselect("Choose year:", unique_years)
            if chosen_years:
                final_filtered = final_filtered[final_filtered["year"].isin(chosen_years)]
        elif filter_type == "Publisher":
            unique_publishers = sorted(base_filtered["publisher"].dropna().unique())
            chosen_publishers = st.multiselect("Choose publisher:", unique_publishers)
            if chosen_publishers:
                final_filtered = final_filtered[final_filtered["publisher"].isin(chosen_publishers)]
        elif filter_type == "Ranking":
            unique_rankings = sorted(base_filtered["ranking"].dropna().unique())
            chosen_rankings = st.multiselect("Choose ranking:", unique_rankings)
            if chosen_rankings:
                final_filtered = final_filtered[final_filtered["ranking"].isin(chosen_rankings)]

        st.write(f"{len(final_filtered)} paper(s) found after applying {filter_type} filter")

    for idx, row in final_filtered.iterrows():
        title = row["title"]
        with st.expander(f"📝 {title}"):
            authors = row["authors"].replace(";", ", ")
            publisher = row.get("publisher", "Unknown publisher")
            ranking = row.get("ranking", "")
            year = int(row["year"]) if pd.notna(row["year"]) else "N/A"
            keywords = row["keywords"].replace(";", ", ")
            link = row.get("link", "").strip()

            st.write(f"- **Authors:** {authors}")
            st.write(f"- **Publisher:** {publisher} {f'({ranking})' if ranking else ''}")
            st.write(f"- **Year:** {year}")
            st.write(f"- **Keywords:** {keywords}")
            if pd.notna(row.get("cited_papers", "")) and str(row["cited_papers"]).strip():
                st.write(f"- **Cited Papers:** {row['cited_papers']}")
            if link:
                st.markdown(f"- **Link:** [Click here]({link})")

    if st.button("Visualize"):
        G = nx.Graph()

        paper_data = {}
        for _, row in final_filtered.iterrows():
            title = str(row["title"]).strip()
            G.add_node(title)
            paper_data[title] = {
                "authors": set(str(row.get("authors", "")).split(";")),
                "keywords": set(str(row.get("keywords", "")).split(";")),
                "publisher": str(row.get("publisher", "")).strip(),
                "ranking": str(row.get("ranking", "")).strip()
            }

        titles = list(paper_data.keys())

        for i in range(len(titles)):
            for j in range(i + 1, len(titles)):
                t1, t2 = titles[i], titles[j]
                d1, d2 = paper_data[t1], paper_data[t2]

                shared_authors = d1["authors"] & d2["authors"]
                shared_publisher = d1["publisher"] and d1["publisher"] == d2["publisher"]
                shared_ranking = d1["ranking"] and d1["ranking"] == d2["ranking"]

                if shared_authors or shared_publisher or shared_ranking:
                    reasons = []
                    if shared_authors:
                        reasons.append("authors")
                    if shared_publisher:
                        reasons.append("publisher")
                    if shared_ranking:
                        reasons.append("ranking")
                    G.add_edge(t1, t2, relation=", ".join(reasons))

        pos = nx.spring_layout(G, seed=42)
        for node_id, (x, y) in pos.items():
            G.nodes[node_id]["pos"] = (x, y)

        net = Network(
            height="780px", width="100%", directed=False,
            notebook=False, cdn_resources="in_line"
        )

        for node_id in G.nodes():
            label = node_id[:15] + "..." if len(node_id) > 15 else node_id
            full_title = node_id
            data = paper_data.get(node_id, {})
            authors = ", ".join(a.strip() for a in data.get("authors", []))
            keywords = ", ".join(k.strip() for k in data.get("keywords", []))
            publisher = data.get("publisher", "")
            ranking = data.get("ranking", "")
            title_html = (
                f"{full_title}\n"
                f"Authors: {authors}\n"
                f"Keywords: {keywords}\n"
                f"Publisher: {publisher} ({ranking})"
            )
            x, y = pos[node_id]
            net.add_node(
                node_id,
                label=label,
                title=title_html,
                x=x * 1000,
                y=y * 1000,
                color="#87CEFA",
                shape="box",
                font={"strokeWidth": 4}
            )

        relation_colors = {
            "authors": "#FF5733",
            "publisher": "#9D33FF",
            "ranking": "#33FF57"
        }

        def get_edge_color(relation_str):
            for rel in relation_colors:
                if rel in relation_str:
                    return relation_colors[rel]
            return "#CCCCCC"

        for src, tgt, data in G.edges(data=True):
            rel = data.get("relation", "")
            edge_color = get_edge_color(rel)
            net.add_edge(src, tgt, title=f"Relation: {rel}", label=rel, color=edge_color)

        net.set_options("""{
          "physics": {
            "enabled": true,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
              "gravitationalConstant": -100,
              "centralGravity": 0.01,
              "springLength": 100,
              "springConstant": 0.001,
              "damping": 0.4,
              "avoidOverlap": 1
            },
            "maxVelocity": 50,
            "stabilization": {
              "enabled": true,
              "iterations": 1000,
              "updateInterval": 25
            }
          }
        }""")
        html_content = net.generate_html()
        components.html(html_content, height=800, scrolling=True)
else:
    st.info("Please enter a keyword to search for related papers.")
