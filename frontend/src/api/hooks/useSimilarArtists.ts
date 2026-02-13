import { useQuery } from '@tanstack/react-query'
import client from '../client'
import type { ArtistsListResponse } from '../types'

export function useSimilarArtists(artistId: string | null, nArtists = 25) {
  return useQuery({
    queryKey: ['similarArtists', artistId, nArtists],
    queryFn: async () => {
      const { data } = await client.get<ArtistsListResponse>(
        `/web/get_similar_artists/${artistId}?n_artists=${nArtists}`,
      )
      return data.artists
    },
    enabled: !!artistId,
  })
}
