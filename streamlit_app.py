""" Streamlit app for Spotify Playlist Report."""

import pandas as pd
import streamlit as st
from utils import display_image, fetch_spotify_data

data = fetch_spotify_data(
    "https://github.com/FreekvanGeffen/spotify_pull",
    "spotify_data",
    ["data_folder/playlist.ndjson", "data_folder/tracks.ndjson"],
)
df_tracks = data["data_folder/tracks.ndjson"]
df_tracks["image"] = df_tracks["image"].apply(display_image)
df_playlist = data["data_folder/playlist.ndjson"]
latest_playlist_info = df_playlist.sort_values("date", ascending=False).iloc[
    0
]  # check if redundant

st.balloons()

## Header
st.markdown(f"# {latest_playlist_info['name']}")
st.write(f"{latest_playlist_info['description']}")

col1, col2 = st.columns([1, 1])
with col1:
    st.metric("Number of followers", df_playlist["followers"].iloc[0])
with col2:
    st.metric("Number of tracks", df_playlist["numbers"].iloc[0])

## Image
st.image(latest_playlist_info["image"], width=400)

## Table
col1, col2 = st.columns([1, 1])
with col1:
    options = ["All"] + list(df_tracks.added_by.unique())
    added_by_filter = st.selectbox("Added by", options=options)
with col2:
    options = ["All"] + list(df_tracks.artist.unique())
    artist_filter = st.selectbox("Choose an artist", options=options)

skip_columns = ["added_by", "added_at", "duration", "image"]
df_tracks_table = df_tracks.drop(skip_columns, axis=1).copy()
if added_by_filter != "All":
    df_tracks_table = df_tracks[df_tracks["added_by"] == added_by_filter]
if artist_filter != "All":
    df_tracks_table = df_tracks_table[df_tracks_table["artist"] == artist_filter]

st.dataframe(
    df_tracks_table,
    column_config={
        "name": "Name",
        "artist": "Artist",
        "album": "Album",
        "release_date": st.column_config.DateColumn("Release Date"),
        "url": st.column_config.LinkColumn("App URL"),
    },
    hide_index=True,
)
df_plot = df_tracks.added_by.value_counts().reset_index()
st.bar_chart(
    df_plot,
    x="added_by",
    y="count",
)

## Line Chart
# Select the y-column using a selectbox
if "column_selection" not in st.session_state:
    st.session_state.column_selection = "followers"

st.radio(
    "Select column",
    key="column_selection",
    options=["followers", "numbers"],
)

# Plot the selected column against the date column
st.line_chart(df_playlist.set_index("date")[st.session_state.column_selection])

dark_mode_css = """
    <style>
        /* Add your custom CSS for dark mode here */
        body {
            background-color: #1a1a1a; /* Example: Dark background color */
            color: #ffffff; /* Example: Light text color */
        }
        /* Add more CSS rules for other elements */
    </style>
    """
st.markdown(dark_mode_css, unsafe_allow_html=True)