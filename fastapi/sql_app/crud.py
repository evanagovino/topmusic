from sqlalchemy import func, text, cast, String
from sqlalchemy.orm import Session, joinedload, load_only

from . import models, schemas

def get_unique_genres(db: Session):
    return db.query(models.RelevantAlbums.genre, models.RelevantAlbums.subgenre).distinct().order_by(models.RelevantAlbums.genre, models.RelevantAlbums.subgenre).all()

def get_unique_publications(db: Session):
    return db.query(models.RelevantAlbums.publication, models.RelevantAlbums.list).distinct().all()

def get_unique_moods(db: Session):
    return db.query(models.AlbumDescriptors.mood).distinct().order_by(models.AlbumDescriptors.mood).all()

def get_unique_artists_albums(db: Session):
    return db.query(models.TrackFeatures.artist, models.TrackFeatures.artist_id, models.TrackFeatures.album_name, models.TrackFeatures.album_id).distinct().all()

def get_artist_name_ids(db: Session):
    return db.query(models.AppleMusicArtists.artist_name, models.AppleMusicArtists.artist_id).distinct().order_by(models.AppleMusicArtists.artist_name).all()

def get_albums_for_artist(db: Session, artist_id: str):
    return db.query(models.TrackFeatures.album_name, models.TrackFeatures.album_id).filter(models.TrackFeatures.artist_id == artist_id).distinct().all()

def get_artist_id_from_name(db: Session, artist_name: str):
    return db.query(models.TrackFeatures.artist, models.TrackFeatures.artist_id).filter(models.TrackFeatures.artist == artist_name).distinct().all()

def get_artist_id_from_name_new(db: Session, artist_name: str):
    return db.query(models.AppleMusicArtists.artist_name, models.AppleMusicArtists.artist_id).filter(models.AppleMusicArtists.artist_name == artist_name).distinct().all()

def get_all_tracks(db: Session, min_duration: int, max_duration: int):
    return db.query(models.TrackFeatures).filter(models.TrackFeatures.duration >= min_duration).filter(models.TrackFeatures.duration <= max_duration).all()

def get_all_tracks_genre(db: Session, genre: str, min_duration: int, max_duration: int):
    return db.query(models.TrackFeatures).filter(models.TrackFeatures.duration >= min_duration).filter(models.TrackFeatures.duration <= max_duration).filter(models.TrackFeatures.genre == genre).all()

def get_tracks_for_artist(db: Session, artist_id: str):
    return db.query(models.TrackFeatures.album_id, models.TrackFeatures.track_name, models.TrackFeatures.track_id, models.TrackFeatures.track_popularity, models.TrackFeatures.artist_id).filter(models.TrackFeatures.artist_id == artist_id).distinct(models.TrackFeatures.album_id, models.TrackFeatures.track_name, models.TrackFeatures.track_id, models.TrackFeatures.track_popularity).all()

def get_tracks_for_album(db: Session, album_id: str):
    return db.query(models.TrackFeatures.album_id, models.TrackFeatures.track_name, models.TrackFeatures.track_id, models.TrackFeatures.track_popularity, models.TrackFeatures.artist, models.TrackFeatures.album_name, models.TrackFeatures.genre, models.TrackFeatures.subgenre, models.TrackFeatures.year, models.TrackFeatures.image_url, models.TrackFeatures.album_url).filter(models.TrackFeatures.album_id == album_id).distinct().all()

def get_tracks_for_albums(db: Session, album_ids: list, min_duration: int, max_duration: int):
    return db.query(models.TrackFeatures.album_id, models.TrackFeatures.track_name, models.TrackFeatures.track_id, models.TrackFeatures.track_popularity, models.TrackFeatures.artist, models.TrackFeatures.album_name, models.TrackFeatures.genre, models.TrackFeatures.subgenre, models.TrackFeatures.year, models.TrackFeatures.image_url, models.TrackFeatures.album_url).filter(models.TrackFeatures.album_id.in_(album_ids)).filter(models.TrackFeatures.duration >= min_duration).filter(models.TrackFeatures.duration <= max_duration).distinct().all()

def get_tracks_for_albums_new(db: Session, album_keys: list, min_duration: int, max_duration: int):
    return db.query(models.FctTracks.album_key, models.FctTracks.artist, models.FctTracks.album, models.FctTracks.genre, models.FctTracks.subgenre, models.FctTracks.year, models.FctTracks.image_url, models.FctTracks.apple_music_track_id,models.FctTracks.apple_music_album_id, models.FctTracks.apple_music_album_url, models.FctTracks.spotify_album_uri, models.FctTracks.duration_ms, models.FctTracks.apple_music_track_name, models.FctTracks.track_popularity).filter(models.FctTracks.album_key.in_(album_keys)).filter(models.FctTracks.duration_ms >= min_duration).filter(models.FctTracks.duration_ms <= max_duration).distinct().all()

def get_tracks_by_features(db: Session, excluded_genres: list, excluded_subgenres: list, excluded_time_signatures: list, min_danceability: float, max_danceability: float, min_energy: float, max_energy: float, min_speechiness: float, max_speechiness: float, min_acousticness: float, max_acousticness: float, min_instrumentalness: float, max_instrumentalness: float, min_liveness: float, max_liveness: float, min_valence: float, max_valence: float, min_tempo: float, max_tempo: float, min_popularity: int, max_popularity: int, min_duration: int, max_duration: int):
    base_query = db.query(models.TrackFeatures).filter(models.TrackFeatures.danceability_clean >= min_danceability, models.TrackFeatures.danceability_clean <= max_danceability, models.TrackFeatures.energy_clean >= min_energy, models.TrackFeatures.energy_clean <= max_energy, models.TrackFeatures.speechiness_clean >= min_speechiness, models.TrackFeatures.speechiness_clean <= max_speechiness, models.TrackFeatures.acousticness_clean >= min_acousticness, models.TrackFeatures.acousticness_clean <= max_acousticness, models.TrackFeatures.instrumentalness_clean >= min_instrumentalness, models.TrackFeatures.instrumentalness_clean <= max_instrumentalness, models.TrackFeatures.liveness_clean >= min_liveness, models.TrackFeatures.liveness_clean <= max_liveness, models.TrackFeatures.valence_clean >= min_valence, models.TrackFeatures.valence_clean <= max_valence, models.TrackFeatures.valence_clean >= min_valence, models.TrackFeatures.tempo_mapped >= min_tempo, models.TrackFeatures.tempo_mapped <= max_tempo, models.TrackFeatures.tempo_mapped <= max_tempo, models.TrackFeatures.track_popularity >= min_popularity, models.TrackFeatures.track_popularity <= max_popularity, models.TrackFeatures.duration >= min_duration, models.TrackFeatures.duration <= max_duration)
    if len(excluded_genres[0]) > 0:
        base_query = base_query.filter(~models.TrackFeatures.genre.in_(excluded_genres))
    if len(excluded_subgenres[0]) > 0:
        base_query = base_query.filter(~models.TrackFeatures.subgenre.in_(excluded_subgenres))
    if excluded_time_signatures[0] != 0:
        base_query = base_query.filter(~models.TrackFeatures.time_signature_clean.in_(excluded_time_signatures))
    return base_query.all()

def get_relevant_albums(db: Session, min_year: int, max_year: int, genre: list, subgenre: list, publication: list, list: list, mood: list, album_uri_required: bool):
    # Start with a subquery to get distinct album_keys that match filters
    # This avoids JSON column comparison issues
    subquery = db.query(models.FctAlbums.album_key).filter(
        models.FctAlbums.year >= min_year, 
        models.FctAlbums.year <= max_year
    )
    
    # Join and filter on RelevantAlbums if needed
    needs_music_lists_join = len(list[0]) > 0 or len(publication[0]) > 0 or album_uri_required
    if needs_music_lists_join:
        subquery = subquery.join(
            models.RelevantAlbums, 
            cast(models.FctAlbums.album_key, String) == models.RelevantAlbums.album_key
        )
        if len(list[0]) > 0:
            subquery = subquery.filter(models.RelevantAlbums.list.in_(list))
        if len(publication[0]) > 0:
            subquery = subquery.filter(models.RelevantAlbums.publication.in_(publication))
        if album_uri_required:
            subquery = subquery.filter(models.RelevantAlbums.spotify_album_uri.isnot(None))
    
    # Filter on AlbumDescriptors - require ALL selected moods (AND logic, not OR)
    # Note: We always load moods via joinedload below, so moods are always available
    if len(mood[0]) > 0:
        # Use a subquery to find albums that have ALL the requested moods
        # This uses GROUP BY and HAVING to ensure the album has all moods
        mood_subquery = db.query(models.AlbumDescriptors.album_key).filter(
            models.AlbumDescriptors.mood.in_(mood)
        ).group_by(models.AlbumDescriptors.album_key).having(
            func.count(func.distinct(models.AlbumDescriptors.mood)) == len(mood)
        ).subquery()
        
        # Join the subquery to filter albums that have all moods
        subquery = subquery.join(
            mood_subquery,
            models.FctAlbums.album_key == mood_subquery.c.album_key
        )
    
    # Filter on genre/subgenre
    if len(genre[0]) > 0:
        subquery = subquery.filter(models.FctAlbums.genre.in_(genre))
    if len(subgenre[0]) > 0:
        subquery = subquery.filter(models.FctAlbums.subgenre.in_(subgenre))
    
    # Get distinct album_keys from subquery (only selecting album_key avoids JSON column issues)
    album_keys = [row[0] for row in subquery.distinct().all()]
    
    if not album_keys:
        return []
    
    # Now query only the columns we need from FctAlbums with relationships
    # Using load_only() to only load the columns we actually use, which speeds up the query
    # joinedload ensures moods and music_lists are always loaded and available
    base_query = db.query(models.FctAlbums).options(
        load_only(
            models.FctAlbums.album_key,
            models.FctAlbums.year,
            models.FctAlbums.artist,
            models.FctAlbums.album,
            models.FctAlbums.genre,
            models.FctAlbums.subgenre,
            models.FctAlbums.apple_music_album_id,
            models.FctAlbums.apple_music_album_url,
            models.FctAlbums.spotify_album_uri,
            models.FctAlbums.image_url
        ),
        joinedload(models.FctAlbums.music_lists).load_only(
            models.RelevantAlbums.points,
            models.RelevantAlbums.total_points
        ),
        joinedload(models.FctAlbums.moods).load_only(
            models.AlbumDescriptors.mood
        )
    ).filter(models.FctAlbums.album_key.in_(album_keys))
    
    return base_query.all()

def get_relevant_lists(db: Session, min_year: int, max_year: int, genre: list, subgenre: list, publication: list):
    base_query = db.query(models.RelevantAlbums.list).distinct().filter(models.RelevantAlbums.year >= min_year, models.RelevantAlbums.year <= max_year)
    if len(genre[0]) > 0:
        base_query = base_query.filter(models.RelevantAlbums.genre.in_(genre))
    if len(subgenre[0]) > 0:
        base_query = base_query.filter(models.RelevantAlbums.subgenre.in_(subgenre))
    if len(publication[0]) > 0:
        base_query = base_query.filter(models.RelevantAlbums.publication.in_(publication))
    return base_query.all()

def get_album_info(db: Session, album_uris: list):
    base_query = db.query(models.RelevantAlbums.album_uri, models.RelevantAlbums.album_url, models.RelevantAlbums.album_key, models.RelevantAlbums.spotify_deeplink, models.RelevantAlbums.image_url, models.RelevantAlbums.artist, models.RelevantAlbums.album, models.RelevantAlbums.genre, models.RelevantAlbums.subgenre, models.RelevantAlbums.year, func.sum(models.RelevantAlbums.points), func.avg(models.RelevantAlbums.total_points)).filter(models.RelevantAlbums.album_uri.in_(album_uris))
    return base_query.group_by(models.RelevantAlbums.album_uri, models.RelevantAlbums.album_url, models.RelevantAlbums.album_key, models.RelevantAlbums.spotify_deeplink, models.RelevantAlbums.image_url, models.RelevantAlbums.artist, models.RelevantAlbums.album, models.RelevantAlbums.genre, models.RelevantAlbums.subgenre, models.RelevantAlbums.year).all()

def get_album_accolades(db: Session, album_id: str):
    return db.query(models.RelevantAlbums.album_key, models.RelevantAlbums.rank, models.RelevantAlbums.points, models.RelevantAlbums.publication, models.RelevantAlbums.list).filter(models.RelevantAlbums.album_key == album_id).all()

def get_album_accolades_multiple_albums(db: Session, album_ids: list):
    return db.query(models.RelevantAlbums.album_key, models.RelevantAlbums.rank, models.RelevantAlbums.points, models.RelevantAlbums.publication, models.RelevantAlbums.list).filter(models.RelevantAlbums.album_key.in_(album_ids)).all()

def get_similar_artists_by_publication(db: Session):
    return db.query(models.ArtistPublications).all()

def get_similar_artists_by_genre(db: Session):
    return db.query(models.ArtistGenres).all()

def get_similar_genres(db: Session):
    return db.query(models.GenreFeatures).all()

def get_similar_albums_by_publication(db: Session, genre: str = None):
    if genre:
        return db.query(models.AlbumPublications).filter(models.AlbumPublications.genre == genre).all()
    else:
        return db.query(models.AlbumPublications).all()

def get_artist_track_details(db: Session):
    return db.query(models.ArtistFeatures).all()

def get_album_track_details(db: Session, genre: str = None):
    if genre:
        return db.query(models.AlbumFeatures).filter(models.AlbumFeatures.genre == genre).all()
    else:
        return db.query(models.AlbumFeatures).all()

def get_track_data(db: Session, track_id: str):
    return db.query(models.TrackFeatures).filter(models.TrackFeatures.track_id == track_id).all()

def get_relevant_artists(db: Session, search_string: str):
    tsquery = func.plainto_tsquery(f'{search_string}:*')
    print('SEARCHSTRING', search_string)
    print('SEARCHSTRING', f'{search_string}:*')
    print('TSQUERY', tsquery)
    return db.query(models.ArtistPoints).filter(models.ArtistPoints.artist.op("@@")(func.to_tsquery(f'{search_string}:*'))).order_by(models.ArtistPoints.points.desc()).limit(5).all()

def get_similar_albums(db: Session, album_key: str, publication_weight: float, num_results: int):
    query = text(f"""
    SELECT 
        s.album_key,
        s.artist,
        s.album,
        s.genre,
        s.year,
        s.subgenre,
        s.image_url,
        s.spotify_album_id,
        s.apple_music_album_id,
        s.apple_music_url,
        s.mood_vector <-> target.mood_vector AS mood_distance,
        s.publication_vector <=> target.publication_vector AS publication_distance
    FROM dbt.vector_albums s
    CROSS JOIN (
        SELECT mood_vector, publication_vector, genre
        FROM dbt.vector_albums
        WHERE album_key = '{album_key}'
    ) target
    WHERE s.genre = target.genre
    ORDER BY (s.publication_vector <=> target.publication_vector) * {publication_weight} + (s.mood_vector <-> target.mood_vector) * {1-publication_weight}
    LIMIT {num_results};
    """)
    return db.execute(query).fetchall()

def get_similar_artists(db: Session, artist_id: str, genre_weight: float, publication_weight: float, num_results: int):
    query = text(f"""
    SELECT 
        s.artist_id,
        s.artist_name,
        s.mood_vector <-> target.mood_vector AS mood_distance,
        s.publication_vector <=> target.publication_vector AS publication_distance,
        s.genre_vector <=> target.genre_vector genre_distance,
        (s.genre_vector <=> target.genre_vector) * {genre_weight} + (s.publication_vector <-> target.publication_vector) * {publication_weight} + (s.mood_vector <-> target.mood_vector) * {1 - genre_weight - publication_weight} AS total_distance
        FROM dbt.vector_artists s
        CROSS JOIN (
        SELECT mood_vector, publication_vector, genre_vector
        FROM dbt.vector_artists
        WHERE artist_id = '{artist_id}'
        ) target
        ORDER BY (s.genre_vector <=> target.genre_vector) * {genre_weight} + (s.publication_vector <-> target.publication_vector) * {publication_weight} + (s.mood_vector <-> target.mood_vector) * {1 - genre_weight - publication_weight}
        LIMIT {num_results};
    """)
    return db.execute(query).fetchall()

def get_similar_tracks_from_similar_artists(db: Session, artist_id: str, genre_weight: float, publication_weight: float, num_results: int):
    query = text(f"""
    WITH similar_artists AS (
        SELECT 
        s.artist_id,
        s.artist_name,
        s.mood_vector <-> target.mood_vector AS mood_distance,
        s.publication_vector <=> target.publication_vector AS publication_distance,
        s.genre_vector <=> target.genre_vector genre_distance,
        (s.genre_vector <=> target.genre_vector) * {genre_weight} + (s.publication_vector <-> target.publication_vector) * {publication_weight} + (s.mood_vector <-> target.mood_vector) * {1 - genre_weight - publication_weight} AS total_distance
        FROM dbt.vector_artists s
        CROSS JOIN (
        SELECT mood_vector, publication_vector, genre_vector
        FROM dbt.vector_artists
        WHERE artist_id = '{artist_id}'
        ) target
        ORDER BY (s.genre_vector <=> target.genre_vector) * {genre_weight} + (s.publication_vector <-> target.publication_vector) * {publication_weight} + (s.mood_vector <-> target.mood_vector) * {1 - genre_weight - publication_weight}
        LIMIT {num_results}
        )
        SELECT
            DISTINCT
                similar_artists.artist_id,
                similar_artists.artist_name,
                similar_artists.total_distance,
                fct_tracks.album_key,
                fct_tracks.apple_music_album_id,
                fct_tracks.apple_music_album_name,
                fct_tracks.apple_music_track_id,
                fct_tracks.apple_music_track_name,
                fct_tracks.apple_music_album_url,
                fct_tracks.genre,
                fct_tracks.subgenre,
                fct_tracks.track_popularity,
                fct_tracks.image_url,
                fct_tracks.year,
                fct_tracks.duration_ms
        FROM
            similar_artists
        JOIN
            dbt.fct_apple_music_artists
        ON
            similar_artists.artist_id = fct_apple_music_artists.artist_id
        JOIN
            dbt.fct_tracks
        ON
            fct_apple_music_artists.album_id = fct_tracks.apple_music_album_id
        WHERE
            fct_tracks.apple_music_track_id IS NOT NULL
        AND
            fct_tracks.duration_ms >= 60000 AND fct_tracks.duration_ms <= 600000
    """)
    return db.execute(query).fetchall()


def get_album_info_new(db: Session, album_keys: list, apple_music_required: bool):
    base_query = db.query(models.FctAlbums).options(joinedload(models.FctAlbums.moods)).filter(models.FctAlbums.album_key.in_(album_keys))
    if apple_music_required:
        base_query = base_query.filter(models.FctAlbums.apple_music_album_id.isnot(None))
    return base_query.all()

def get_album_info_new_albums_table(db: Session, album_key: str):
    return db.query(models.FctAlbums).options(joinedload(models.FctAlbums.moods)).filter(models.FctAlbums.album_key == album_key).all()

def get_mean_standard_deviation_of_audio_features(db: Session):
    return db.query(func.avg(models.FctAlbums.spotify_danceability_clean), func.stddev(models.FctAlbums.spotify_danceability_clean), func.avg(models.FctAlbums.spotify_energy_clean), func.stddev(models.FctAlbums.spotify_energy_clean), func.avg(models.FctAlbums.spotify_instrumentalness_clean), func.stddev(models.FctAlbums.spotify_instrumentalness_clean), func.avg(models.FctAlbums.spotify_valence_clean), func.stddev(models.FctAlbums.spotify_valence_clean), func.avg(models.FctAlbums.spotify_tempo_clean), func.stddev(models.FctAlbums.spotify_tempo_clean)).filter(models.FctAlbums.spotify_danceability_clean.isnot(None), models.FctAlbums.spotify_energy_clean.isnot(None), models.FctAlbums.spotify_instrumentalness_clean.isnot(None), models.FctAlbums.spotify_valence_clean.isnot(None), models.FctAlbums.spotify_tempo_clean.isnot(None)).all()

def get_all_tracks_new(db: Session, genres: list = []):
    print('Genres', genres)
    base_query = db.query(models.FctTracks).filter(models.FctTracks.apple_music_track_id.isnot(None))
    if len(genres) > 0 and genres[0] != '':
        base_query = base_query.filter(models.FctTracks.genre.in_(genres))
    return base_query.all()

def get_albums_from_search_string(db: Session, search_term: str, num_results: int):
    search_words = search_term.split(' ')
    ts_query = ' & '.join([f"{word}:*" for word in search_words])
    query = text(f"""
    SELECT *, ts_rank(vector_search, query) as rank
    FROM dbt.vector_album_search, websearch_to_tsquery('english', '{ts_query}') query
    WHERE vector_search @@ to_tsquery('english', '{ts_query}')
    ORDER BY rank DESC
    LIMIT {num_results};
    """)
    return db.execute(query).fetchall()
