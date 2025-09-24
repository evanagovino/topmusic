from .. import crud
from fastapi import HTTPException
import time
import re
import json
import requests
import numpy as np
import pandas as pd
import os
from typing import List
from sqlalchemy.orm import Session
import anthropic

OLLAMA_HOST = os.getenv('LLM_ENDPOINT')

def test_llm(prompt, model="llama2:7b", initial_max_tokens=600):
    """Test the LLM with adaptive token limits and retry logic"""
    
    max_attempts = 3
    token_increments = [initial_max_tokens, initial_max_tokens * 1.5, initial_max_tokens * 2, initial_max_tokens * 3]
    
    for attempt, max_tokens in enumerate(token_increments):
        url = f"{OLLAMA_HOST}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": int(max_tokens),
                "temperature": 0.7,
                # "stop": ["}"]  # Stop after JSON closes
            }
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=120)  # Increased timeout
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                response_text = result['response']
                
                print(f"⏱️ Response time: {end_time - start_time:.2f}s (tokens: {max_tokens})")
                
                # Check if response looks complete
                if response_text.strip().endswith('}'):
                    print(f"✅ Complete response received")
                    return response_text
                elif attempt < len(token_increments) - 1:
                    print(f"⚠️ Response may be truncated, retrying with more tokens...")
                    continue
                else:
                    print(f"⚠️ Response may be truncated but using anyway")
                    return response_text
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error (attempt {attempt + 1}): {e}")
            if attempt < len(token_increments) - 1:
                print("Retrying...")
                continue
            return None
    
    return None

def test_llm_claude(prompt):
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    try:
        start_time = time.time()
        response = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": f"{prompt}"}
            ]
        )
        end_time = time.time()
        # return json.loads(response.content[0].text, strict=False)
        return response.content[0].text
            
    except Exception as e:
        print(f"❌ Error): {e}")
        return None
    
    return None

def get_all_tracks(db: Session, genres: List[str] = [], limit: int = None):
    db_tracks = crud.get_all_tracks_new(db, genres=genres)
    if db_tracks is None:
        raise HTTPException(status_code=404, detail="Tracks not found")
    x = {'tracks': []}
    if limit is not None:
        db_tracks = db_tracks[:limit]
    for position, value in enumerate(db_tracks):
        d = {'track_id': value.apple_music_track_id,
             'track_name': value.apple_music_track_name,
             'artist': value.artist,
             'album': value.album,
             'genre': value.genre,
             'subgenre': value.subgenre,
             'year': value.year,
             'tempo': value.tempo_raw,
             'danceability': value.danceability_clean,
             'energy': value.energy_clean,
             'instrumentalness': value.instrumentalness_clean,
             'valence': value.valence_clean,
             'speechiness': value.speechiness_clean,
             'popularity': value.track_popularity,
             'apple_music_album_id': value.apple_music_album_id,
             'apple_music_album_url': value.apple_music_album_url,
             'album_key': value.album_key,
             'image_url': value.image_url,
             }
        x['tracks'].append(d)
    return x

def normalize_column_manual(series):
    """Manually normalize a column to 0-1 range"""
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:  # Handle case where all values are the same
        return pd.Series([0.5] * len(series), index=series.index)
    return (series - min_val) / (max_val - min_val)

def normalize_tempo_column(row):
    genre = row.get('genre')
    tempo = float(row.get('tempo', 0.5))
    if genre == 'electronic' and tempo < 90:
        return max(50, tempo) * 2
    elif genre == 'electronic':
        return min(170, tempo)
    elif genre == 'pop' and tempo >= 140:
        return min(170, tempo) / 2
    elif tempo >= 120:
        return min(170, tempo) / 2
    else:
        return max(50, tempo)

def derive_mood_from_features(row):
    """Derive mood categories from audio features"""
    try:
        energy = float(row.get('energy', 0.5))
        valence = float(row.get('valence', 0.5))
        tempo = float(row.get('tempo_raw', 120))
        danceability = float(row.get('danceability', 0.5))
        
        # Create mood categories based on feature combinations
        if energy > 0.7 and valence > 0.6:
            return 'energetic_happy'
        elif energy > 0.7 and valence < 0.4:
            return 'energetic_aggressive'
        elif energy < 0.3 and valence > 0.6:
            return 'calm_happy'
        elif energy < 0.3 and valence < 0.4:
            return 'calm_sad'
        elif danceability > 0.7:
            return 'danceable'
        elif energy > 0.5 and tempo > 140:
            return 'upbeat'
        elif energy < 0.4 and tempo < 100:
            return 'mellow'
        else:
            return 'neutral'
    except:
        return 'unknown'

def parse_condition(df, condition):
    """Parse a single WHERE condition more precisely"""
    condition = condition.strip()
    
    # Handle different condition types
    if " IN (" in condition.upper():
        # Extract column name and values for IN conditions
        match = re.match(r'(\w+)\s+IN\s*\(\s*(.+?)\s*\)', condition, re.IGNORECASE)
        if match:
            column = match.group(1)
            values_str = match.group(2)
            # Extract quoted values
            values = re.findall(r"'([^']*)'", values_str)
            return 'IN', column, values
    
    elif " BETWEEN " in condition.upper():
        # Handle BETWEEN conditions
        # match = re.match(r'(\w+)\s+BETWEEN\s+(\d+)\s+AND\s+(\d+)', condition, re.IGNORECASE)
        match = re.match(r'(\w+)\s+BETWEEN\s+([\d.]+)\s+AND\s+([\d.]+)', condition, re.IGNORECASE)
        if match:
            column = match.group(1)
            min_val = float(match.group(2))
            max_val = float(match.group(3))
            return 'BETWEEN', column, (min_val, max_val)
    
    elif " > " in condition:
        # Handle greater than conditions
        match = re.match(r'(\w+)\s*>\s*([\d.]+)', condition, re.IGNORECASE)
        if match:
            column = match.group(1)
            value = float(match.group(2))
            return '>', column, value
    
    elif " < " in condition:
        # Handle less than conditions
        match = re.match(r'(\w+)\s*<\s*([\d.]+)', condition, re.IGNORECASE)
        if match:
            column = match.group(1)
            value = float(match.group(2))
            return '<', column, value
    
    elif " >= " in condition:
        # Handle greater than or equal
        match = re.match(r'(\w+)\s*>=\s*([\d.]+)', condition, re.IGNORECASE)
        if match:
            column = match.group(1)
            value = float(match.group(2))
            return '>=', column, value
    
    elif " <= " in condition:
        # Handle less than or equal
        match = re.match(r'(\w+)\s*<=\s*([\d.]+)', condition, re.IGNORECASE)
        if match:
            column = match.group(1)
            value = float(match.group(2))
            return '<=', column, value
    
    elif " LIKE " in condition.upper() or " ILIKE " in condition.upper():
        # Handle LIKE conditions
        match = re.match(r'(\w+)\s+I?LIKE\s+\'([^\']+)\'', condition, re.IGNORECASE)
        if match:
            column = match.group(1)
            pattern = match.group(2)
            return 'LIKE', column, pattern
    
    elif " = " in condition:
        # Handle equality conditions
        match = re.match(r'(\w+)\s*=\s*\'?([^\']+)\'?', condition, re.IGNORECASE)
        if match:
            column = match.group(1)
            value = match.group(2)
            # Try to convert to float if it's a number, otherwise keep as string
            try:
                value = float(value)
            except ValueError:
                pass
            return '=', column, value
    
    return None, None, None

def query_songs_with_features(df, where_conditions=None, weigh_by_popularity=True, song_limit=50):
    """Query songs using your actual feature set with better condition parsing"""
    
    df = df.copy()
    
    if where_conditions:
        print(f"🔍 Applying filters: {where_conditions}")
        
        for condition in where_conditions:
            try:
                operator, column, value = parse_condition(df, condition)
                
                if operator is None:
                    print(f"⚠️ Could not parse condition: '{condition}'")
                    continue
                
                print(f"  Parsing: {column} {operator} {value}")
                
                # Map column names to DataFrame columns (case-insensitive)
                column_mapping = {}
                for col in df.columns:
                    if col not in column_mapping:
                        column_mapping[col.lower()] = col
                
                df_column = column_mapping.get(column.lower())
                if df_column is None:
                    print(f"⚠️ Column '{column}' not found in data")
                    continue
                
                # Apply the filter based on operator
                if operator == 'IN':
                    df = df[df[df_column].isin(value)]
                    print(f"    Filtered to {len(df)} songs where {df_column} in {value}")
                
                elif operator == 'BETWEEN':
                    min_val, max_val = value
                    df = df[(df[df_column] >= min_val) & (df[df_column] <= max_val)]
                    print(f"    Filtered to {len(df)} songs where {df_column} between {min_val} and {max_val}")
                
                elif operator == '>':
                    df = df[df[df_column] > value]
                    print(f"    Filtered to {len(df)} songs where {df_column} > {value}")
                
                elif operator == '<':
                    df = df[df[df_column] < value]
                    print(f"    Filtered to {len(df)} songs where {df_column} < {value}")
                
                elif operator == '>=':
                    df = df[df[df_column] >= value]
                    print(f"    Filtered to {len(df)} songs where {df_column} >= {value}")
                
                elif operator == '<=':
                    df = df[df[df_column] <= value]
                    print(f"    Filtered to {len(df)} songs where {df_column} <= {value}")
                
                elif operator == 'LIKE':
                    df = df[df[df_column].str.contains(value, case=False, na=False)]
                    print(f"    Filtered to {len(df)} songs where {df_column} contains '{value}'")

                elif operator == '=':
                    df = df[df[df_column] == value]
                    print(f"    Filtered to {len(df)} songs where {df_column} = {value}")
                
            except Exception as e:
                print(f"⚠️ Error processing condition '{condition}': {e}")
                continue
    
    # Sort by popularity if available
    if weigh_by_popularity:
        try:
            weights = df['popularity'].values
            min_weight = weights.min()
            if min_weight <= 0:
                weights = weights - min_weight + 0.01
            sampled_indices = np.random.choice(
                            df.index, 
                            size=min(song_limit, len(df)), 
                            replace=False, 
                            p=weights / weights.sum()
                        )
            result = df.loc[sampled_indices]
        except Exception as e:
            print('Error', e)
            result = df.head(song_limit)
    else:
        result = df.head(song_limit)
    print(f"✅ Final result: {len(result)} songs")
    return result

def generate_playlist_with_audio_features(user_request, df, weigh_by_popularity=True, song_limit=50):
    """Generate playlist using your actual audio features"""
    
    # Build context from your actual data
    genre_counts = df['genre'].value_counts().head(15)
    subgenre_counts = df['subgenre'].value_counts().head(10)
    mood_counts = df['derived_mood'].value_counts().head(10)
    
    # Audio feature ranges
    feature_ranges = {}
    for feature in ['energy', 'valence', 'danceability', 'instrumentalness','tempo_mapped', 'popularity']:
        if feature in df.columns:
            feature_ranges[feature] = {
                'min': df[feature].min(),
                'max': df[feature].max(),
                'mean': df[feature].mean()
            }
    
    prompt = f"""You are a music curator with access to a database of {len(df)} songs.
Create a playlist matching this request: "{user_request}"

AVAILABLE DATA:
Genres: {', '.join(genre_counts.index.tolist())}
Subgenres: {', '.join(subgenre_counts.index.tolist())}
Moods: {', '.join(mood_counts.index.tolist())}
Years: {df['year'].min()}-{df['year'].max()}

AUDIO FEATURES (0.0-1.0 scale except Tempo and Popularity):
- Energy: {feature_ranges.get('energy_clean', {}).get('min', 0):.2f}-{feature_ranges.get('energy_clean', {}).get('max', 1):.2f}. Mean of {feature_ranges.get('energy_clean', {}).get('mean', 0.5):.2f} (higher = more energetic)
- Valence: {feature_ranges.get('valence_clean', {}).get('min', 0):.2f}-{feature_ranges.get('valence_clean', {}).get('max', 1):.2f}. Mean of {feature_ranges.get('valence_clean', {}).get('mean', 0.5):.2f} (higher = more positive/happy)
- Danceability: {feature_ranges.get('danceability_clean', {}).get('min', 0):.2f}-{feature_ranges.get('danceability_clean', {}).get('max', 1):.2f}. Mean of {feature_ranges.get('danceability_clean', {}).get('mean', 0.5):.2f} (higher = more danceable)
- Instrumentalness: {feature_ranges.get('instrumentalness_clean', {}).get('min', 0):.2f}-{feature_ranges.get('instrumentalness_clean', {}).get('max', 1):.2f}. Mean of {feature_ranges.get('instrumentalness_clean', {}).get('mean', 0.5):.2f} (higher = less vocals)
- Tempo: {feature_ranges.get('tempo_mapped', {}).get('min', 0):.0f}-{feature_ranges.get('tempo_mapped', {}).get('max', 200):.0f}. Mean of {feature_ranges.get('tempo_mapped', {}).get('mean', 120):.0f} BPM
- Popularity: {feature_ranges.get('popularity', {}).get('min', 0):.0f}-{feature_ranges.get('popularity', {}).get('max', 100):.0f}. Mean of {feature_ranges.get('popularity', {}).get('mean', 50):.0f}

For the request, try and determine which moods it fits from the available moods, and then return songs with those moods, or songs that have similar audio features to the moods requested.

RANGE MAPPING GUIDELINES:
- "calm/relaxing" → Energy BETWEEN 0.1 AND 0.4 (NOT just Energy > something)
- "high energy/intense" → Energy BETWEEN 0.7 AND 1.0
- "moderate energy" → Energy BETWEEN 0.4 AND 0.7
- "sad/melancholy" → Valence BETWEEN 0.0 AND 0.3
- "happy/upbeat" → Valence BETWEEN 0.6 AND 1.0
- "neutral mood" → Valence BETWEEN 0.4 AND 0.6
- "not danceable/ambient" → Danceability BETWEEN 0.0 AND 0.4
- "very danceable" → Danceability BETWEEN 0.7 AND 1.0
- "instrumental" -> Instrumentalness BETWEEN 0.6 AND 1.0

CONDITION EXAMPLES:
- "calm relaxing music" → ["Energy BETWEEN 0.1 AND 0.4", "Valence BETWEEN 0.3 AND 0.7"]
- "high energy workout" → ["Energy BETWEEN 0.7 AND 1.0", "Danceability > 0.6"]
- "sad slow songs" → ["Energy BETWEEN 0.0 AND 0.3", "Valence BETWEEN 0.0 AND 0.3"]


Generate PostgreSQL WHERE conditions. Use exact column names: Energy, Valence, Danceability, Tempo, Genre, Subgenre,Year.
Return ONLY valid JSON:
{{
  "where_conditions": ["condition1", "condition2", "condition3"],
  "explanation": "reasoning about audio features",
  "playlist name": "one or two words description of the playlist"
}}

Request: {user_request}
JSON:"""
    response = test_llm_claude(prompt)
    
    if response:
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                query_spec = json.loads(json_match.group(), strict=False)
                
                print("🤖 LLM Generated:")
                print(json.dumps(query_spec, indent=2))
                
                # Apply to real data
                where_conditions = query_spec.get('where_conditions', [])
                explanation = query_spec.get('explanation', '')
                playlist_name = query_spec.get('playlist name', '')
                print('*******************Where Conditions')
                results = query_songs_with_features(df, where_conditions, weigh_by_popularity=weigh_by_popularity, song_limit=song_limit)
                
                print(f"\n🎵 Playlist Results:")
                for idx, row in results.iterrows():
                    energy = f"E:{row.get('energy', 'N/A'):.2f}" if pd.notna(row.get('energy')) else "E:N/A"
                    valence = f"V:{row.get('valence', 'N/A'):.2f}" if pd.notna(row.get('valence')) else "V:N/A"
                    danceability = f"D:{row.get('danceability', 'N/A'):.2f}" if pd.notna(row.get('danceability')) else "D:N/A"
                    instrumentalness = f"I:{row.get('instrumentalness', 'N/A'):.2f}" if pd.notna(row.get('instrumentalness')) else "I:N/A"
                    tempo = f"T:{row.get('tempo_mapped', 'N/A'):.0f}" if pd.notna(row.get('tempo_mapped')) else "T:N/A"
                    
                    print(f"  {row['artist']} - {row.get('track_name', 'Unknown Track Name')} ({row['genre']}) [{energy}, {valence}, {tempo}, {danceability}, {instrumentalness}]")
                return results, explanation, playlist_name,where_conditions, prompt
            else:
                print('No JSON match returned')
                print(response)
                
        except Exception as e:
            print(f"❌ Error processing LLM response: {e}")
            print("Raw response:", response)
    else:
        print('No response returned.')
    
    return None, None, None, None