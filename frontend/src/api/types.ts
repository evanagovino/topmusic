// ── Genre endpoints ──
export interface GenresResponse {
  genres: Record<string, string[]>
}

// ── Artist endpoints ──
export interface ArtistsResponse {
  artists: Record<string, string>
}

export interface ArtistListItem {
  artist_id: string
  genre_similarity?: number
  publication_similarity?: number
  track_details_similarity?: number
  estimated_total_score?: number
}

export interface ArtistsListResponse {
  artists: ArtistListItem[]
}

// ── Publication endpoints ──
export interface PublicationsResponse {
  publications: Record<string, string[]>
}

// ── Mood endpoints ──
export interface MoodsResponse {
  moods: string[]
}

// ── Album types ──
export interface AlbumDict {
  album_key: string
  artist: string
  album: string
  genre: string
  subgenre: string
  year: number
  image_url: string
  apple_music_album_url?: string
  moods?: string[]
  weighted_rank?: number
}

export interface AlbumsResponse {
  albums: Record<string, AlbumDict>
}

export interface AlbumListItem {
  album_key?: string
  album_id?: string
  album?: string
  album_name?: string
  artist: string
  genre?: string
  subgenre?: string
  year?: number
  image_url?: string
  album_url?: string
  apple_music_album_url?: string
  moods?: string[]
  track_details_similarity?: number
  publication_similarity?: number
  estimated_total_score?: number
}

export interface AlbumsListResponse {
  albums: AlbumListItem[]
}

// ── Accolades ──
export interface Accolade {
  rank: string
  points: number
  publication: string
  list: string
}

export interface AlbumAccoladesResponse {
  albums: Record<string, Accolade[]>
}

// ── Track types ──
export interface Track {
  track_id: string
  track_name: string
  artist?: string
  artist_id?: string
  album_name?: string
  album_key?: string
  album_url?: string
  image_url?: string
  genre?: string
  subgenre?: string
  year?: number
  popularity?: number
  track_popularity?: number
  duration_ms?: number
  artist_similarity?: number
  apple_music_album_id?: string
}

export interface TracksListResponse {
  tracks: Track[]
}

// ── Custom prompt response ──
export interface CustomPromptResponse {
  tracks: Track[]
  explanation?: string
  playlist_name?: string
  where_conditions?: string
}

// ── Lists ──
export interface ListsResponse {
  lists: string[]
}

// ── Similar artists (old web dict format used by Data page) ──
export interface SimilarArtistsDictResponse {
  artists: Record<string, number[]>
}

// ── Similar albums (old web dict format used by Data page) ──
export interface SimilarAlbumsDictResponse {
  albums: Record<string, number[]>
}

// ── Artists albums list ──
export interface ArtistAlbumItem {
  album_id: string
  album_name: string
  artist: string
  artist_id: string
}

export interface ArtistsAlbumsListResponse {
  albums: ArtistAlbumItem[]
}
