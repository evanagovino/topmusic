import { create } from 'zustand'

interface FilterState {
  yearMode: 'single' | 'range'
  singleYear: number
  minYear: number
  maxYear: number
  genres: string[]
  subgenres: string[]
  publications: string[]
  lists: string[]
  moods: string[]
  albumLimit: number

  setYearMode: (mode: 'single' | 'range') => void
  setSingleYear: (y: number) => void
  setMinYear: (y: number) => void
  setMaxYear: (y: number) => void
  setGenres: (g: string[]) => void
  setSubgenres: (s: string[]) => void
  setPublications: (p: string[]) => void
  setLists: (l: string[]) => void
  setMoods: (m: string[]) => void
  setAlbumLimit: (n: number) => void

  effectiveMinYear: () => number
  effectiveMaxYear: () => number
}

const currentYear = new Date().getFullYear()

export const useFilterStore = create<FilterState>((set, get) => ({
  yearMode: 'single',
  singleYear: 2026,
  minYear: 2000,
  maxYear: currentYear,
  genres: [],
  subgenres: [],
  publications: [],
  lists: [],
  moods: [],
  albumLimit: 100,

  setYearMode: (mode) => set({ yearMode: mode }),
  setSingleYear: (y) => set({ singleYear: y }),
  setMinYear: (y) => set({ minYear: y }),
  setMaxYear: (y) => set({ maxYear: y }),
  setGenres: (g) => set({ genres: g, subgenres: [], lists: [] }),
  setSubgenres: (s) => set({ subgenres: s, lists: [] }),
  setPublications: (p) => set({ publications: p, lists: [] }),
  setLists: (l) => set({ lists: l }),
  setMoods: (m) => set({ moods: m }),
  setAlbumLimit: (n) => set({ albumLimit: n }),

  effectiveMinYear: () => {
    const s = get()
    return s.yearMode === 'single' ? s.singleYear : s.minYear
  },
  effectiveMaxYear: () => {
    const s = get()
    return s.yearMode === 'single' ? s.singleYear : s.maxYear
  },
}))
