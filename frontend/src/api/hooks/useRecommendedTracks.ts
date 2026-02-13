import { useQuery } from '@tanstack/react-query'
import client from '../client'
import type { TracksListResponse } from '../types'

export function useRecommendedTracks(artistId: string | null) {
  return useQuery({
    queryKey: ['recommendedTracks', artistId],
    queryFn: async () => {
      const { data } = await client.get<TracksListResponse>(
        `/app/get_recommended_tracks/?artist_id=${artistId}`,
      )
      return data.tracks
    },
    enabled: !!artistId,
  })
}
