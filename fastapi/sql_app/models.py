from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship
from .database import Base

class GenreFeatures(Base):
    __tablename__ = 'genre_track_details'
    __table_args__ = {"schema": "dbt"}

    genre = Column(String, primary_key=True)
    danceability_raw = Column(Float)
    energy_raw = Column(Float)
    speechiness_raw = Column(Float)
    acousticness_raw = Column(Float)
    instrumentalness_raw = Column(Float)
    liveness_raw = Column(Float)
    valence_raw = Column(Float)
    tempo_raw = Column(Float)
    danceability_clean = Column(Float)
    energy_clean = Column(Float)
    speechiness_clean = Column(Float)
    acousticness_clean = Column(Float)
    instrumentalness_clean = Column(Float)
    liveness_clean = Column(Float)
    valence_clean = Column(Float)
    tempo_clean = Column(Float)

class ArtistFeatures(Base):
    __tablename__ = 'artist_track_details'
    __table_args__ = {"schema": "dbt"}

    artist_id = Column(String, primary_key=True)
    danceability_raw = Column(Float)
    energy_raw = Column(Float)
    speechiness_raw = Column(Float)
    acousticness_raw = Column(Float)
    instrumentalness_raw = Column(Float)
    liveness_raw = Column(Float)
    valence_raw = Column(Float)
    tempo_raw = Column(Float)
    danceability_clean = Column(Float)
    energy_clean = Column(Float)
    speechiness_clean = Column(Float)
    acousticness_clean = Column(Float)
    instrumentalness_clean = Column(Float)
    liveness_clean = Column(Float)
    valence_clean = Column(Float)
    tempo_clean = Column(Float)

class TrackFeatures(Base):
    __tablename__ = "track_data"
    __table_args__ = {"schema": "dbt"}

    track_id = Column(String, primary_key=True)
    artist_id = Column(String)
    track_name = Column(String)
    track_popularity = Column(Integer)
    genre = Column(String)
    subgenre = Column(String)
    year = Column(Integer)
    artist = Column(String)
    artist_id = Column(String)
    album_id = Column(String)
    album_url = Column(String)
    album_name = Column(String)
    image_url = Column(String)
    duration = Column(Float)
    danceability_raw = Column(Float)
    energy_raw = Column(Float)
    speechiness_raw = Column(Float)
    acousticness_raw = Column(Float)
    instrumentalness_raw = Column(Float)
    liveness_raw = Column(Float)
    valence_raw = Column(Float)
    tempo_raw = Column(Float)
    time_signature_raw = Column(Float)
    danceability_clean = Column(Float)
    energy_clean = Column(Float)
    speechiness_clean = Column(Float)
    acousticness_clean = Column(Float)
    instrumentalness_clean = Column(Float)
    liveness_clean = Column(Float)
    valence_clean = Column(Float)
    tempo_clean = Column(Float)
<<<<<<< HEAD
    time_signature_clean = Column(Float)
=======
    time_signature_raw = Column(Float)
>>>>>>> master
    tempo_mapped = Column(Float)

class RelevantAlbums(Base):
    __tablename__ = "music_lists"
    __table_args__ = {"schema": "dbt"}

    album_uri = Column(String, primary_key = True)
    album_url = Column(String)
    image_url = Column(String)
    artist = Column(String)
    album = Column(String)
    genre = Column(String)
    subgenre = Column(String)
    publication = Column(String)
    rank = Column(String)
    list = Column(String)
    year = Column(Integer)
    points = Column(Integer)
    total_points = Column(Integer)

class ArtistPublications(Base):
    __tablename__ = "artist_publication_data"
    __table_args__ = {"schema": "dbt"}

    artist_id = Column(String, primary_key=True)
    publication_data = Column(String)

    



    