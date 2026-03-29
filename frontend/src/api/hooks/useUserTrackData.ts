import { useQuery } from '@tanstack/react-query'
import client from '../client'

interface UserTrackDataItem {
  topic: string
  type: string
  count: number
  rate: number
}

export function useUserTrackData(musicUserToken: string | null, enabled: boolean) {
  return useQuery({
    queryKey: ['userTrackData', musicUserToken],
    queryFn: async () => {
      const { data } = await client.get<UserTrackDataItem[]>('/web/get_user_track_data/', {
        headers: {
          'Music-User-Token': musicUserToken!,
          'X-API-Key': import.meta.env.VITE_API_KEY ?? '',
        },
      })
      return data
    },
    enabled: enabled && !!musicUserToken,
    retry: false,
  })
}
