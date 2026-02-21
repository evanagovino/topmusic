/* global MusicKit */

declare global {
  interface Window {
    MusicKit: typeof MusicKit
  }
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace MusicKit {
    function configure(config: {
      developerToken: string
      app: { name: string; build: string }
    }): Promise<MusicKitInstance>
    function getInstance(): MusicKitInstance

    interface MusicKitMediaItem {
      id: string
      title: string
      artistName: string
      albumName: string
      artworkURL?: string
      artwork?: { url: string }
      playbackDuration: number
    }

    interface MusicKitPlayer {
      currentPlaybackTime: number
      currentPlaybackDuration: number
      nowPlayingItem: MusicKitMediaItem | null
      isPlaying: boolean
      queue: { items: MusicKitMediaItem[] }
    }

    interface MusicKitInstance {
      isAuthorized: boolean
      developerToken: string
      musicUserToken: string
      player: MusicKitPlayer
      authorize(): Promise<string>
      unauthorize(): Promise<void>
      setQueue(options: {
        songs?: string[]
        startPlaying?: boolean
        startWith?: number
      }): Promise<void>
      play(): Promise<void>
      pause(): void
      stop(): Promise<void>
      skipToNextItem(): Promise<void>
      skipToPreviousItem(): Promise<void>
      seekToTime(time: number): Promise<void>
      addEventListener(event: string, callback: (...args: any[]) => void): void
      removeEventListener(event: string, callback: (...args: any[]) => void): void
      nowPlayingItem: MusicKitMediaItem | null
      queue: { items: MusicKitMediaItem[]; position: number }
    }
  }
}

let scriptLoaded = false
let scriptLoading: Promise<void> | null = null

/**
 * Dynamically load the MusicKit JS script from Apple's CDN.
 * Returns a promise that resolves once the script is ready.
 */
export function loadMusicKit(): Promise<void> {
  if (scriptLoaded && window.MusicKit) {
    return Promise.resolve()
  }
  if (scriptLoading) {
    return scriptLoading
  }

  scriptLoading = new Promise<void>((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://js-cdn.music.apple.com/musickit/v3/musickit.js'
    script.async = true

    script.onload = () => {
      // MusicKit fires a 'musickitloaded' event, but the script onload
      // may fire before the global is ready. Poll briefly.
      const check = () => {
        if (window.MusicKit) {
          scriptLoaded = true
          resolve()
        } else {
          setTimeout(check, 50)
        }
      }
      check()
    }

    script.onerror = () => {
      scriptLoading = null
      reject(new Error('Failed to load MusicKit JS'))
    }

    document.head.appendChild(script)
  })

  return scriptLoading
}

/**
 * Configure MusicKit with a developer token and return the singleton instance.
 */
export async function configureMusicKit(developerToken: string): Promise<MusicKit.MusicKitInstance> {
  const instance = await MusicKit.configure({
    developerToken,
    app: { name: 'TopMusic', build: '1.0.0' },
  })
  return instance
}

/**
 * Create an Apple Music playlist directly from the browser using MusicKit tokens.
 */
export async function createPlaylist(
  instance: MusicKit.MusicKitInstance,
  playlistName: string,
  trackIds: string[],
): Promise<boolean> {
  const tracksData = trackIds.map((id) => ({ id, type: 'songs' }))

  const response = await fetch(
    'https://api.music.apple.com/v1/me/library/playlists',
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${instance.developerToken}`,
        'Music-User-Token': instance.musicUserToken,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        attributes: {
          name: `${playlistName} Radio`,
          description: 'Created via TopMusic',
        },
        relationships: {
          tracks: { data: tracksData },
        },
      }),
    },
  )

  return response.status === 201 || response.ok
}

/**
 * Love a song (add a positive rating) via the Apple Music API.
 */
export async function loveSong(
  instance: MusicKit.MusicKitInstance,
  songId: string,
): Promise<boolean> {
  const response = await fetch(
    `https://api.music.apple.com/v1/me/ratings/songs/${songId}`,
    {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${instance.developerToken}`,
        'Music-User-Token': instance.musicUserToken,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type: 'rating',
        attributes: { value: 1 },
      }),
    },
  )
  if (!response.ok) {
    const body = await response.text().catch(() => '(unreadable)')
    console.error(`[loveSong] ${response.status} ${response.statusText} — ${body}`)
  }
  return response.ok
}

/**
 * Remove a song's rating (unlove) via the Apple Music API.
 */
export async function unloveSong(
  instance: MusicKit.MusicKitInstance,
  songId: string,
): Promise<boolean> {
  const response = await fetch(
    `https://api.music.apple.com/v1/me/ratings/songs/${songId}`,
    {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${instance.developerToken}`,
        'Music-User-Token': instance.musicUserToken,
      },
    },
  )
  if (!response.ok && response.status !== 204) {
    const body = await response.text().catch(() => '(unreadable)')
    console.error(`[unloveSong] ${response.status} ${response.statusText} — ${body}`)
  }
  return response.ok || response.status === 204
}

export {}
