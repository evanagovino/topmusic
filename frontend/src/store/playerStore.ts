import { create } from 'zustand'
import { useAuthStore } from './authStore'
import { loveSong, unloveSong } from '../utils/musicKit'
import type { Track } from '../api/types'

interface PlayerState {
  isPlaying: boolean
  currentTrack: Track | null
  queue: Track[]
  queueName: string | null
  currentIndex: number
  currentTime: number
  duration: number
  isPlayerVisible: boolean
  lovedTrackIds: Set<string>

  playTracks: (tracks: Track[], name?: string) => Promise<void>
  playTrackAtIndex: (tracks: Track[], index: number) => Promise<void>
  play: () => Promise<void>
  pause: () => void
  togglePlayPause: () => void
  next: () => Promise<void>
  previous: () => Promise<void>
  seekTo: (time: number) => Promise<void>
  toggleLove: (trackId: string) => Promise<void>
  isTrackLoved: (trackId: string) => boolean
  close: () => void
  bindEvents: () => void
  unbindEvents: () => void
}

function getInstance() {
  return useAuthStore.getState().musicInstance
}

const STATE_NAMES: Record<number, string> = {
  0: 'none', 1: 'loading', 2: 'playing', 3: 'paused', 4: 'stopped', 5: 'ended',
  6: 'seeking', 7: 'waiting', 8: 'stalled', 9: 'completed',
}

// Stalled-state recovery: if stuck in waiting/stalled for 4s, stop then play
/**
 * Parse track IDs that Apple couldn't resolve from the NOT_FOUND error message.
 * Example: "NOT_FOUND: One or more items could not be resolved: 1527323477"
 */
function parseBadIds(err: unknown): Set<string> {
  const msg = err instanceof Error ? err.message : String(err)
  const ids = new Set<string>()
  const match = msg.match(/could not be resolved:\s*(.+)$/i)
  if (match) {
    match[1].split(/[,\s]+/).forEach((id) => {
      const trimmed = id.trim()
      if (trimmed) ids.add(trimmed)
    })
  }
  return ids
}

let _stalledTimer: ReturnType<typeof setTimeout> | null = null

function clearStalledTimer() {
  if (_stalledTimer) {
    clearTimeout(_stalledTimer)
    _stalledTimer = null
  }
}

let onPlaybackStateChange: ((e: { state: number }) => void) | null = null
let onPlaybackTimeChange: ((e: { currentPlaybackTime: number }) => void) | null = null
let onPlaybackDurationChange: ((e: { duration: number }) => void) | null = null
let onNowPlayingItemChange: (() => void) | null = null

export const usePlayerStore = create<PlayerState>((set, get) => ({
  isPlaying: false,
  currentTrack: null,
  queue: [],
  queueName: null,
  currentIndex: 0,
  currentTime: 0,
  duration: 0,
  isPlayerVisible: false,
  lovedTrackIds: new Set<string>(),

  playTracks: async (tracks, name) => {
    const instance = getInstance()
    console.log(`[Player] playTracks called, instance=${!!instance}, tracks=${tracks.length}`)
    if (!instance || tracks.length === 0) return

    // Stop current playback and clear old queue before loading new one
    try { await instance.stop() } catch { /* nothing playing */ }

    const validTracks = tracks.filter((t) => t.track_id)
    console.log(`[Player] Valid tracks with track_id: ${validTracks.length}`)
    if (validTracks.length === 0) return

    const trackIds = validTracks.map((t) => t.track_id)

    set({
      queue: validTracks,
      queueName: name ?? null,
      currentIndex: 0,
      currentTrack: validTracks[0],
      isPlayerVisible: true,
      currentTime: 0,
      duration: 0,
    })

    // Retry loop: if Apple can't resolve some track IDs, remove them and retry
    let remaining = validTracks
    for (let attempt = 0; attempt < 5; attempt++) {
      try {
        const ids = remaining.map((t) => t.track_id)
        console.log(`[Player] setQueue attempt ${attempt + 1} with ${ids.length} songs, startPlaying=true`)
        await instance.setQueue({ songs: ids, startPlaying: true })
        console.log('[Player] setQueue resolved, Apple managing playback')
        return
      } catch (err) {
        const badIds = parseBadIds(err)
        if (badIds.size === 0) {
          console.error('[Player] setQueue failed (non-recoverable):', err)
          return
        }
        console.warn(`[Player] Removing ${badIds.size} unresolvable track(s): ${[...badIds].join(', ')}`)
        remaining = remaining.filter((t) => !badIds.has(t.track_id))
        if (remaining.length === 0) {
          console.error('[Player] No playable tracks remain')
          set({ isPlayerVisible: false, currentTrack: null, queue: [] })
          return
        }
        // Update store with cleaned queue
        set({
          queue: remaining,
          currentIndex: 0,
          currentTrack: remaining[0],
        })
      }
    }
    console.error('[Player] setQueue failed after max retries')
  },

  playTrackAtIndex: async (tracks, index) => {
    const instance = getInstance()
    console.log(`[Player] playTrackAtIndex called, index=${index}, instance=${!!instance}`)
    if (!instance || tracks.length === 0) return

    // Stop current playback and clear old queue before loading new one
    try { await instance.stop() } catch { /* nothing playing */ }

    const validTracks = tracks.filter((t) => t.track_id)
    if (validTracks.length === 0) return

    const targetTrack = tracks[index]
    let validIndex = validTracks.findIndex((t) => t === targetTrack)
    if (validIndex < 0) validIndex = 0

    const trackIds = validTracks.map((t) => t.track_id)

    set({
      queue: validTracks,
      currentIndex: validIndex,
      currentTrack: validTracks[validIndex],
      isPlayerVisible: true,
      currentTime: 0,
      duration: 0,
    })

    // Retry loop: if Apple can't resolve some track IDs, remove them and retry
    let remaining = validTracks
    let startIdx = validIndex
    for (let attempt = 0; attempt < 5; attempt++) {
      try {
        const ids = remaining.map((t) => t.track_id)
        console.log(`[Player] setQueue attempt ${attempt + 1} with ${ids.length} songs, startWith=${startIdx}, startPlaying=true`)
        await instance.setQueue({ songs: ids, startWith: startIdx, startPlaying: true })
        console.log('[Player] setQueue resolved')
        return
      } catch (err) {
        const badIds = parseBadIds(err)
        if (badIds.size === 0) {
          console.error('[Player] setQueue failed (non-recoverable):', err)
          return
        }
        console.warn(`[Player] Removing ${badIds.size} unresolvable track(s): ${[...badIds].join(', ')}`)
        // Check if the target track itself was removed
        const targetRemoved = badIds.has(remaining[startIdx]?.track_id)
        remaining = remaining.filter((t) => !badIds.has(t.track_id))
        if (remaining.length === 0) {
          console.error('[Player] No playable tracks remain')
          set({ isPlayerVisible: false, currentTrack: null, queue: [] })
          return
        }
        // Recalculate startIdx
        if (targetRemoved) {
          startIdx = Math.min(startIdx, remaining.length - 1)
        } else {
          startIdx = remaining.findIndex((t) => t === targetTrack)
          if (startIdx < 0) startIdx = 0
        }
        set({
          queue: remaining,
          currentIndex: startIdx,
          currentTrack: remaining[startIdx],
        })
      }
    }
    console.error('[Player] setQueue failed after max retries')
  },

  play: async () => {
    const instance = getInstance()
    if (!instance) return
    try {
      await instance.play()
    } catch (err) {
      console.error('[Player] Failed to play:', err)
    }
  },

  pause: () => {
    const instance = getInstance()
    if (!instance) return
    instance.pause()
  },

  togglePlayPause: () => {
    if (get().isPlaying) {
      get().pause()
    } else {
      get().play()
    }
  },

  next: async () => {
    const instance = getInstance()
    if (!instance) return
    const { currentIndex, queue } = get()
    if (currentIndex >= queue.length - 1) return

    console.log(`[Player] next() from index ${currentIndex}`)
    try {
      await instance.skipToNextItem()
    } catch (err) {
      console.error('[Player] skipToNextItem failed:', err)
    }
  },

  previous: async () => {
    const instance = getInstance()
    if (!instance) return
    const { currentIndex } = get()
    if (currentIndex <= 0) return

    console.log(`[Player] previous() from index ${currentIndex}`)
    try {
      await instance.skipToPreviousItem()
    } catch (err) {
      console.error('[Player] skipToPreviousItem failed:', err)
    }
  },

  seekTo: async (time) => {
    const instance = getInstance()
    if (!instance) return
    try {
      await instance.seekToTime(time)
    } catch (err) {
      console.error('[Player] Failed to seek:', err)
    }
  },

  toggleLove: async (trackId: string) => {
    const instance = getInstance()
    if (!instance || !instance.isAuthorized) return

    const loved = get().lovedTrackIds
    const isLoved = loved.has(trackId)

    try {
      const success = isLoved
        ? await unloveSong(instance, trackId)
        : await loveSong(instance, trackId)

      if (success) {
        const next = new Set(loved)
        if (isLoved) {
          next.delete(trackId)
        } else {
          next.add(trackId)
        }
        set({ lovedTrackIds: next })
      }
    } catch (err) {
      console.error('[Player] toggleLove failed:', err)
    }
  },

  isTrackLoved: (trackId: string) => {
    return get().lovedTrackIds.has(trackId)
  },

  close: () => {
    console.log('[Player] close()')
    clearStalledTimer()
    const instance = getInstance()
    if (instance) {
      try {
        instance.stop()
      } catch {
        // ignore
      }
    }
    set({
      isPlaying: false,
      currentTrack: null,
      queue: [],
      queueName: null,
      currentIndex: 0,
      currentTime: 0,
      duration: 0,
      isPlayerVisible: false,
    })
  },

  bindEvents: () => {
    const instance = getInstance()
    if (!instance) return

    get().unbindEvents()

    onPlaybackStateChange = (e) => {
      const stateName = STATE_NAMES[e.state] ?? String(e.state)
      console.log(`[Player] playbackStateDidChange: ${stateName} (${e.state})`)
      const playing = e.state === 2
      set({ isPlaying: playing })

      // Stalled-state recovery: if stuck in stalled/waiting for 4s, try stop → play
      if (e.state === 7 || e.state === 8) {
        clearStalledTimer()
        _stalledTimer = setTimeout(() => {
          const inst = getInstance()
          if (!inst) return
          // Still stalled? Try recovery
          if (!inst.player.isPlaying) {
            console.log('[Player] Stalled recovery: stop → play')
            inst.stop().then(() => inst.play()).catch(() => {})
          }
        }, 4000)
      } else {
        clearStalledTimer()
      }
    }

    // Sync our queue index with MusicKit's now-playing item
    onNowPlayingItemChange = () => {
      const inst = getInstance()
      if (!inst) return
      const { queue } = get()
      const mkItem = inst.nowPlayingItem
      if (mkItem && queue.length > 0) {
        const idx = queue.findIndex((t) => t.track_id === mkItem.id)
        if (idx >= 0) {
          console.log(`[Player] nowPlayingItemDidChange: index ${idx}, "${queue[idx].track_name}"`)
          set({ currentIndex: idx, currentTrack: queue[idx], currentTime: 0, duration: 0 })
        }
      }
    }

    onPlaybackTimeChange = (e) => {
      set({ currentTime: e.currentPlaybackTime })
    }

    onPlaybackDurationChange = (e) => {
      set({ duration: e.duration })
    }

    instance.addEventListener('playbackStateDidChange', onPlaybackStateChange)
    instance.addEventListener('nowPlayingItemDidChange', onNowPlayingItemChange)
    instance.addEventListener('playbackTimeDidChange', onPlaybackTimeChange)
    instance.addEventListener('playbackDurationDidChange', onPlaybackDurationChange)
  },

  unbindEvents: () => {
    const instance = getInstance()
    if (!instance) return
    clearStalledTimer()

    if (onPlaybackStateChange) {
      instance.removeEventListener('playbackStateDidChange', onPlaybackStateChange)
      onPlaybackStateChange = null
    }
    if (onNowPlayingItemChange) {
      instance.removeEventListener('nowPlayingItemDidChange', onNowPlayingItemChange)
      onNowPlayingItemChange = null
    }
    if (onPlaybackTimeChange) {
      instance.removeEventListener('playbackTimeDidChange', onPlaybackTimeChange)
      onPlaybackTimeChange = null
    }
    if (onPlaybackDurationChange) {
      instance.removeEventListener('playbackDurationDidChange', onPlaybackDurationChange)
      onPlaybackDurationChange = null
    }
  },
}))
