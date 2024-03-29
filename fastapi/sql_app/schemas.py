from typing import List, Union

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

class TrackDetails(BaseModel):
    track_id: str
    artist_id: str
    track_name: str
    track_popularity: int
    genre: str
    subgenre: str
    year: int
    artist: str
    image_url: str

class Albums(BaseModel):
    albums: dict

    class Config:
        orm_mode = True

class AlbumsList(BaseModel):
    albums: list

    class Config:
        orm_mode = True