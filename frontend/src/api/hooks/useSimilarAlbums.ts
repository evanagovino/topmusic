import { useQuery } from '@tanstack/react-query'
import client from '../client'
import type { AlbumsListResponse } from '../types'

export function useSimilarAlbums(albumId: string | null, nAlbums = 25) {
  return useQuery({
    queryKey: ['similarAlbums', albumId, nAlbums],
    queryFn: async () => {
      const { data } = await client.get<AlbumsListResponse>(
        `/web/get_similar_albums/${albumId}?n_albums=${nAlbums}`,
      )
      return data.albums
    },
    enabled: !!albumId,
  })
}
