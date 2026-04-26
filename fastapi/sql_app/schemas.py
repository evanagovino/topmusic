from typing import List, Union, Optional

from pydantic import BaseModel

class Genres(BaseModel):
    genres: dict

    class Config:
        orm_mode = True

class GenresList(BaseModel):
    genres: list

    class Config:
        orm_mode = True

class Publications(BaseModel):
    publications: dict

    class Config:
        orm_mode = True

class Artists(BaseModel):
    artists: dict

    class Config:
        orm_mode = True

class ArtistsList(BaseModel):
    artists: list

    class Config:
        orm_mode = True

class Tracks(BaseModel):
    tracks: dict

    class Config:
        orm_mode = True

class TracksList(BaseModel):
    tracks: list

    class Config:
        orm_mode = True

class Lists(BaseModel):
    lists: list

    class Config:
        orm_mode = True

class TracksLLMResponse(BaseModel):
    tracks: list
    explanation: str
    playlist_name: str
    where_conditions: dict

    class Config:
        orm_mode = True

class TrackDetails(BaseModel):
    apple_music_track_id: str
    album_key: int
    artist: str
    album: str
    genre: str
    subgenre: str
    year: int
    image_url: str
    apple_music_album_id: str
    apple_music_album_url: str
    spotify_album_uri: str
    duration_ms: int
    apple_music_track_name: str
    track_popularity: int
    album_points: int
    eligible_points: int
    tempo_raw: float
    danceability_clean: float
    energy_clean: float
    instrumentalness_clean: float
    valence_clean: float
    speechiness_clean: float

class Albums(BaseModel):
    albums: dict

    class Config:
        orm_mode = True

class AlbumsList(BaseModel):
    albums: list

    class Config:
        orm_mode = True

class UserTokenRequest(BaseModel):
    user_token: str

class AudioDescription(BaseModel):
    album_id: str
    audio_descriptors: list
    explanation: str

class Moods(BaseModel):
    moods: list

    class Config:
        orm_mode = True