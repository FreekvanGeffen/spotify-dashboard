""" Utility functions for the Spotify Dashboard application. """

import shutil

import git
import pandas as pd


def fetch_spotify_data(repo_url, local_repo_path, file_paths):
    """
    Fetch Spotify data from a Git repository.

    Parameters:
    - repo_url (str): The URL of the Git repository to clone.
    - local_repo_path (str): The local directory path where the repository will be cloned.
    - file_paths (list): A list of file paths relative to the repository root to read.

    Returns:
    - dict: A dictionary containing the contents of the specified files.
    """
    # Clone the Git repository
    shutil.rmtree(local_repo_path, ignore_errors=True)
    repo = git.Repo.clone_from(repo_url, local_repo_path)

    # Read contents of each file
    data = {}
    for file_path in file_paths:
        # Construct full file path
        full_file_path = repo.working_tree_dir + "/" + file_path
        data[file_path] = pd.read_json(full_file_path, orient="records", lines=True)

    # Remove reposity after reading the files
    shutil.rmtree(local_repo_path, ignore_errors=True)

    return data


def display_image(url):
    return f'<img src="{url}" width="50">'
