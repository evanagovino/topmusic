import { useMemo, useCallback, useState, useRef, useEffect } from 'react'
import Sidebar from '../components/layout/Sidebar'
import YearSelector from '../components/ui/YearSelector'
import TrackCard from '../components/ui/TrackCard'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import { useRadioStore, type RadioMode } from '../store/radioStore'
import { useAuthStore } from '../store/authStore'
import { usePlayerStore } from '../store/playerStore'
import { useGenres } from '../api/hooks/useGenres'
import { useArtists } from '../api/hooks/useArtists'
import { useRelevantAlbums } from '../api/hooks/useRelevantAlbums'
import { useTracksFromAlbums } from '../api/hooks/useTracksFromAlbums'
import { useRecommendedTracks } from '../api/hooks/useRecommendedTracks'
import { useCustomPrompt } from '../api/hooks/useCustomPrompt'
import { sortList } from '../utils/helpers'
import type { Track } from '../api/types'

function ArtistSearch({
  artists,
  value,
  onChange,
}: {
  artists: string[]
  value: string | null
  onChange: (name: string | null) => void
}) {
  const [query, setQuery] = useState(value ?? '')
  const [open, setOpen] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)

  // Sync query text when value changes externally (e.g. mode switch)
  useEffect(() => {
    setQuery(value ?? '')
  }, [value])

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const filtered = useMemo(() => {
    if (!query.trim()) return artists.slice(0, 50)
    const lower = query.toLowerCase()
    return artists.filter((a) =>
      a.toLowerCase().split(/\s+/).some((word) => word.startsWith(lower))
    ).slice(0, 50)
  }, [artists, query])

  return (
    <div ref={wrapperRef} className="relative">
      <label className="mb-1 block text-sm font-medium text-gray-300">Artist</label>
      <input
        type="text"
        value={query}
        placeholder="Type to search artists..."
        onChange={(e) => {
          setQuery(e.target.value)
          setOpen(true)
          if (!e.target.value) onChange(null)
        }}
        onFocus={() => setOpen(true)}
        className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-base text-gray-200 sm:text-sm outline-none focus:border-indigo-500"
      />
      {open && filtered.length > 0 && (
        <ul className="absolute z-50 mt-1 max-h-60 w-full overflow-y-auto rounded-lg border border-gray-700 bg-gray-800 py-1 shadow-lg">
          {filtered.map((a) => (
            <li key={a}>
              <button
                type="button"
                onClick={() => {
                  setQuery(a)
                  onChange(a)
                  setOpen(false)
                }}
                className={`w-full px-3 py-2 text-left text-base hover:bg-gray-700 sm:py-1.5 sm:text-sm ${
                  a === value ? 'text-indigo-400' : 'text-gray-200'
                }`}
              >
                {a}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function RadioPage() {
  const radio = useRadioStore()
  const isAuthorized = useAuthStore((s) => s.isAuthorized)
  const createPlaylist = useAuthStore((s) => s.createPlaylist)
  const playTracks = usePlayerStore((s) => s.playTracks)

  const { data: genresPayload } = useGenres()
  const { data: artistsPayload } = useArtists()

  const allGenres = useMemo(
    () => (genresPayload ? sortList(Object.keys(genresPayload)) : []),
    [genresPayload],
  )

  const availableSubgenres = useMemo(() => {
    if (!genresPayload || !radio.genre || !genresPayload[radio.genre]) return []
    return ['All', ...genresPayload[radio.genre].sort()]
  }, [genresPayload, radio.genre])

  const allArtists = useMemo(
    () => (artistsPayload ? sortList(Object.keys(artistsPayload)) : []),
    [artistsPayload],
  )

  // Genre mode: get relevant albums, then tracks
  const genreForQuery = radio.mode === 'genre' && radio.genre ? [radio.genre] : undefined
  const subgenreForQuery =
    radio.mode === 'genre' && radio.subgenre && radio.subgenre !== 'All'
      ? [radio.subgenre]
      : undefined

  const { data: genreAlbums } = useRelevantAlbums({
    minYear: radio.minYear,
    maxYear: radio.maxYear,
    genre: genreForQuery,
    subgenre: subgenreForQuery,
    enabled: radio.mode === 'genre' && radio.isGenerating && !!radio.genre,
  })

  const genreAlbumKeys = useMemo(
    () => (genreAlbums ? genreAlbums.map((a) => a.album_key) : []),
    [genreAlbums],
  )

  const { data: genreTracks, isLoading: genreTracksLoading } = useTracksFromAlbums(
    genreAlbumKeys,
    radio.albumLimit,
    radio.mode === 'genre' && radio.isGenerating && genreAlbumKeys.length > 0,
  )

  // Artist mode
  const { data: artistTracks, isLoading: artistTracksLoading } = useRecommendedTracks(
    radio.mode === 'artist' && radio.isGenerating ? radio.artistId : null,
  )

  // Custom prompt mode
  const { data: promptResult, isLoading: promptLoading } = useCustomPrompt(
    radio.mode === 'prompt' && radio.isGenerating ? radio.submittedPrompt : null,
  )

  const currentTracks: Track[] | undefined = useMemo(() => {
    if (radio.mode === 'genre') return genreTracks
    if (radio.mode === 'artist') return artistTracks
    if (radio.mode === 'prompt') return promptResult?.tracks
    return undefined
  }, [radio.mode, genreTracks, artistTracks, promptResult])

  const isLoading =
    (radio.mode === 'genre' && genreTracksLoading) ||
    (radio.mode === 'artist' && artistTracksLoading) ||
    (radio.mode === 'prompt' && promptLoading)

  const handleGenerate = useCallback(() => {
    if (radio.mode === 'prompt') {
      radio.submitPrompt()
    }
    radio.setIsGenerating(true)
  }, [radio])

  const canGenerate = useMemo(() => {
    if (radio.mode === 'genre') return !!radio.genre
    if (radio.mode === 'artist') return !!radio.artistId
    if (radio.mode === 'prompt') return radio.customPrompt.trim().length > 0
    return false
  }, [radio.mode, radio.genre, radio.artistId, radio.customPrompt])

  const displayLabel = useMemo(() => {
    if (radio.mode === 'genre') return radio.subgenre ?? radio.genre ?? 'Genre'
    if (radio.mode === 'artist') return radio.artistName ?? 'Artist'
    if (radio.mode === 'prompt') return 'Custom'
    return ''
  }, [radio])

  async function handleExport() {
    if (!currentTracks) return
    const trackIds = currentTracks.map((t) => t.track_id)
    const success = await createPlaylist(displayLabel, trackIds)
    if (success) {
      alert('Playlist created! Check your Apple Music library.')
    } else {
      alert('Failed to create playlist. Please try again.')
    }
  }

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <Sidebar label="Radio Settings">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-300">Radio Type</label>
          <select
            value={radio.mode}
            onChange={(e) => {
              radio.setMode(e.target.value as RadioMode)
              radio.setIsGenerating(false)
            }}
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-base text-gray-200 sm:text-sm"
          >
            <option value="genre">Genre</option>
            <option value="artist">Artist</option>
            <option value="prompt">Custom Prompt</option>
          </select>
        </div>

        {radio.mode === 'genre' && (
          <>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-300">Genre</label>
              <select
                value={radio.genre ?? ''}
                onChange={(e) => radio.setGenre(e.target.value || null)}
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-base text-gray-200 sm:text-sm"
              >
                <option value="">Select a genre</option>
                {allGenres.map((g) => (
                  <option key={g} value={g}>
                    {g}
                  </option>
                ))}
              </select>
            </div>
            {radio.genre && availableSubgenres.length > 0 && (
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-300">Subgenre</label>
                <select
                  value={radio.subgenre ?? 'All'}
                  onChange={(e) =>
                    radio.setSubgenre(e.target.value === 'All' ? null : e.target.value)
                  }
                  className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-base text-gray-200 sm:text-sm"
                >
                  {availableSubgenres.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div className="grid grid-cols-2 gap-2">
              <YearSelector label="First Year" value={radio.minYear} onChange={radio.setMinYear} />
              <YearSelector
                label="Last Year"
                value={radio.maxYear}
                onChange={radio.setMaxYear}
                reverse
              />
            </div>
          </>
        )}

        {radio.mode === 'artist' && (
          <ArtistSearch
            artists={allArtists}
            value={radio.artistName}
            onChange={(name) => {
              radio.setArtistName(name)
              radio.setArtistId(name && artistsPayload ? artistsPayload[name] : null)
              radio.setIsGenerating(false)
            }}
          />
        )}

        {radio.mode === 'prompt' && (
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-300">Custom Prompt</label>
            <textarea
              value={radio.customPrompt}
              onChange={(e) => radio.setCustomPrompt(e.target.value)}
              placeholder="Describe the playlist you want..."
              rows={2}
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-base text-gray-200 sm:text-sm outline-none focus:border-indigo-500"
            />
          </div>
        )}

{canGenerate && (
          <div className="flex items-end">
            <button
              type="button"
              onClick={handleGenerate}
              disabled={isLoading}
              className="w-full rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              {isLoading ? 'Generating...' : `Generate ${displayLabel} Radio`}
            </button>
          </div>
        )}

        {isAuthorized && currentTracks && currentTracks.length > 0 && (
          <div className="flex items-end">
            <button
              type="button"
              onClick={handleExport}
              className="w-full rounded-lg bg-pink-600 px-3 py-2 text-sm font-medium text-white hover:bg-pink-500"
            >
              Export to Apple Music
            </button>
          </div>
        )}
      </Sidebar>

      <div className="flex-1 p-4 sm:p-6">
        {!radio.isGenerating && (
          <p className="py-10 text-center text-gray-500">
            Pick a Genre, Artist, or Custom Prompt to start your radio.
          </p>
        )}

        {isLoading && <LoadingSpinner />}

        {radio.mode === 'prompt' && promptResult?.explanation && (
          <div className="mb-6 rounded-lg border border-gray-700 bg-gray-900 p-4">
            {promptResult.playlist_name && (
              <h3 className="mb-2 text-lg font-semibold text-white">
                {promptResult.playlist_name}
              </h3>
            )}
            <p className="text-sm text-gray-300">{promptResult.explanation}</p>
          </div>
        )}

        {currentTracks && currentTracks.length > 0 && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-4">
              <h2 className="text-xl font-bold text-white">
                Recommended Tracks ({currentTracks.length})
              </h2>
              {isAuthorized && (
                <button
                  type="button"
                  onClick={() => playTracks(currentTracks, `${displayLabel} Radio`)}
                  className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
                >
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                  Play All
                </button>
              )}
            </div>
            {currentTracks.map((t, i) => (
              <TrackCard
                key={t.track_id + i}
                track={t}
                allTracks={currentTracks}
                trackIndex={i}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
