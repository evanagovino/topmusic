import { create } from 'zustand'
import type { Track } from '../api/types'

export type RadioMode = 'genre' | 'artist' | 'prompt'

interface RadioState {
  mode: RadioMode
  // Genre mode
  genre: string | null
  subgenre: string | null
  minYear: number
  maxYear: number
  // Artist mode
  artistName: string | null
  artistId: string | null
  // Custom prompt mode
  customPrompt: string
  submittedPrompt: string | null
  playlistName: string | null
  explanation: string | null
  // Shared
  albumLimit: number
  generatedTracks: Track[] | null
  isGenerating: boolean

  setMode: (m: RadioMode) => void
  setGenre: (g: string | null) => void
  setSubgenre: (s: string | null) => void
  setMinYear: (y: number) => void
  setMaxYear: (y: number) => void
  setArtistName: (name: string | null) => void
  setArtistId: (id: string | null) => void
  setCustomPrompt: (p: string) => void
  submitPrompt: () => void
  setAlbumLimit: (n: number) => void
  setGeneratedTracks: (t: Track[] | null) => void
  setIsGenerating: (v: boolean) => void
  setPlaylistName: (n: string | null) => void
  setExplanation: (e: string | null) => void
  reset: () => void
}

const currentYear = new Date().getFullYear()

export const useRadioStore = create<RadioState>((set, get) => ({
  mode: 'genre',
  genre: null,
  subgenre: null,
  minYear: 2000,
  maxYear: currentYear,
  artistName: null,
  artistId: null,
  customPrompt: '',
  submittedPrompt: null,
  playlistName: null,
  explanation: null,
  albumLimit: 100,
  generatedTracks: null,
  isGenerating: false,

  setMode: (m) => set({ mode: m, generatedTracks: null }),
  setGenre: (g) => set({ genre: g, subgenre: null, isGenerating: false }),
  setSubgenre: (s) => set({ subgenre: s, isGenerating: false }),
  setMinYear: (y) => set({ minYear: y, isGenerating: false }),
  setMaxYear: (y) => set({ maxYear: y, isGenerating: false }),
  setArtistName: (name) => set({ artistName: name }),
  setArtistId: (id) => set({ artistId: id }),
  setCustomPrompt: (p) => set({ customPrompt: p }),
  submitPrompt: () => set((s) => ({ submittedPrompt: s.customPrompt })),
  setAlbumLimit: (n) => set({ albumLimit: n, isGenerating: false }),
  setGeneratedTracks: (t) => set({ generatedTracks: t }),
  setIsGenerating: (v) => set({ isGenerating: v }),
  setPlaylistName: (n) => set({ playlistName: n }),
  setExplanation: (e) => set({ explanation: e }),
  reset: () =>
    set({
      genre: null,
      subgenre: null,
      artistName: null,
      artistId: null,
      customPrompt: '',
      submittedPrompt: null,
      playlistName: null,
      explanation: null,
      generatedTracks: null,
      isGenerating: false,
    }),
}))
