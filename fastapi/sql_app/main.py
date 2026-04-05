from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from collections import Counter
import logging

from . import models, crud
from .database import engine, SessionLocal
from .routes import mobile_app, web
from .routes._utils import _get_apple_music_auth_header, _get_apple_music_recently_played_tracks

logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

def refresh_stale_user_preferences():
    db = SessionLocal()
    try:
        stale_users = crud.get_active_stale_users(db)
        for user in stale_users:
            try:
                encoded_heading = _get_apple_music_auth_header(user.api_key)
                developer_token = encoded_heading['developer_token']
                headers = {
                    'Authorization': f'Bearer {developer_token}',
                    'Music-User-Token': user.music_user_token,
                }
                tracks = _get_apple_music_recently_played_tracks(headers, track_limit=100)
                track_ids = list(set([i['id'] for i in tracks]))
                db_tracks = crud.get_track_data_multiple_tracks(db, track_ids=track_ids)
                if len(db_tracks) == 0:
                    continue
                track_dicts = [
                    {feature: getattr(t, feature) for feature in ['apple_music_track_id', 'album_key', 'artist', 'genre']}
                    for t in db_tracks
                ]
                total = len(track_dicts)
                all_results = []
                for artist, count in Counter(t['artist'] for t in track_dicts).most_common(1):
                    all_results.append({
                        'topic': artist,
                        'type': 'artist',
                        'count': count,
                        'rate': count / total,
                        'album_keys': list(set(str(t['album_key']) for t in track_dicts if t['artist'] == artist)),
                    })
                for genre, count in Counter(t['genre'] for t in track_dicts).most_common(2):
                    all_results.append({
                        'topic': genre,
                        'type': 'genre',
                        'count': count,
                        'rate': count / total,
                        'album_keys': list(set(str(t['album_key']) for t in track_dicts if t['genre'] == genre)),
                    })
                crud.upsert_user_listening_preferences(db, api_key=user.api_key, results=all_results)
            except Exception as e:
                logger.warning(f"Failed to refresh preferences for user {user.api_key}: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_stale_user_preferences, 'interval', hours=1)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mobile_app.router)
app.include_router(web.router)