import { useQuery } from '@tanstack/react-query'
import client from '../client'
import type { MoodsResponse } from '../types'

export function useMoods() {
  return useQuery({
    queryKey: ['moods'],
    queryFn: async () => {
      const { data } = await client.get<MoodsResponse>('/web/moods/')
      return data.moods.sort()
    },
  })
}
