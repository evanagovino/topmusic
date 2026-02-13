import { useQuery } from '@tanstack/react-query'
import client from '../client'
import type { PublicationsResponse } from '../types'

export function usePublications() {
  return useQuery({
    queryKey: ['publications'],
    queryFn: async () => {
      const { data } = await client.get<PublicationsResponse>('/web/publications/')
      return data.publications
    },
  })
}
