import { useQuery } from '@tanstack/react-query'
import client from '../client'
import type { ArtistsResponse } from '../types'

export function useArtists() {
  return useQuery({
    queryKey: ['artists'],
    queryFn: async () => {
      const { data } = await client.get<ArtistsResponse>('/web/artists/')
      return data.artists
    },
  })
}
