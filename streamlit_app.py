""" Streamlit app for Spotify Playlist Report."""

import altair as alt
import pandas as pd
import streamlit as st
from utils import convert_to_timedelta, display_image, fetch_spotify_data

data = fetch_spotify_data(
    "https://github.com/FreekvanGeffen/spotify_pull",
    "spotify_data",
    ["data_folder/playlist.ndjson", "data_folder/tracks.ndjson"],
)
df_tracks = data["data_folder/tracks.ndjson"]
df_tracks["image"] = df_tracks["image"].apply(display_image)
df_tracks["duration_timedelta"] = df_tracks["duration"].apply(convert_to_timedelta)
df_tracks["release_date"] = pd.to_datetime(df_tracks["release_date"], format="mixed")
df_tracks["release_year"] = df_tracks["release_date"].dt.year
df_playlist = data["data_folder/playlist.ndjson"]

latest_playlist_info = df_playlist.sort_values("date", ascending=False).iloc[0]
total_duration = df_tracks["duration_timedelta"].sum()

st.balloons()

## Header
st.markdown(f"# {latest_playlist_info['name']}")
st.write(f"{latest_playlist_info['description']}")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Number of followers", latest_playlist_info["followers"])
with col2:
    st.metric("Number of tracks", latest_playlist_info["numbers"])
with col3:
    st.metric(
        "Number of hours",
        f"{int(total_duration.total_seconds() // 3600)}",
    )

## Image
html_code = f"""
<div style="text-align: center;">
    <a href="{latest_playlist_info["url"]}" target="_blank">
        <img src="{latest_playlist_info["image"]}" alt="Clickable Image" style="width: 80%;">
    </a>
</div>
<br>
"""
st.markdown(html_code, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Playlist", "Tracks"])

with tab1:
    ## Line Chart
    if "column_selection" not in st.session_state:
        st.session_state.column_selection = "followers"
    st.radio(
        "Select column",
        key="column_selection",
        options=["followers", "numbers"],
    )

    chart = (
        alt.Chart(df_playlist)
        .mark_line()
        .encode(
            x=alt.X("date:T", axis=alt.Axis(format="%Y-%m-%d")),
            y=f"{st.session_state.column_selection}:Q",
        )
        .properties(
            title=f"{st.session_state.column_selection} over time", width="container"
        )
    )
    st.altair_chart(chart, use_container_width=True)

with tab2:
    ## Bar chart
    if "bar_selection" not in st.session_state:
        st.session_state.bar_selection = "added_by"
    st.radio(
        "Select column",
        key="bar_selection",
        options=["added_by", "artist", "album", "release_year"],
    )
    df_plot = df_tracks[st.session_state.bar_selection].value_counts().reset_index()
    st.bar_chart(
        df_plot,
        x=st.session_state.bar_selection,
        y="count",
    )
