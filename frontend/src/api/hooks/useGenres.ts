import { useQuery } from '@tanstack/react-query'
import client from '../client'
import type { GenresResponse } from '../types'

export function useGenres() {
  return useQuery({
    queryKey: ['genres'],
    queryFn: async () => {
      const { data } = await client.get<GenresResponse>('/web/genres/')
      return data.genres
    },
  })
}
