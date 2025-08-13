from ..database import get_db
from .. import crud, models, schemas
from fastapi import Depends, FastAPI, HTTPException, Query, APIRouter
from sqlalchemy.orm import Session
from typing import List
from ._utils import pull_relevant_albums_new, unpack_albums_new, return_tracks_new
import numpy as np
import json

router = APIRouter(prefix="/v2", tags=["v2"])

@router.get("/get_relevant_albums/", response_model=schemas.AlbumsList)
def get_relevant_albums(min_year: int, 
                        max_year: int, 
                        genre: List[str] = Query([None]), 
                        subgenre: List[str] = Query([None]), 
                        publication: List[str] =Query([None]), 
                        list: List[str] = Query([None]), 
                        points_weight: float = 0.5,
                        randomize: bool = False,
                        order_by_recency: bool = False,
                        album_limit: int = 50,
                        db: Session = Depends(get_db)
                        ):
    """
    Return a list of relevant albums given a set of inputs

    Returned in list format, used for Flutterflow
    """
    x = pull_relevant_albums_new(db=db, 
                                 min_year=min_year,
                                 max_year=max_year, 
                                 genre=genre, 
                                 subgenre=subgenre, 
                                 publication=publication, 
                                 list=list,
                                 points_weight=points_weight,
                                 album_uri_required=False
                                 )
    new_dict = []
    if order_by_recency:
        for value in sorted(x['albums'].items(), key=lambda x: x[1]['album_key'], reverse=True)[:album_limit]:
            new_dict.append(value[1])
    else:
        for value in sorted(x['albums'].items(), key=lambda x: x[1]['weighted_rank'], reverse=True)[:album_limit]:
            new_dict.append(value[1])
    x['albums'] = new_dict
    return x

@router.get("/get_similar_albums/", response_model=schemas.AlbumsList)
def get_similar_albums(album_key: str, 
                      publication_weight: float = 0.7,
                      num_results: int = 10,
                      db: Session = Depends(get_db)):
    x = {}
    x['albums'] = []
    results = crud.get_similar_albums(db=db, album_key=album_key, publication_weight=publication_weight, num_results=num_results)
    for value in results:
        x['albums'].append({
            'album_key': value.album_key,
            'artist': value.artist,
            'album': value.album,
            'genre': value.genre,
            'subgenre': value.subgenre,
            'image_url': value.image_url,
            'spotify_album_id': value.spotify_album_id,
            'apple_music_album_id': value.apple_music_album_id,
            'apple_music_url': value.apple_music_url,
            'mood_distance': value.mood_distance,
            'publication_distance': value.publication_distance
        })
    return x

@router.get("/get_tracks_from_albums/", response_model=schemas.TracksList)
def get_tracks_from_albums(album_keys: List[str] = Query(['']),
                           weighted_rank: bool = True,
                           album_limit: int = 500,
                           track_length: int = 50,
                           shuffle_tracks: bool = True,
                           apple_music_required: bool = True,
                           db: Session = Depends(get_db)):
    """
    Return a list of tracks given a list of albums
    """
    db_albums = crud.get_album_info_new(db=db,
                                        album_keys=album_keys,
                                        apple_music_required=apple_music_required)
    if db_albums is None:
        raise HTTPException(status_code=404, detail="No albums that match criteria")
    x = unpack_albums_new(db_albums, points_weight=0.5)
    album_uris = [i for i in x['albums']]
    print(album_uris)
    if weighted_rank:
        weighted_ranks = [x['albums'][i]['weighted_rank'] for i in x['albums']]
    else:
        weighted_ranks = [1 for i in x]
    tracks = return_tracks_new(db,
                               album_uris,
                                weighted_rank=weighted_ranks, 
                                random_order=True, 
                                track_length=track_length, 
                                replace_albums=True, 
                                weight_albums=True, 
                                weight_tracks=True,
                                album_limit=album_limit,
                                max_songs_per_album=3
                                )
    x = {'tracks': []}
    if shuffle_tracks:
        np.random.shuffle(tracks)
    for track in tracks:
        x['tracks'].append(track)
    return x