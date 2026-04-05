import requests

def get_recently_played_tracks(
    user_token: str,
    developer_token: str,
    track_limit: int = 100,
    storefront: str = "us"
) -> list[dict]:
    """
    Fetches recently played tracks from Apple Music API with pagination.

    Args:
        user_token: Apple Music user token (MusicKit user token)
        developer_token: Apple Music developer JWT token
        track_limit: Maximum number of tracks to fetch (default: 100)
        storefront: Apple Music storefront/country code (default: "us")

    Returns:
        List of track objects up to the specified limit
    """
    BASE_URL = "https://api.music.apple.com/v1/me/recent/played/tracks"
    PAGE_SIZE = 30  # API max per request

    headers = {
        "Authorization": f"Bearer {developer_token}",
        "Music-User-Token": user_token,
    }

    all_tracks = []
    offset = 0

    while len(all_tracks) < track_limit:
        # Calculate how many tracks to request this page
        remaining = track_limit - len(all_tracks)
        page_limit = min(PAGE_SIZE, remaining)

        params = {
            "limit": page_limit,
            "offset": offset,
        }

        response = requests.get(BASE_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        tracks = data.get("data", [])
        if not tracks:
            break  # No more tracks available

        all_tracks.extend(tracks)

        # Stop if there's no next page
        if not data.get("next"):
            break

        # Advance offset for next page
        offset += len(tracks)

    return all_tracks[:track_limit]