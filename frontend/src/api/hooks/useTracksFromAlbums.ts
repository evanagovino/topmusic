import { useQuery } from '@tanstack/react-query'
import client from '../client'
import type { TracksListResponse } from '../types'

interface TracksFromAlbumsOptions {
  weightTracks?: boolean
  shuffleTracks?: boolean
}

export function useTracksFromAlbums(
  albumKeys: string[],
  albumLimit = 500,
  enabled = false,
  options: TracksFromAlbumsOptions = {},
) {
  const { weightTracks, shuffleTracks } = options
  return useQuery({
    queryKey: ['tracksFromAlbums', albumKeys, albumLimit, weightTracks, shuffleTracks],
    queryFn: async () => {
      const sp = new URLSearchParams()
      albumKeys.slice(0, albumLimit).forEach((k) => sp.append('album_keys', k))
      sp.set('album_limit', String(albumLimit))
      if (weightTracks !== undefined) {
        sp.set('weight_tracks', String(weightTracks))
      }
      if (shuffleTracks !== undefined) {
        sp.set('shuffle_tracks', String(shuffleTracks))
      }
      const { data } = await client.get<TracksListResponse>(
        `/app/get_tracks_from_albums/?${sp.toString()}`,
      )
      return data.tracks
    },
    enabled: enabled && albumKeys.length > 0,
  })
}
