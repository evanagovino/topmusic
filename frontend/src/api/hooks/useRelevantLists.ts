import { useQuery } from '@tanstack/react-query'
import client from '../client'
import type { ListsResponse } from '../types'

interface RelevantListsParams {
  minYear: number
  maxYear: number
  genre?: string[]
  subgenre?: string[]
  publication?: string[]
}

export function useRelevantLists(params: RelevantListsParams) {
  const { minYear, maxYear, genre, subgenre, publication } = params

  return useQuery({
    queryKey: ['relevantLists', minYear, maxYear, genre, subgenre, publication],
    queryFn: async () => {
      const searchParams = new URLSearchParams()
      searchParams.set('min_year', String(minYear))
      searchParams.set('max_year', String(maxYear))
      searchParams.set('ignore_monthly_lists', String(minYear !== maxYear))

      if (genre?.length) {
        genre.forEach((g) => searchParams.append('genre', g))
      } else {
        searchParams.append('genre', '')
      }
      if (subgenre?.length) {
        subgenre.forEach((s) => searchParams.append('subgenre', s))
      } else {
        searchParams.append('subgenre', '')
      }
      if (publication?.length) {
        publication.forEach((p) => searchParams.append('publication', p))
      } else {
        searchParams.append('publication', '')
      }

      const { data } = await client.get<ListsResponse>(
        `/web/get_relevant_lists/?${searchParams.toString()}`,
      )
      return data.lists
    },
  })
}
