import { useQuery } from '@tanstack/react-query'
import client from '../client'
import type { CustomPromptResponse } from '../types'

export function useCustomPrompt(prompt: string | null) {
  return useQuery({
    queryKey: ['customPrompt', prompt],
    queryFn: async () => {
      const { data } = await client.get<CustomPromptResponse>(
        `/app/create_playlist_from_user_prompt/?user_request=${encodeURIComponent(prompt!)}`,
      )
      return data
    },
    enabled: !!prompt,
  })
}
