import pandas as pd
import networkx as nx
import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components

papers_df = pd.read_csv("data/papers.csv")

st.write("### Dữ liệu Papers")
st.dataframe(papers_df)

G = nx.DiGraph()

for _, row in papers_df.iterrows():
    paper_title = row["title"].strip()
    authors = [a.strip() for a in str(row.get("authors", "")).split(";") if a.strip()]
    keywords = [k.strip() for k in str(row.get("keywords", "")).split(";") if k.strip()]
    G.add_node(paper_title, type="paper", title=paper_title, authors=authors, keywords=keywords)

for _, row in papers_df.iterrows():
    authors = [a.strip() for a in str(row.get("authors", "")).split(";") if a.strip()]
    for author in authors:
        if author not in G.nodes:
            G.add_node(author, type="author", name=author)

for _, row in papers_df.iterrows():
    paper_title = row["title"].strip()
    authors = [a.strip() for a in str(row.get("authors", "")).split(";") if a.strip()]
    for author in authors:
        G.add_edge(author, paper_title, relation="authorship")
    for i in range(len(authors)):
        for j in range(i+1, len(authors)):
            a1 = authors[i]
            a2 = authors[j]
            G.add_edge(a1, a2, relation="coauthor")
            G.add_edge(a2, a1, relation="coauthor")

all_papers = set(papers_df["title"].str.strip())
for _, row in papers_df.iterrows():
    paper_title = row["title"].strip()
    cited_list = [c.strip() for c in str(row.get("cited_papers", "")).split(";") if c.strip()]
    for cited in cited_list:
        if cited in all_papers:
            G.add_edge(paper_title, cited, relation="citation")
        else:
            G.add_node(cited, type="paper", title=cited, authors=[], keywords=[])
            G.add_edge(paper_title, cited, relation="citation")

paper_keywords = {row["title"].strip(): [k.strip() for k in str(row.get("keywords", "")).split(";") if k.strip()] for _, row in papers_df.iterrows()}
papers = list(paper_keywords.keys())
for i in range(len(papers)):
    for j in range(i+1, len(papers)):
        p1 = papers[i]
        p2 = papers[j]
        kws1 = set(paper_keywords.get(p1, []))
        kws2 = set(paper_keywords.get(p2, []))
        if kws1 & kws2:
            G.add_edge(p1, p2, relation="keyword")
            G.add_edge(p2, p1, relation="keyword")

pos = nx.spring_layout(G, seed=42)
for node_id, (x, y) in pos.items():
    G.nodes[node_id]["pos"] = (x, y)

net = Network(
    height="600px",
    width="100%",
    directed=True,
    notebook=False,
    cdn_resources="in_line",
)

for node_id, data in G.nodes(data=True):
    if data.get("type") == "author":
        label = data.get("name", node_id)
        title_html = f"<b>Author:</b> {data.get('name')}"
        color = "#FFA500"  
        shape = "ellipse"
    else:
        label = (data.get("title")[:15] + "...") if len(data.get("title", "")) > 15 else data.get("title")
        authors = ", ".join(data.get("authors", []))
        keywords = ", ".join(data.get("keywords", []))
        title_html = (
            f"<b>Paper:</b> {data.get('title')}<br>"
            f"<b>Authors:</b> {authors}<br>"
            f"<b>Keywords:</b> {keywords}<br>"
        )
        color = "#87CEFA"  
        shape = "box"
    net.add_node(
        node_id,
        label=label,
        title=title_html,
        x=pos[node_id][0] * 1000,
        y=pos[node_id][1] * 1000,
        color=color,
        shape=shape,
        font={"strokeWidth": 4},
    )

for src, tgt, data in G.edges(data=True):
    rel = data.get("relation", "")
    net.add_edge(src, tgt, title=f"Relation: {rel}", label=rel)

net.set_options("""
{
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
}
"""
)

html_content = net.generate_html()
components.html(html_content, height=800, scrolling=True)
