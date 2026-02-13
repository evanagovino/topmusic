import { useQuery } from '@tanstack/react-query'
import client from '../client'
import type { TracksListResponse } from '../types'

export function useTracksFromAlbums(albumKeys: string[], albumLimit = 500, enabled = false) {
  return useQuery({
    queryKey: ['tracksFromAlbums', albumKeys, albumLimit],
    queryFn: async () => {
      const sp = new URLSearchParams()
      albumKeys.slice(0, albumLimit).forEach((k) => sp.append('album_keys', k))
      sp.set('album_limit', String(albumLimit))
      const { data } = await client.get<TracksListResponse>(
        `/app/get_tracks_from_albums/?${sp.toString()}`,
      )
      return data.tracks
    },
    enabled: enabled && albumKeys.length > 0,
  })
}
