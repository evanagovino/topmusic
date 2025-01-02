from dataclasses import dataclass

@dataclass
class MoodSettings:
    all_genres: list = ('African', 'Alternative', 'Classical', 'Contemporary', 'Country', 'Electronic', 'Experimental', 'Indie Rock', 'Jazz', 'Latin', 'Metal', 'Pop', 'Rap', 'R&B', 'Reggae', 'Rock')
    musical_features: list = ('min_danceability','max_danceability', 'min_energy', 'max_energy', 'min_speechiness', 'max_speechiness', 'min_acousticness', 'max_acousticness', 'min_instrumentalness', 'max_instrumentalness', 'min_liveness', 'max_liveness', 'min_valence', 'max_valence', 'min_tempo', 'max_tempo')
    excluded_genres: list = (None)
    excluded_subgenres: list = (None)
    default_excluded_genres: list = (None)
    default_excluded_subgenres: list = (None)
    excluded_time_signatures: list = (None)
    min_danceability: float = (None)
    max_danceability: float = (None)
    min_energy: float = (None)
    max_energy: float = (None)
    min_speechiness: float = (None)
    max_speechiness: float = (None)
    min_acousticness: float = (None)
    max_acousticness: float = (None)
    min_instrumentalness: float = (None)
    max_instrumentalness: float = (None)
    min_liveness: float = (None)
    max_liveness: float = (None)
    min_valence: float = (None)
    max_valence: float = (None)
    min_tempo: float = (None)
    max_tempo: float = (None)

    def import_custom_genres(self, genres):
        if len(genres) > 0:
            self.excluded_genres = [i for i in self.all_genres if i not in genres]
            self.excluded_subgenres = []
        else:
            self.excluded_genres = self.default_excluded_genres
            self.excluded_subgenres = self.default_excluded_subgenres

def add_musical_features_to_base_url(mood_object, base_url):
    for feature in dir(mood_object):
        if feature in mood_object.musical_features:
            feature_value = getattr(mood_object, feature)
            if feature_value:
                base_url += f'&{feature}={feature_value}'
    return base_url

def add_genres_to_remove(mood_object, base_url):
    for genre in mood_object.excluded_genres:
        if genre == 'R&B':
            genre = 'R%26B'
        base_url += f'&excluded_genres={genre}'
    for subgenre in mood_object.excluded_subgenres:
        if subgenre == 'R&B':
            subgenre = 'R%26B'
        base_url += f'&excluded_subgenres={subgenre}'
    return base_url

mood_dictionary = {
    'Focus': MoodSettings(
    min_instrumentalness = 0.93,
    min_energy = 0.5,
    min_danceability = 0.65,
    min_valence = 0.4,
    max_tempo = 135,
    default_excluded_genres = ['Indie Rock', 'Rock', 'Pop'],
    default_excluded_subgenres = ['Country']
),
    'Chill': MoodSettings(
    min_valence = 0.6,
    min_tempo = 90,
    max_tempo = 115,
    default_excluded_genres = ['Country', 'Metal'],
    default_excluded_subgenres = ['Rap', 'British Rap']
)
}