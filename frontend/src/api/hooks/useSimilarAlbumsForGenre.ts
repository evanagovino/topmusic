import { useQuery } from '@tanstack/react-query'
import client from '../client'

interface SimilarAlbum {
  album_key: string
  artist: string
  album: string
  genre: string
  year: number
  subgenre: string
  image_url: string
  apple_music_album_id: string
  apple_music_album_url: string
}

interface SimilarAlbumsResponse {
  albums: SimilarAlbum[]
}

export function useSimilarAlbumsForGenre(albumKeys: string[], enabled: boolean = true) {
  return useQuery({
    queryKey: ['similarAlbumsForGenre', albumKeys],
    queryFn: async () => {
      const sp = new URLSearchParams()
      albumKeys.forEach((key) => sp.append('album_keys', key))
      const { data } = await client.get<SimilarAlbumsResponse>(
        `/web/get_similar_albums_for_user_genre/?${sp.toString()}`,
      )
      return data.albums
    },
    enabled: enabled && albumKeys.length > 0,
    staleTime: 10 * 60 * 1000,
  })
}
