import { create } from 'zustand'
import { loadMusicKit, configureMusicKit, createPlaylist } from '../utils/musicKit'
import client from '../api/client'

interface AuthState {
  isAuthorized: boolean
  isConfiguring: boolean
  musicInstance: MusicKit.MusicKitInstance | null

  initialize: () => Promise<void>
  authorize: () => Promise<void>
  unauthorize: () => Promise<void>
  createPlaylist: (name: string, trackIds: string[]) => Promise<boolean>
}

export const useAuthStore = create<AuthState>((set, get) => ({
  isAuthorized: false,
  isConfiguring: false,
  musicInstance: null,

  initialize: async () => {
    if (get().musicInstance || get().isConfiguring) return

    set({ isConfiguring: true })
    try {
      // Fetch developer token from backend
      const { data } = await client.get<{ developer_token: string }>(
        '/web/get_developer_token/',
      )

      // Load MusicKit JS script and configure
      await loadMusicKit()
      const instance = await configureMusicKit(data.developer_token)

      set({
        musicInstance: instance,
        isAuthorized: instance.isAuthorized,
        isConfiguring: false,
      })
    } catch {
      set({ isConfiguring: false })
    }
  },

  authorize: async () => {
    const instance = get().musicInstance
    if (!instance) return

    try {
      await instance.authorize()
      set({ isAuthorized: instance.isAuthorized })
    } catch {
      // User cancelled or auth failed
    }
  },

  unauthorize: async () => {
    const instance = get().musicInstance
    if (!instance) return

    try {
      await instance.unauthorize()
      set({ isAuthorized: false })
    } catch {
      set({ isAuthorized: false })
    }
  },

  createPlaylist: async (name: string, trackIds: string[]) => {
    const instance = get().musicInstance
    if (!instance || !instance.isAuthorized) return false

    return createPlaylist(instance, name, trackIds)
  },
}))
