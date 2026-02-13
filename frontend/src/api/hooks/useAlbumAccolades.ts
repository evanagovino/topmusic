import { useQuery } from '@tanstack/react-query'
import client from '../client'
import type { AlbumAccoladesResponse } from '../types'

export function useAlbumAccolades(albumIds: string[]) {
  return useQuery({
    queryKey: ['albumAccolades', albumIds],
    queryFn: async () => {
      const sp = new URLSearchParams()
      albumIds.slice(0, 50).forEach((id) => sp.append('album_ids', id))
      const { data } = await client.get<AlbumAccoladesResponse>(
        `/web/get_album_accolades_multiple_albums/?${sp.toString()}`,
      )
      return data.albums
    },
    enabled: albumIds.length > 0,
  })
}
