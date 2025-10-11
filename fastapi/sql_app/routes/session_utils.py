import secrets
import datetime
import os
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Cookie, HTTPException, Header
from typing import Optional
from ._utils import _get_apple_music_auth_header

SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
SESSION_COOKIE_NAME = "apple_music_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

serializer = URLSafeTimedSerializer(SECRET_KEY)

sessions = {}
api_keys = {}

def create_session(user_token: str):
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        'user_token': user_token,
        'created_at': datetime.datetime.now(),
        'expires_at': datetime.datetime.now() + datetime.timedelta(seconds=SESSION_MAX_AGE)
    }
    return session_id

def get_session(session_id: str):
    if session_id not in sessions:
        return None
    session_data = sessions[session_id]
    if session_data['expires_at'] < datetime.datetime.now():
        del sessions[session_id]
        return None
    return session_data

def get_current_session(session_cookie: Optional[str] = Cookie(None, alias=SESSION_COOKIE_NAME)) -> dict:
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        session_id = serializer.loads(session_cookie, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    session_data = get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return session_data

def create_api_key(session_id: str):
    api_key = secrets.token_urlsafe(32)
    api_keys[api_key] = {
        'session_id': session_id,
        'created_at': datetime.datetime.utcnow()
    }
    return api_key

def get_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key not in api_keys:
        raise HTTPException(status_code=401, detail="Invalid or expired API key")
    return api_keys[x_api_key]

def return_all_sessions_api_keys():
    return sessions, api_keys

def get_user_token_developer_token(session_info: dict):
    # Get session data for user
    session_id = session_info['session_id']
    session_data = get_session(session_id)
    user_token = session_data['user_token']
    # Get developer API key
    api_key = os.getenv('API_KEY')
    developer_token_dict = _get_apple_music_auth_header(api_key)
    developer_token = developer_token_dict['developer_token']
    return user_token, developer_token