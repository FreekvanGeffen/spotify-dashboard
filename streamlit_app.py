""" Streamlit app for Spotify Playlist Report."""

import os
from datetime import datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection
from utils import convert_to_timedelta, display_image, fetch_spotify_data, parse_date
from vote import (
    add_track_to_playlist,
    check_track_in_playlist,
    create_spotipy_oauth_client,
    search_track,
)

playlist_id = "36ElcXTgduenOvy2glOReJ"
data = fetch_spotify_data(
    "https://github.com/FreekvanGeffen/spotify_pull",
    "spotify_data",
    ["data_folder/playlist.ndjson", "data_folder/tracks.ndjson"],
)
df_tracks = data["data_folder/tracks.ndjson"]
df_tracks["image"] = df_tracks["image"].apply(display_image)
df_tracks["duration_timedelta"] = df_tracks["duration"].apply(convert_to_timedelta)
df_tracks["release_date"] = df_tracks["release_date"].apply(parse_date)
df_tracks["release_year"] = df_tracks["release_date"].dt.year
df_playlist = data["data_folder/playlist.ndjson"]

latest_playlist_info = df_playlist.sort_values("date", ascending=False).iloc[0]
total_duration = df_tracks["duration_timedelta"].sum()
seven_days_ago = datetime.now() - timedelta(days=7)


if "cache_path" not in st.session_state:
    st.session_state["cache_path"] = ".cache"
    if os.path.exists(st.session_state["cache_path"]):
        os.remove(st.session_state["cache_path"])

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

tab1, tab2, tab3 = st.tabs(["Votes", "Playlist", "Tracks"])

with tab1:
    sp = create_spotipy_oauth_client()
    if sp:
        st.success("Authorization successful!")
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_votes = conn.read()

        st.write("Vote to add more tracks to this playlist!")
        track_name = st.text_input("Track Name", None)
        artist = st.text_input("Artist", None)

        if track_name and artist:
            with st.spinner("Searching..."):
                track_info = search_track(sp, track_name, artist)

            if track_info:
                with st.expander("Track Found!", expanded=True):
                    html_code = f"""
                                <div style="text-align: center;">
                                    <a href="{track_info["url"]}" target="_blank">
                                        <img src="{track_info["image"]}" alt="Clickable Image" style="width: 50%;">
                                    </a>
                                </div>
                                <br>
                                """
                    st.markdown(html_code, unsafe_allow_html=True)
                    st.write(
                        f"{track_info['name']} - {track_info['artist']} - {track_info['release_date']}"
                    )

                    # Check if track is already in playlist
                    track_check = check_track_in_playlist(
                        sp, playlist_id, track_info["url"]
                    )
                    if track_check[0]:
                        # Voting section
                        st.write("Vote for this track:")
                        vote_button = st.button("Vote")
                        if vote_button:
                            # Add vote if track already in vote list
                            user_name = sp.current_user()["display_name"]
                            if track_info["url"] in df_votes["url"].values:
                                index = df_votes[
                                    df_votes["url"] == track_info["url"]
                                ].index[0]
                                if user_name in df_votes.loc[index, "voted_by"]:
                                    st.warning("You have already voted for this track.")
                                else:
                                    df_votes.loc[index, "voted_by"] += ", " + user_name
                                    df_votes.loc[index, "votes"] += 1

                            # Add track to vote list if not already there
                            else:
                                df_new_vote = pd.DataFrame.from_dict(
                                    {
                                        "name": [track_info["name"]],
                                        "artist": [track_info["artist"]],
                                        "url": [track_info["url"]],
                                        "votes": [1],
                                        "added_at": [
                                            datetime.now().strftime("%Y-%m-%d")
                                        ],
                                        "voted_by": [user_name],
                                    }
                                )
                                df_votes = pd.concat([df_votes, df_new_vote])
                    else:
                        st.warning(track_check[1])
            else:
                st.warning("Track not found. Please try again.")
        conn.update(data=df_votes)
        df_votes = conn.read(ttl=0)

        # Add track to playlist if enough votes
        for index, row in df_votes.iterrows():
            if row["votes"] > 4:
                df_votes.drop(index, inplace=True)
                conn.update(data=df_votes)
                df_votes = conn.read(ttl=0)
                st.success(add_track_to_playlist(sp, playlist_id, row["url"]))

        # Show votes
        df_votes["added_at"] = df_votes["added_at"].apply(parse_date)
        filtered_df = df_votes[df_votes["added_at"] >= seven_days_ago].sort_values(
            by=["votes", "added_at"], ascending=[False, True]
        )
        if len(filtered_df):
            st.dataframe(
                filtered_df,
                column_config={
                    "name": "Name",
                    "artist": "Artist",
                    "url": st.column_config.LinkColumn(
                        "URL", display_text="Open in Spotify"
                    ),
                    "votes": "Votes",
                    "added_at": st.column_config.DatetimeColumn(
                        "Added At", format="YYYY-MM-DD"
                    ),
                    "voted_by": "Voted By",
                },
                hide_index=True,
                use_container_width=True,
            )


with tab2:
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


with tab3:
    ## Bar chart
    if "bar_selection" not in st.session_state:
        st.session_state.bar_selection = "added_by"
    st.radio(
        "Select column",
        key="bar_selection",
        options=["added_by", "artist", "album", "release_year"],
    )
    df_plot = df_tracks[st.session_state.bar_selection].value_counts().reset_index()
    df_plot.columns = [st.session_state.bar_selection, "Count"]
    st.bar_chart(
        df_plot,
        x=st.session_state.bar_selection,
        y="Count",
    )
