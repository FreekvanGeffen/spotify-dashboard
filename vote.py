"""Facilities to interact with the `Spotify` API."""

import os

import spotipy
import streamlit as st
from spotipy.oauth2 import SpotifyOAuth


def create_spotipy_oauth_client():
    sp_oauth = SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="playlist-modify-public playlist-modify-private",
        open_browser=False,
    )
    auth_url = sp_oauth.get_authorize_url()
    st.markdown(f"[Authorize Spotify]({auth_url})")

    if "code" in st.query_params:
        response = (
            f"https://hetevangelievanjob.streamlit.app/?code={st.query_params['code']}"
        )
    else:
        response = st.text_input("Copy the URL you were redirected to:")

    if response:
        # Extract the authorization code from the response URL
        code = sp_oauth.parse_response_code(response)
        if not code:
            st.error("Failed to parse the authorization code from the response URL")
            return None

        # Use the authorization code to get the access token
        try:
            token_info = sp_oauth.get_access_token(code, as_dict=False)
            if not token_info:
                st.error("Failed to get access token")
                return None
            return spotipy.Spotify(auth=token_info)
        except Exception as e:
            st.error(f"An error occurred: {e}")
            return None


def get_playlist(sp: spotipy, playlist_id: str) -> dict:
    """Fetch all playlist data.

    Args:
    ----
        sp: Spotipy client
        playlist_id: Spotify playlist ID

    Returns:
    -------
        Spotify playlist object

    """
    return sp.playlist(playlist_id)


def milliseconds_to_mm_ss(milliseconds: str) -> str:
    """Convert milliseconds to mm:ss."""
    total_seconds = milliseconds / 1000
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)

    # Format the result as mm:ss
    return f"{minutes:02}:{seconds:02}"


def get_track_info(sp: spotipy, playlist: dict) -> list[dict]:
    """Get tracks info from playlist dictionary.

    Args:
    ----
        sp: Spotipy client
        playlist: Playlist dictionary

    Returns:
    -------
        Tracks info

    """
    tracks = list(playlist["tracks"]["items"])
    track_info = []

    # Fetch all tracks in the playlist
    while "tracks" in playlist and playlist["tracks"]["next"]:
        playlist = sp.next(playlist["tracks"])
        if "items" in playlist:
            tracks += list(playlist["items"])

    # Select interesting track details
    for track in tracks:
        track_details = {
            "name": track["track"]["name"],
            "artist": track["track"]["artists"][0]["name"],
            "album": track["track"]["album"]["name"],
            "release_date": track["track"]["album"]["release_date"],
            "duration": milliseconds_to_mm_ss(track["track"]["duration_ms"]),
            "added_by": track["added_by"]["id"],
            "added_at": str(track["added_at"])[:10],
            "url": track["track"]["external_urls"]["spotify"],
            "image": track["track"]["album"]["images"][0]["url"],
        }
        track_info.append(track_details)

    return track_info


def check_track_in_playlist(sp: spotipy, playlist_id: str, track_url: str) -> bool:
    """Check if a track is already in a playlist.

    Args:
    ----
        sp: Spotipy client
        playlist_id: Spotify playlist ID
        track_url: Spotify track URL
    """
    playlist_info = get_playlist(sp, playlist_id)
    track_info = get_track_info(sp, playlist_info)
    existings_urls = [track["url"] for track in track_info]
    if track_url in existings_urls:
        return (False, "Track already in playlist.")
    else:
        return (True, "Track not in playlist.")


def add_track_to_playlist(sp: spotipy, playlist_id: str, track_url: str) -> str:
    """Add a track to a playlist.

    Args:
    ----
        sp: Spotipy client
        playlist_id: Spotify playlist ID
        track_url: Spotify track url

    """
    sp.playlist_add_items(playlist_id, [track_url])
    return "Track succesfully added to playlist."


def search_track(sp, track_name, artist) -> str:
    """Search for a track by name.

    Args:
    ----
        sp: Spotipy client
        track_name: Track name
        artist: Artist name

    Returns:
    -------
        Track URL

    """
    query = f"track:{track_name} artist:{artist}"
    result = sp.search(query, limit=1)
    if result["tracks"]["total"] < 1:
        return None

    track_info = {
        "name": result["tracks"]["items"][0]["name"],
        "artist": result["tracks"]["items"][0]["artists"][0]["name"],
        "album": result["tracks"]["items"][0]["album"]["name"],
        "url": result["tracks"]["items"][0]["external_urls"]["spotify"],
        "image": result["tracks"]["items"][0]["album"]["images"][0]["url"],
        "release_date": result["tracks"]["items"][0]["album"]["release_date"],
    }
    return track_info
