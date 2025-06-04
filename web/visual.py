import pandas as pd
import networkx as nx
import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components

# ============================================================
# 1. Đọc dữ liệu đầu vào từ thư mục data/
#    - data/papers.csv  (paper_id, title, authors, keywords)
#    - data/citations.csv (source_id, target_id)
# ============================================================
papers_df = pd.read_csv("data/papers.csv")
citations_df = pd.read_csv("data/citations.csv")

# Bạn có thể comment nếu không cần hiển thị bảng
st.write("### Dữ liệu Papers")
st.dataframe(papers_df)

st.write("### Dữ liệu Citations")
st.dataframe(citations_df)

# ============================================================
# 2. Xây dựng đồ thị directed graph bằng NetworkX
# ============================================================
G = nx.DiGraph()
for _, row in papers_df.iterrows():
    pid = row["paper_id"]
    G.add_node(
        pid,
        title=row["title"],
        authors=row["authors"],
        keywords=row["keywords"]
    )
for _, row in citations_df.iterrows():
    src = row["source_id"]
    tgt = row["target_id"]
    if src in G.nodes and tgt in G.nodes:
        G.add_edge(src, tgt)

# ============================================================
# 3. Tính layout (vị trí) cho đồ thị
#    - Dùng spring_layout để nodes không chồng lấn nhau
# ============================================================
pos = nx.spring_layout(G, seed=42)
for node_id, (x, y) in pos.items():
    G.nodes[node_id]["pos"] = (x, y)

# ============================================================
# 4. Khởi tạo PyVis Network (draggable, physics-on)
# ============================================================
net = Network(
    height="450px",
    width="100%",
    directed=True,
    notebook=False,
    cdn_resources="in_line",  # chèn JS/CSS inline vào HTML
)
# Thêm nodes và edges vào PyVis
for node_id, data in G.nodes(data=True):
    title_html = (
        f"Title: {data['title']}\n"
        f"Authors: {data['authors']}\n"
        f"Keywords: {data['keywords']}\n"
    )
    net.add_node(
        node_id,
        label=(data["title"][:10] + "..." if len(data["title"]) > 10 else data["title"]),
        title=title_html,
        x=pos[node_id][0],
        y=pos[node_id][1],
        font={'strokeWidth': 4}
    )
for src, tgt in G.edges():
    net.add_edge(src, tgt)

# Bật physics để cho phép drag-drop node
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
""")

html_content = net.generate_html()

components.html(html_content, height=800, scrolling=True)
