from ..database import get_db
from .. import crud, models, schemas
from fastapi import Depends, FastAPI, HTTPException, Query, APIRouter
from sqlalchemy.orm import Session
from typing import List
from ._utils import pull_relevant_albums_new, unpack_albums_new, return_tracks_new, normalize_weights
import numpy as np
import json

router = APIRouter(prefix="/v2", tags=["v2"])

@router.get("/genres/", response_model=schemas.GenresList)
def get_distinct_genres(db: Session = Depends(get_db)):
    db_genre = crud.get_unique_genres_new(db)
    x = {'genres': []}
    for i in db_genre:
        genre = i[0]
        subgenre = i[1]
        genre_not_present = True
        for value in x['genres']:
            if value['name'] == genre:
                if subgenre in value['subgenres']:
                    pass
                else:
                    value['subgenres'].append(subgenre)
                genre_not_present = False
                continue
        if genre_not_present:
            x['genres'].append({'name': genre, 'subgenres': [subgenre]})
    return x

@router.get("/artists/", response_model=schemas.ArtistsList)
def get_distinct_artists(db: Session = Depends(get_db)):
    db_artist = crud.get_artist_name_ids_new(db)
    x = {'artists': []}
    for i in db_artist:
        x['artists'].append({'name': i.artist_name, 'id': i.artist_id})
    return x

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
    if len(db_albums) == 0:
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

@router.get("/get_recommended_tracks/", response_model=schemas.TracksList)
def get_recommended_tracks(artist_id: str = None,
                           genre: str = None, 
                           db: Session = Depends(get_db)
                           ):
    """
    Get recommended tracks for either an artist ID input or a genre input.

    If Artist ID is provided, it will be used and all other inputs will be ignored.

    Used for Flutterflow endpoint.
    """
    if artist_id is None and genre is None:
        raise HTTPException(status_code=404, detail="Artist ID or Genre must be provided")
    if artist_id:
        db_artist = crud.get_similar_tracks_from_similar_artists(db, artist_id=artist_id, genre_weight=0.6, publication_weight=0.3, num_results=50)
        if len(db_artist) == 0:
            raise HTTPException(status_code=404, detail="Artist not found")
        
        # Extract data from CRUD results
        tracks_data = []
        original_artist_tracks = []  # Separate list for original artist tracks
        
        for track in db_artist:
            track_data = {
                'artist_id': track.artist_id,
                'track_id': track.apple_music_track_id,
                'artist_similarity': track.total_distance,
                'track_popularity': track.track_popularity,
                'full_track_data': track  # Keep full data for final output
            }
            
            # Separate original artist tracks (distance should be 0 or very close)
            if track.artist_id == artist_id:
                original_artist_tracks.append(track_data)
            else:
                tracks_data.append(track_data)

        num_original_artist_tracks = min(3, len(original_artist_tracks))
        
        # Sort original artist tracks by popularity (descending) to get the best ones
        original_artist_tracks.sort(key=lambda x: x['track_popularity'], reverse=True)
        original_track_popularities = [t['track_popularity'] for t in original_artist_tracks]
        original_track_weights = normalize_weights(original_track_popularities)
        selected_indices = np.random.choice(len(original_artist_tracks), 
                                                  size=num_original_artist_tracks, 
                                                  replace=False, 
                                                  p=original_track_weights)
        selected_original_tracks = [original_artist_tracks[i] for i in selected_indices]
        
        # Group remaining tracks by artist (excluding original artist)
        artist_tracks = {}
        for track in tracks_data:
            artist_id_key = track['artist_id']
            if artist_id_key not in artist_tracks:
                artist_tracks[artist_id_key] = []
            artist_tracks[artist_id_key].append(track)
        
        # Calculate artist weights for similar artists only
        if len(artist_tracks) > 0:
            artist_similarities = {}
            for artist_id_key, tracks in artist_tracks.items():
                # Use the best (lowest) similarity score for this artist
                artist_similarities[artist_id_key] = min([t['artist_similarity'] for t in tracks])
            
            # Convert distances to weights (inverse and normalize)
            max_distance = max(artist_similarities.values())
            artist_weights = {}
            for artist_id_key, distance in artist_similarities.items():
                # Inverse weight: higher distance = lower weight
                artist_weights[artist_id_key] = max_distance - distance + 0.1  # Add small constant to avoid zero weights
            
            # Normalize artist weights
            artist_ids = list(artist_weights.keys())
            weights = list(artist_weights.values())
            normalized_weights = normalize_weights(weights)
            
            # Select tracks from similar artists (47 tracks since we already have 3 from original)
            selected_similar_tracks = []
            tracks_per_artist = {}  # Track how many tracks selected per artist
            
            for _ in range(50-num_original_artist_tracks):
                if len(artist_ids) == 0:
                    break
                # Choose artist based on similarity weights
                chosen_artist = np.random.choice(artist_ids, p=normalized_weights)
                
                # Check if we've already selected 3 tracks from this artist
                if tracks_per_artist.get(chosen_artist, 0) >= 3:
                    # Remove this artist from future selections
                    artist_index = artist_ids.index(chosen_artist)
                    artist_ids.pop(artist_index)
                    weights.pop(artist_index)
                    if len(artist_ids) == 0:  # No more artists available
                        break
                    normalized_weights = normalize_weights(weights)
                    continue
                
                # Get available tracks for this artist
                available_tracks = artist_tracks[chosen_artist]
                
                # Weight tracks by popularity within this artist
                track_popularities = [t['track_popularity'] for t in available_tracks]
                if max(track_popularities) > min(track_popularities):
                    # Normalize track popularity weights
                    track_weights = normalize_weights(track_popularities)
                    chosen_track = np.random.choice(len(available_tracks), p=track_weights)
                else:
                    # If all tracks have same popularity, choose randomly
                    chosen_track = np.random.choice(len(available_tracks))
                
                selected_track = available_tracks[chosen_track]
                selected_similar_tracks.append(selected_track['full_track_data'])
                
                # Update count for this artist
                tracks_per_artist[chosen_artist] = tracks_per_artist.get(chosen_artist, 0) + 1
                
                # Remove selected track from available tracks to avoid duplicates
                artist_tracks[chosen_artist].remove(selected_track)
                if len(artist_tracks[chosen_artist]) == 0:
                    # No more tracks from this artist, remove from selection
                    artist_index = artist_ids.index(chosen_artist)
                    artist_ids.pop(artist_index)
                    weights.pop(artist_index)
                    if len(artist_ids) == 0:  # No more artists available
                        break
                    normalized_weights = normalize_weights(weights)
        else:
            selected_similar_tracks = []
        
        # Combine tracks: first track from original artist + similar tracks + remaining original tracks
        selected_tracks = []
        
        # First track must be from original artist (best by popularity)
        selected_tracks.append(selected_original_tracks[0]['full_track_data'])
        
        # Add similar artist tracks
        selected_tracks.extend(selected_similar_tracks)
        
        # Add remaining 2 original artist tracks at random positions
        remaining_original = [track['full_track_data'] for track in selected_original_tracks[1:]]
        
        # Insert the remaining original tracks at random positions (but not first)
        for track in remaining_original:
            if len(selected_tracks) == 1:
                # If we only have the first track, add at position 1
                selected_tracks.append(track)
            else:
                # Insert at random position (but not first)
                insert_pos = np.random.randint(1, len(selected_tracks) + 1)
                selected_tracks.insert(insert_pos, track)
        
        # Format response
        track_choices = {'tracks': []}
        for track in selected_tracks:
            track_choices['tracks'].append({
                'artist_id': track.artist_id,
                'artist': track.artist_name,
                'track_id': track.apple_music_track_id,
                'track_name': track.apple_music_track_name,
                'apple_music_album_id': track.apple_music_album_id,
                'album_name': track.apple_music_album_name,
                'album_key': track.album_key,
                'album_url': track.apple_music_album_url,
                'image_url': track.image_url,
                'year': track.year,
                'duration_ms': track.duration_ms,
                'genre': track.genre,
                'subgenre': track.subgenre,
                'track_popularity': track.track_popularity,
                'artist_similarity': track.total_distance,
            })
        
        return track_choices

    elif genre:
        x = pull_relevant_albums_new(db=db, 
                                     min_year=2000,
                                     max_year=2025, 
                                     genre=[genre], 
                                     subgenre=[''], 
                                     publication=[''], 
                                     list=[''],
                                     points_weight=0.5,
                                     album_uri_required=False
                                     )
        new_dict = {}
        for value in sorted(x['albums'].items(), key=lambda x: x[1]['weighted_rank'], reverse=True):
            new_dict[value[0]] = value[1]
        x['albums'] = new_dict
        album_uris = [x['albums'][i]['album_key'] for i in x['albums']]
        weighted_rank = [x['albums'][i]['weighted_rank'] for i in x['albums']]
        if len(album_uris) == 0 or len(weighted_rank) == 0 or len(album_uris) != len(weighted_rank):
            raise HTTPException(status_code=404, detail="Error Processing Album URIs")
        tracks = return_tracks_new(db,
                                   album_uris,
                                   weighted_rank=weighted_rank, 
                                   random_order=True, 
                                   track_length=50, 
                                   replace_albums=True, 
                                   weight_albums=True, 
                                   weight_tracks=True,
                                   album_limit=100,
                                   max_songs_per_album=3
                                  )
        x = {'tracks': []}
        np.random.shuffle(tracks)
        for track in tracks:
            x['tracks'].append(track)
        return x

@router.get("/artist_id_from_artist_name/", response_model=schemas.ArtistsList)
def get_artist_id_from_artist_name(artist_name: str, db: Session = Depends(get_db)):
    db_artist = crud.get_artist_id_from_name_new(db, artist_name=artist_name)
    if db_artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    x = {'artists': []}
    for i in db_artist:
        x['artists'].append({'name': i.artist_name, 'id': i.artist_id})
    return x

@router.get('/get_album_accolades/', response_model=schemas.AlbumsList)
def get_album_accolades(album_id: str = Query(None),
                        n_accolades: int = 10,
                        db: Session = Depends(get_db),
                        exclude_accolades_only_one_point: bool = True):
    """
    Return a dictionary of album accolades given a single album URI
    """
    db_albums = crud.get_album_accolades_new(db, album_id=album_id)
    if db_albums is None:
        raise HTTPException(status_code=404, detail="No albums that match criteria")
    if len(db_albums) == 1:
        exclude_accolades_only_one_point = False
    x = {'albums': []}
    for position, value in enumerate(db_albums):
        new_value = {}
        for feature in ['rank', 'points', 'publication', 'list']:
            new_value[feature] = getattr(value, feature)
        x['albums'].append(new_value)
    new_dict = []
    counting_value = 0
    for value in sorted(x['albums'], key=lambda x: x['points'], reverse=True):
        if exclude_accolades_only_one_point:
            if value['points'] == 1:
                continue
        new_dict.append(value)
        counting_value += 1
        if counting_value >= n_accolades:
            break
    x['albums'] = new_dict
    return x