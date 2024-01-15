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

def get_all_tracks(db: Session):
    return db.query(models.TrackFeatures).all()

def get_tracks_for_artist(db: Session, artist_id: str):
    return db.query(models.TrackFeatures.album_id, models.TrackFeatures.track_name, models.TrackFeatures.track_id, models.TrackFeatures.track_popularity, models.TrackFeatures.artist_id).filter(models.TrackFeatures.artist_id == artist_id).distinct(models.TrackFeatures.album_id, models.TrackFeatures.track_name, models.TrackFeatures.track_id, models.TrackFeatures.track_popularity).all()

def get_tracks_for_album(db: Session, album_id: str):
    return db.query(models.TrackFeatures.album_id, models.TrackFeatures.track_name, models.TrackFeatures.track_id, models.TrackFeatures.track_popularity, models.TrackFeatures.artist, models.TrackFeatures.album_name, models.TrackFeatures.genre, models.TrackFeatures.subgenre, models.TrackFeatures.year, models.TrackFeatures.image_url, models.TrackFeatures.album_url).filter(models.TrackFeatures.album_id == album_id).distinct().all()

def get_tracks_for_albums(db: Session, album_ids: list):
    return db.query(models.TrackFeatures.album_id, models.TrackFeatures.track_name, models.TrackFeatures.track_id, models.TrackFeatures.track_popularity, models.TrackFeatures.artist, models.TrackFeatures.album_name, models.TrackFeatures.genre, models.TrackFeatures.subgenre, models.TrackFeatures.year, models.TrackFeatures.image_url, models.TrackFeatures.album_url).filter(models.TrackFeatures.album_id.in_(album_ids)).distinct().all()

def get_relevant_albums(db: Session, min_year: int, max_year: int, genre: list, subgenre: list, publication: list, list: list):
    base_query = db.query(models.RelevantAlbums.album_uri, models.RelevantAlbums.album_url, models.RelevantAlbums.image_url, models.RelevantAlbums.artist, models.RelevantAlbums.album, models.RelevantAlbums.genre, models.RelevantAlbums.subgenre, models.RelevantAlbums.year, func.sum(models.RelevantAlbums.points), func.avg(models.RelevantAlbums.total_points)).filter(models.RelevantAlbums.year >= min_year, models.RelevantAlbums.year <= max_year)
    if len(genre[0]) > 0:
        base_query = base_query.filter(models.RelevantAlbums.genre.in_(genre))
    if len(subgenre[0]) > 0:
        base_query = base_query.filter(models.RelevantAlbums.subgenre.in_(subgenre))
    if len(list[0]) > 0:
        base_query = base_query.filter(models.RelevantAlbums.list.in_(list))
    if len(publication[0]) > 0:
        base_query = base_query.filter(models.RelevantAlbums.publication.in_(publication))
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