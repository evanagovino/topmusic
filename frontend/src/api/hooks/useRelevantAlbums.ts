import { useQuery } from '@tanstack/react-query'
import client from '../client'
import type { AlbumsResponse, AlbumDict } from '../types'

interface RelevantAlbumsParams {
  minYear: number
  maxYear: number
  genre?: string[]
  subgenre?: string[]
  publication?: string[]
  list?: string[]
  mood?: string[]
  enabled?: boolean
}

export function useRelevantAlbums(params: RelevantAlbumsParams) {
  const { minYear, maxYear, genre, subgenre, publication, list, mood, enabled = true } = params

  return useQuery({
    queryKey: ['relevantAlbums', minYear, maxYear, genre, subgenre, publication, list, mood],
    queryFn: async () => {
      const sp = new URLSearchParams()
      sp.set('min_year', String(minYear))
      sp.set('max_year', String(maxYear))

      const appendList = (key: string, arr?: string[]) => {
        if (arr?.length) {
          arr.forEach((v) => sp.append(key, v))
        } else {
          sp.append(key, '')
        }
      }

      appendList('genre', genre)
      appendList('subgenre', subgenre)
      appendList('publication', publication)
      appendList('list', list)
      appendList('mood', mood)

      const { data } = await client.get<AlbumsResponse>(
        `/web/get_relevant_albums/?${sp.toString()}`,
      )

      // Convert dict response to sorted array
      const albums: AlbumDict[] = Object.entries(data.albums).map(([key, album]) => ({
        ...album,
        album_key: key,
      }))
      albums.sort((a, b) => (b.weighted_rank ?? 0) - (a.weighted_rank ?? 0))
      return albums
    },
    enabled,
  })
}
