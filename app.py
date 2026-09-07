"""Streamlit app: a map of British town-name origins.

Each town/city is drawn as a dot on a map of Great Britain. Dot size scales
with population and colour indicates the linguistic origin of the name's
prefixes/suffixes (Old English, Old Norse, Celtic, Roman/Latin, Norman).

Run with::

    streamlit run app.py
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from british_names.data import load_towns
from british_names.origins import ORIGIN_COLORS, Origin, color_hex

st.set_page_config(
    page_title="British Town-Name Origins",
    page_icon="🗺️",
    layout="wide",
)

st.title("🗺️ British Town-Name Origins")
st.markdown(
    "Each dot is a British town or city. **Size** scales with population and "
    "**colour** shows the linguistic origin of the name's prefixes and "
    "suffixes (e.g. Old Norse `-by`, Old English `-ton`, Roman `-chester`, "
    "Celtic `pen-`/`aber-`). Origins are inferred with a transparent rule-based "
    "heuristic — see `british_names/origins.py`."
)


@st.cache_data
def get_data():
    return load_towns()


df = get_data()

# --- Sidebar controls -------------------------------------------------------
st.sidebar.header("Filters")

all_origins = [o.value for o in Origin if o.value in set(df["origin"])]
selected = st.sidebar.multiselect(
    "Name origins to show",
    options=all_origins,
    default=all_origins,
)

min_pop, max_pop = int(df["population"].min()), int(df["population"].max())
pop_floor = st.sidebar.slider(
    "Minimum population",
    min_value=min_pop,
    max_value=max_pop,
    value=min_pop,
    step=1000,
)

filtered = df[df["origin"].isin(selected) & (df["population"] >= pop_floor)]

# --- Map --------------------------------------------------------------------
fig = go.Figure()
for origin in Origin:
    if origin.value not in selected:
        continue
    subset = filtered[filtered["origin"] == origin.value]
    if subset.empty:
        continue
    fig.add_trace(
        go.Scattergeo(
            lon=subset["lon"],
            lat=subset["lat"],
            text=subset["name"] + " (" + subset["population"].astype(str) + ")",
            name=origin.value,
            hovertemplate="%{text}<extra>" + origin.value + "</extra>",
            marker=dict(
                size=subset["population"],
                sizemode="area",
                sizeref=2.0 * df["population"].max() / (60.0**2),
                sizemin=4,
                color=color_hex(origin),
                line=dict(width=0.5, color="rgba(0,0,0,0.4)"),
                opacity=0.85,
            ),
        )
    )

fig.update_geos(
    scope="europe",
    resolution=50,
    lataxis_range=[49.5, 59.0],
    lonaxis_range=[-8.5, 2.5],
    showcountries=True,
    countrycolor="rgba(120,120,120,0.6)",
    showland=True,
    landcolor="rgb(243, 243, 243)",
    showocean=True,
    oceancolor="rgb(216, 235, 246)",
    showlakes=False,
)
fig.update_layout(
    height=720,
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(title="Name origin", yanchor="top", y=0.99, xanchor="left", x=0.01),
)

col_map, col_stats = st.columns([3, 1])
with col_map:
    st.plotly_chart(fig, use_container_width=True)

with col_stats:
    st.subheader("Legend")
    for origin in Origin:
        if origin.value not in set(df["origin"]):
            continue
        r, g, b = ORIGIN_COLORS[origin]
        st.markdown(
            f"<span style='display:inline-block;width:12px;height:12px;"
            f"background:rgb({r},{g},{b});border-radius:50%;margin-right:6px;'></span>"
            f"{origin.value}",
            unsafe_allow_html=True,
        )

    st.subheader("Counts")
    counts = (
        filtered["origin"].value_counts().rename_axis("origin").reset_index(name="towns")
    )
    st.dataframe(counts, hide_index=True, use_container_width=True)

st.caption(
    f"Showing {len(filtered)} of {len(df)} towns. "
    "Sample dataset — replace `data/towns_sample.csv` with OS OpenNames + ONS "
    "data for the full map."
)

with st.expander("Show underlying data"):
    st.dataframe(
        filtered[["name", "origin", "population", "lat", "lon"]].sort_values(
            "population", ascending=False
        ),
        hide_index=True,
        use_container_width=True,
    )
