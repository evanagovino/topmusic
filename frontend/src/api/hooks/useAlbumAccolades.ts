import { keepPreviousData, useQuery } from '@tanstack/react-query'
import client from '../client'
import type { AlbumAccoladesResponse } from '../types'

export function useAlbumAccolades(albumIds: string[], albumLimit = 50) {
  return useQuery({
    queryKey: ['albumAccolades', albumIds, albumLimit],
    queryFn: async () => {
      const sp = new URLSearchParams()
      albumIds.slice(0, albumLimit).forEach((id) => sp.append('album_ids', id))
      sp.set('album_limit', String(albumLimit))
      const { data } = await client.get<AlbumAccoladesResponse>(
        `/web/get_album_accolades_multiple_albums/?${sp.toString()}`,
      )
      return data.albums
    },
    enabled: albumIds.length > 0,
    placeholderData: keepPreviousData,
  })
}
