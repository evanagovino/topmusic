from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas

def get_unique_genres(db: Session):
    return db.query(models.TrackFeatures.genre, models.TrackFeatures.subgenre).distinct().all()

def get_unique_publications(db: Session):
    return db.query(models.RelevantAlbums.publication, models.RelevantAlbums.list).distinct().all()

def get_artist_name_ids(db: Session):
    return db.query(models.TrackFeatures.artist, models.TrackFeatures.artist_id).distinct().all()

def get_albums_for_artist(db: Session, artist_id: str):
    return db.query(models.TrackFeatures.album_name, models.TrackFeatures.album_id).filter(models.TrackFeatures.artist_id == artist_id).distinct().all()

def get_artist_id_from_name(db: Session, artist_name: str):
    return db.query(models.TrackFeatures.artist, models.TrackFeatures.artist_id).filter(models.TrackFeatures.artist == artist_name).distinct().all()

def get_all_tracks(db: Session, min_duration: int, max_duration: int):
    return db.query(models.TrackFeatures).filter(models.TrackFeatures.duration >= min_duration).filter(models.TrackFeatures.duration <= max_duration).all()

def get_all_tracks_genre(db: Session, genre: str, min_duration: int, max_duration: int):
    return db.query(models.TrackFeatures).filter(models.TrackFeatures.duration >= min_duration).filter(models.TrackFeatures.duration <= max_duration).filter(models.TrackFeatures.genre == genre).all()

def get_tracks_for_artist(db: Session, artist_id: str):
    return db.query(models.TrackFeatures.album_id, models.TrackFeatures.track_name, models.TrackFeatures.track_id, models.TrackFeatures.track_popularity, models.TrackFeatures.artist_id).filter(models.TrackFeatures.artist_id == artist_id).distinct(models.TrackFeatures.album_id, models.TrackFeatures.track_name, models.TrackFeatures.track_id, models.TrackFeatures.track_popularity).all()

def get_tracks_for_album(db: Session, album_id: str):
    return db.query(models.TrackFeatures.album_id, models.TrackFeatures.track_name, models.TrackFeatures.track_id, models.TrackFeatures.track_popularity, models.TrackFeatures.artist, models.TrackFeatures.album_name, models.TrackFeatures.genre, models.TrackFeatures.subgenre, models.TrackFeatures.year, models.TrackFeatures.image_url, models.TrackFeatures.album_url).filter(models.TrackFeatures.album_id == album_id).distinct().all()

def get_tracks_for_albums(db: Session, album_ids: list):
    return db.query(models.TrackFeatures.album_id, models.TrackFeatures.track_name, models.TrackFeatures.track_id, models.TrackFeatures.track_popularity, models.TrackFeatures.artist, models.TrackFeatures.album_name, models.TrackFeatures.genre, models.TrackFeatures.subgenre, models.TrackFeatures.year, models.TrackFeatures.image_url, models.TrackFeatures.album_url).filter(models.TrackFeatures.album_id.in_(album_ids)).distinct().all()

def get_tracks_by_features(db: Session, excluded_genres: list, excluded_subgenres: list, excluded_time_signatures: list, min_danceability: float, max_danceability: float, min_energy: float, max_energy: float, min_speechiness: float, max_speechiness: float, min_acousticness: float, max_acousticness: float, min_instrumentalness: float, max_instrumentalness: float, min_liveness: float, max_liveness: float, min_valence: float, max_valence: float, min_tempo: float, max_tempo: float, min_duration: int, max_duration: int):
    base_query = db.query(models.TrackFeatures).filter(models.TrackFeatures.danceability_clean >= min_danceability, models.TrackFeatures.danceability_clean <= max_danceability, models.TrackFeatures.energy_clean >= min_energy, models.TrackFeatures.energy_clean <= max_energy, models.TrackFeatures.speechiness_clean >= min_speechiness, models.TrackFeatures.speechiness_clean <= max_speechiness, models.TrackFeatures.acousticness_clean >= min_acousticness, models.TrackFeatures.acousticness_clean <= max_acousticness, models.TrackFeatures.instrumentalness_clean >= min_instrumentalness, models.TrackFeatures.instrumentalness_clean <= max_instrumentalness, models.TrackFeatures.liveness_clean >= min_liveness, models.TrackFeatures.liveness_clean <= max_liveness, models.TrackFeatures.valence_clean >= min_valence, models.TrackFeatures.valence_clean <= max_valence, models.TrackFeatures.valence_clean >= min_valence, models.TrackFeatures.tempo_mapped >= min_tempo, models.TrackFeatures.tempo_mapped <= max_tempo, models.TrackFeatures.tempo_mapped <= max_tempo, models.TrackFeatures.duration >= min_duration, models.TrackFeatures.duration >= max_duration)
    if len(excluded_genres[0]) > 0:
        base_query = base_query.filter(~models.TrackFeatures.genre.in_(excluded_genres))
    if len(excluded_subgenres[0]) > 0:
        base_query = base_query.filter(~models.TrackFeatures.subgenre.in_(excluded_subgenres))
    if excluded_time_signatures[0] != 0:
        base_query = base_query.filter(~models.TrackFeatures.time_signature_clean.in_(excluded_time_signatures))
    return base_query.all()

def get_relevant_albums(db: Session, min_year: int, max_year: int, genre: list, subgenre: list, publication: list, list: list, album_uri_required: bool):
    base_query = db.query(models.RelevantAlbums.album_uri, models.RelevantAlbums.album_url, models.RelevantAlbums.image_url, models.RelevantAlbums.artist, models.RelevantAlbums.album, models.RelevantAlbums.genre, models.RelevantAlbums.subgenre, models.RelevantAlbums.year, func.sum(models.RelevantAlbums.points), func.avg(models.RelevantAlbums.total_points)).filter(models.RelevantAlbums.year >= min_year, models.RelevantAlbums.year <= max_year)
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
    return base_query.group_by(models.RelevantAlbums.album_uri, models.RelevantAlbums.album_url, models.RelevantAlbums.image_url, models.RelevantAlbums.artist, models.RelevantAlbums.album, models.RelevantAlbums.genre, models.RelevantAlbums.subgenre, models.RelevantAlbums.year).all()

def get_album_accolades(db: Session, album_id: str):
    return db.query(models.RelevantAlbums.album_uri, models.RelevantAlbums.rank, models.RelevantAlbums.points, models.RelevantAlbums.publication, models.RelevantAlbums.list).filter(models.RelevantAlbums.album_uri == album_id).all()

def get_album_accolades_multiple_albums(db: Session, album_ids: list):
    return db.query(models.RelevantAlbums.album_uri, models.RelevantAlbums.rank, models.RelevantAlbums.points, models.RelevantAlbums.publication, models.RelevantAlbums.list).filter(models.RelevantAlbums.album_uri.in_(album_ids)).all()

def get_similar_artists(db: Session):
    return db.query(models.ArtistPublications).all()

def get_similar_genres(db: Session):
    return db.query(models.GenreFeatures).all()

def get_track_data(db: Session, track_id: str):
    return db.query(models.TrackFeatures).filter(models.TrackFeatures.track_id == track_id).all()