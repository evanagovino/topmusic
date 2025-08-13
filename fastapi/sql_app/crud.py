from sqlalchemy import func, text
from sqlalchemy.orm import Session

from . import models, schemas

def get_unique_genres(db: Session):
    return db.query(models.TrackFeatures.genre, models.TrackFeatures.subgenre).distinct().all()

def get_unique_genres_new(db: Session):
    return db.query(models.RelevantAlbumsNew.genre, models.RelevantAlbumsNew.subgenre).distinct().all()

def get_unique_publications(db: Session):
    return db.query(models.RelevantAlbums.publication, models.RelevantAlbums.list).distinct().all()

def get_unique_artists_albums(db: Session):
    return db.query(models.TrackFeatures.artist, models.TrackFeatures.artist_id, models.TrackFeatures.album_name, models.TrackFeatures.album_id).distinct().all()

def get_artist_name_ids(db: Session):
    return db.query(models.TrackFeatures.artist, models.TrackFeatures.artist_id).distinct().all()

def get_artist_name_ids_new(db: Session):
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

def get_relevant_albums(db: Session, min_year: int, max_year: int, genre: list, subgenre: list, publication: list, list: list, album_uri_required: bool):
    base_query = db.query(models.RelevantAlbums.album_uri, models.RelevantAlbums.album_url, models.RelevantAlbums.album_key, models.RelevantAlbums.spotify_deeplink, models.RelevantAlbums.image_url, models.RelevantAlbums.artist, models.RelevantAlbums.album, models.RelevantAlbums.genre, models.RelevantAlbums.subgenre, models.RelevantAlbums.year, func.sum(models.RelevantAlbums.points), func.avg(models.RelevantAlbums.total_points)).filter(models.RelevantAlbums.year >= min_year, models.RelevantAlbums.year <= max_year)
    if len(genre[0]) > 0:
        base_query = base_query.filter(models.RelevantAlbums.genre.in_(genre))
    if len(subgenre[0]) > 0:
        base_query = base_query.filter(models.RelevantAlbums.subgenre.in_(subgenre))
    if len(list[0]) > 0:
        base_query = base_query.filter(models.RelevantAlbums.list.in_(list))
    if len(publication[0]) > 0:
        base_query = base_query.filter(models.RelevantAlbums.publication.in_(publication))
    if album_uri_required:
        base_query = base_query.filter(models.RelevantAlbums.album_uri.isnot(None))
    return base_query.group_by(models.RelevantAlbums.album_uri, models.RelevantAlbums.album_url, models.RelevantAlbums.album_key, models.RelevantAlbums.spotify_deeplink, models.RelevantAlbums.image_url, models.RelevantAlbums.artist, models.RelevantAlbums.album, models.RelevantAlbums.genre, models.RelevantAlbums.subgenre, models.RelevantAlbums.year).all()

def get_relevant_albums_new(db: Session, min_year: int, max_year: int, genre: list, subgenre: list, publication: list, list: list, album_uri_required: bool):
    base_query = db.query(models.RelevantAlbumsNew.year, 
                          models.RelevantAlbumsNew.album_key, 
                          models.RelevantAlbumsNew.artist, 
                          models.RelevantAlbumsNew.album, 
                          models.RelevantAlbumsNew.genre, 
                          models.RelevantAlbumsNew.subgenre, 
                          models.RelevantAlbumsNew.apple_music_album_id, 
                          models.RelevantAlbumsNew.apple_music_album_url,
                          models.RelevantAlbumsNew.spotify_album_uri,
                          models.RelevantAlbumsNew.image_url,
                          func.sum(models.RelevantAlbumsNew.points), func.avg(models.RelevantAlbumsNew.total_points)).filter(models.RelevantAlbumsNew.year >= min_year, models.RelevantAlbumsNew.year <= max_year)
    if len(genre[0]) > 0:
        base_query = base_query.filter(models.RelevantAlbumsNew.genre.in_(genre))
    if len(subgenre[0]) > 0:
        base_query = base_query.filter(models.RelevantAlbumsNew.subgenre.in_(subgenre))
    if len(list[0]) > 0:
        base_query = base_query.filter(models.RelevantAlbumsNew.list.in_(list))
    if len(publication[0]) > 0:
        base_query = base_query.filter(models.RelevantAlbumsNew.publication.in_(publication))
    if album_uri_required:
        base_query = base_query.filter(models.RelevantAlbumsNew.album_uri.isnot(None))
    return base_query.group_by(models.RelevantAlbumsNew.year, models.RelevantAlbumsNew.album_key, models.RelevantAlbumsNew.artist, models.RelevantAlbumsNew.album, models.RelevantAlbumsNew.genre, models.RelevantAlbumsNew.subgenre, models.RelevantAlbumsNew.apple_music_album_id, models.RelevantAlbumsNew.apple_music_album_url, models.RelevantAlbumsNew.spotify_album_uri, models.RelevantAlbumsNew.image_url).all()

def get_album_info(db: Session, album_uris: list):
    base_query = db.query(models.RelevantAlbums.album_uri, models.RelevantAlbums.album_url, models.RelevantAlbums.album_key, models.RelevantAlbums.spotify_deeplink, models.RelevantAlbums.image_url, models.RelevantAlbums.artist, models.RelevantAlbums.album, models.RelevantAlbums.genre, models.RelevantAlbums.subgenre, models.RelevantAlbums.year, func.sum(models.RelevantAlbums.points), func.avg(models.RelevantAlbums.total_points)).filter(models.RelevantAlbums.album_uri.in_(album_uris))
    return base_query.group_by(models.RelevantAlbums.album_uri, models.RelevantAlbums.album_url, models.RelevantAlbums.album_key, models.RelevantAlbums.spotify_deeplink, models.RelevantAlbums.image_url, models.RelevantAlbums.artist, models.RelevantAlbums.album, models.RelevantAlbums.genre, models.RelevantAlbums.subgenre, models.RelevantAlbums.year).all()

def get_album_accolades(db: Session, album_id: str):
    return db.query(models.RelevantAlbums.album_uri, models.RelevantAlbums.rank, models.RelevantAlbums.points, models.RelevantAlbums.publication, models.RelevantAlbums.list).filter(models.RelevantAlbums.album_uri == album_id).all()

def get_album_accolades_multiple_albums(db: Session, album_ids: list):
    return db.query(models.RelevantAlbums.album_uri, models.RelevantAlbums.rank, models.RelevantAlbums.points, models.RelevantAlbums.publication, models.RelevantAlbums.list).filter(models.RelevantAlbums.album_uri.in_(album_ids)).all()

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
                fct_tracks.apple_music_album_id,
                fct_tracks.apple_music_album_name,
                fct_tracks.apple_music_track_id,
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
    base_query = db.query(models.FctTracks.album_key, models.FctTracks.artist, models.FctTracks.album, models.FctTracks.genre, models.FctTracks.subgenre, models.FctTracks.year, models.FctTracks.image_url, models.FctTracks.apple_music_album_id, models.FctTracks.apple_music_album_url, models.FctTracks.spotify_album_uri, func.sum(models.FctTracks.album_points), func.avg(models.FctTracks.eligible_points)).filter(models.FctTracks.album_key.in_(album_keys))
    if apple_music_required:
        base_query = base_query.filter(models.FctTracks.apple_music_track_id.isnot(None))
    return base_query.group_by(models.FctTracks.album_key, models.FctTracks.artist, models.FctTracks.album, models.FctTracks.genre, models.FctTracks.subgenre, models.FctTracks.year, models.FctTracks.image_url, models.FctTracks.apple_music_album_id, models.FctTracks.apple_music_album_url, models.FctTracks.spotify_album_uri).all()
