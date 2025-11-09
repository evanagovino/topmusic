from ..database import get_db
from .. import crud, models, schemas
from fastapi import Depends, FastAPI, HTTPException, Query, APIRouter
from sqlalchemy.orm import Session
from typing import List
from ._utils import verify_api_key, _get_apple_music_auth_header, pull_relevant_albums, unpack_albums_new, return_tracks_new, normalize_weights
from .llm_utils import test_llm, get_all_tracks, normalize_tempo_column, query_songs_with_features, derive_mood_from_features, generate_playlist_with_audio_features, generate_audio_descriptors_using_features
import numpy as np
import pandas as pd
import json

router = APIRouter(prefix="/app", tags=["Mobile App"])

@router.get("/genres/", response_model=schemas.GenresList)
def get_distinct_genres(db: Session = Depends(get_db)):
    db_genre = crud.get_unique_genres(db)
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
    db_artist = crud.get_artist_name_ids(db)
    x = {'artists': []}
    for i in db_artist:
        x['artists'].append({'name': i.artist_name, 'id': i.artist_id})
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

@router.get("/get_relevant_albums/", response_model=schemas.AlbumsList)
def get_relevant_albums(min_year: int, 
                        max_year: int, 
                        genre: List[str] = Query([None]), 
                        subgenre: List[str] = Query([None]), 
                        publication: List[str] =Query([None]), 
                        list: List[str] = Query([None]), 
                        mood: List[str] = Query([None]),
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
    x = pull_relevant_albums(db=db, 
                             min_year=min_year,
                             max_year=max_year, 
                             genre=genre, 
                             subgenre=subgenre, 
                             publication=publication, 
                             list=list,
                             mood=mood,
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
                      skip_first_album: bool = True,
                      db: Session = Depends(get_db)):
    x = {}
    x['albums'] = []
    results = crud.get_similar_albums(db=db, album_key=album_key, publication_weight=publication_weight, num_results=num_results)
    if skip_first_album:
        results = results[1:]
    for value in results:
        x['albums'].append({
            'album_key': value.album_key,
            'artist': value.artist,
            'album': value.album,
            'genre': value.genre,
            'year': value.year,
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
    # album_uris = [i for i in x['albums']]
    # print(album_uris)
    album_uris = [i.album_key for i in db_albums]
    if weighted_rank:
        weighted_ranks = [x['albums'][i]['weighted_rank'] for i in x['albums']]
        # weighted_ranks = [1 for i in db_albums]
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
        x = pull_relevant_albums(db=db, 
                                 min_year=2000,
                                 max_year=2025, 
                                 genre=[genre], 
                                 subgenre=[''], 
                                 publication=[''], 
                                 list=[''],
                                 mood=[''],
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
    db_albums = crud.get_album_accolades(db, album_id=album_id)
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

@router.get("/get_artists_from_search_string/", response_model=schemas.ArtistsList)
def get_artists_from_search_string(search_string: str, db: Session = Depends(get_db)):
    """
    Return a list of artists given a search string
    """
    db_artists = crud.get_relevant_artists(db, search_string)
    print(len(db_artists))
    x = {'artists': []}
    for i in db_artists:
        x['artists'].append({'name': i.artist, 'id': i.artist_id})
    return x

@router.get("/get_albums_from_search_string/", response_model=schemas.AlbumsList)
def get_albums_from_search_string(search_string: str, num_results: int = 10, db: Session = Depends(get_db)):
    """
    Return a list of artists given a search string
    """
    db_artists = crud.get_albums_from_search_string(db, search_string, num_results)
    x = {'albums': []}
    for i in db_artists:
        x['albums'].append({'name': i.album, 'id': i.album_key, 'artist': i.artist, 'image_url': i.image_url})
    return x

@router.get("/get_apple_music_auth_header/")
def get_apple_music_auth_header(api_key: str = Depends(verify_api_key)):
    return _get_apple_music_auth_header(api_key)

@router.get("/get_album_info/{album_id}", response_model=schemas.AlbumsList)
def get_album_info(album_id: str, db: Session = Depends(get_db)):
    db_album = crud.get_album_info_new_albums_table(db=db, album_key=album_id)
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    x = {'albums': []}
    for i in db_album:
        x['albums'].append({'album_name': i.album, 
                            'album_key': i.album_key,
                            'artist': i.artist,
                            'genre': i.genre,
                            'subgenre': i.subgenre,
                            'year': i.year,
                            'image_url': i.image_url,
                            'apple_music_album_id': i.apple_music_album_id,
                            'apple_music_album_url': i.apple_music_album_url,
                            'spotify_album_uri': i.spotify_album_uri,
                            'moods': [mood.mood for mood in i.moods]})
    return x

@router.get("/get_descriptor_buckets_for_album/{album_id}", response_model=schemas.AudioDescription)
def get_descriptor_buckets_for_album(album_id: str, db: Session = Depends(get_db)):
    #Get Mean and Standard Deviation of Audio Features
    db_audio_features = crud.get_mean_standard_deviation_of_audio_features(db)
    if db_audio_features is None:
        raise HTTPException(status_code=404, detail="No audio features found")
    audio_features = {}
    audio_features['danceability'] = db_audio_features[0][0]
    audio_features['danceability_std'] = db_audio_features[0][1]
    audio_features['energy'] = db_audio_features[0][2]
    audio_features['energy_std'] = db_audio_features[0][3]
    audio_features['instrumentalness'] = db_audio_features[0][4]
    audio_features['instrumentalness_std'] = db_audio_features[0][5]
    audio_features['valence'] = db_audio_features[0][6]
    audio_features['valence_std'] = db_audio_features[0][7]
    audio_features['tempo'] = db_audio_features[0][8]
    audio_features['tempo_std'] = db_audio_features[0][9]
    #Get Descriptor Buckets for Album
    db_album = crud.get_album_info_new_albums_table(db=db, album_key=album_id)
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    album_features = {}
    album_features['danceability'] = db_album[0].spotify_danceability_clean
    album_features['energy'] = db_album[0].spotify_energy_clean
    album_features['instrumentalness'] = db_album[0].spotify_instrumentalness_clean
    album_features['valence'] = db_album[0].spotify_valence_clean
    album_features['tempo'] = db_album[0].spotify_tempo_clean
    album_features['genre'] = db_album[0].genre
    album_features['subgenre'] = db_album[0].subgenre
    album_features['apple_music_editorial_notes_short'] = db_album[0].apple_music_editorial_notes_short
    album_features['apple_music_editorial_notes_standard'] = db_album[0].apple_music_editorial_notes_standard
    audio_descriptors, explanation = generate_audio_descriptors_using_features(album_features, audio_features)
    print('RESPONSE FROM LLM', audio_descriptors, explanation)
    return {'album_id': album_id, 'audio_descriptors': audio_descriptors, 'explanation': explanation}

@router.get("/create_playlist_from_user_prompt/", response_model=schemas.TracksLLMResponse)
def create_playlist_from_user_prompt(user_request: str, genres: List[str] = Query(['']), weigh_by_popularity: bool = True, song_limit: int = 50, debug: bool = False, db: Session = Depends(get_db)):
    tracks_db = get_all_tracks(db, genres=genres)
    print('NUM OF RETURNED SONGS',len(tracks_db['tracks']))
    df = pd.DataFrame(tracks_db['tracks'])
    available_genres = sorted(df['genre'].dropna().unique().tolist())
    available_subgenres = sorted(df['subgenre'].dropna().unique().tolist())
    available_artists = sorted(df['artist'].dropna().unique().tolist())
    df['genre'] = df['genre'].str.lower()
    df['subgenre'] = df['subgenre'].str.lower()
    df['tempo_mapped'] = df.apply(normalize_tempo_column, axis=1)
    audio_features = ['tempo_mapped', 'energy', 'valence', 'danceability', 'instrumentalness', 'popularity']
    df['derived_mood'] = df.apply(derive_mood_from_features, axis=1)
    test_result, explanation, playlist_name, where_conditions, prompt = generate_playlist_with_audio_features(user_request, df, weigh_by_popularity=weigh_by_popularity, song_limit=song_limit)
    if test_result is None:
        raise HTTPException(status_code=404, detail="No tracks found, please try again with different genres or a different request")
    x = {'tracks': [], 'explanation': explanation, 'where_conditions': where_conditions, 'playlist_name': playlist_name}
    if debug:
        x['prompt'] = prompt
    for result in test_result.iterrows():
        x['tracks'].append({
            'track_id': result[1].track_id,
            'track_name': result[1].track_name,
            'artist': result[1].artist,
            'album_name': result[1].album,
            'genre': result[1].genre,
            'subgenre': result[1].subgenre,
            'apple_music_album_id': result[1].apple_music_album_id,
            'album_url': result[1].apple_music_album_url,
            'album_key': result[1].album_key,
            'image_url': result[1].image_url,
            'year': result[1].year,
            'track_popularity': result[1].popularity,
        })
    return x