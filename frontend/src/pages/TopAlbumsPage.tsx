import { useMemo } from 'react'
import Sidebar from '../components/layout/Sidebar'
import MultiSelect from '../components/ui/MultiSelect'
import YearSelector from '../components/ui/YearSelector'
import AlbumGrid from '../components/ui/AlbumGrid'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import { useFilterStore } from '../store/filterStore'
import { useAuthStore } from '../store/authStore'
import { usePlayerStore } from '../store/playerStore'
import { useGenres } from '../api/hooks/useGenres'
import { usePublications } from '../api/hooks/usePublications'
import { useMoods } from '../api/hooks/useMoods'
import { useRelevantLists } from '../api/hooks/useRelevantLists'
import { useRelevantAlbums } from '../api/hooks/useRelevantAlbums'
import { useAlbumAccolades } from '../api/hooks/useAlbumAccolades'
import { useTracksFromAlbums } from '../api/hooks/useTracksFromAlbums'
import { sortList, getGenreForPlaylist, getPublicationForPlaylist } from '../utils/helpers'

export default function TopAlbumsPage() {
  const filters = useFilterStore()
  const isAuthorized = useAuthStore((s) => s.isAuthorized)
  const createPlaylist = useAuthStore((s) => s.createPlaylist)
  const playTracks = usePlayerStore((s) => s.playTracks)

  const { data: genresPayload } = useGenres()
  const { data: publicationsPayload } = usePublications()
  const { data: moods } = useMoods()

  const allGenres = useMemo(
    () => (genresPayload ? sortList(Object.keys(genresPayload)) : []),
    [genresPayload],
  )

  const availableSubgenres = useMemo(() => {
    if (!genresPayload || filters.genres.length === 0) return []
    const subs: string[] = []
    filters.genres.forEach((g) => {
      if (genresPayload[g]) subs.push(...genresPayload[g])
    })
    return sortList(subs)
  }, [genresPayload, filters.genres])

  const allPublications = useMemo(
    () => (publicationsPayload ? sortList(Object.keys(publicationsPayload)) : []),
    [publicationsPayload],
  )

  const minYear = filters.effectiveMinYear()
  const maxYear = filters.effectiveMaxYear()

  const { data: relevantLists } = useRelevantLists({
    minYear,
    maxYear,
    genre: filters.genres,
    subgenre: filters.subgenres,
    publication: filters.publications,
  })

  const { data: albums, isLoading: albumsLoading } = useRelevantAlbums({
    minYear,
    maxYear,
    genre: filters.genres,
    subgenre: filters.subgenres,
    publication: filters.publications,
    list: filters.lists,
    mood: filters.moods,
  })

  const albumKeys = useMemo(() => (albums ? albums.map((a) => a.album_key) : []), [albums])
  const { data: accolades } = useAlbumAccolades(albumKeys)

  // Pre-fetch tracks when authorized so play/export don't need a network call in the click handler
  const { data: preloadedTracks } = useTracksFromAlbums(
    albumKeys,
    filters.albumLimit,
    isAuthorized,
  )

  async function handlePlay() {
    if (!preloadedTracks || preloadedTracks.length === 0) return
    const yearText =
      filters.yearMode === 'single'
        ? String(filters.singleYear)
        : `${filters.minYear} - ${filters.maxYear}`
    const genreText = getGenreForPlaylist(filters.genres, filters.subgenres)
    let name = `Top Albums ${yearText}`
    if (genreText) name += ` ${genreText}`
    await playTracks(preloadedTracks, name)
  }

  async function handleExport() {
    if (!preloadedTracks || preloadedTracks.length === 0) return
    const trackIds = preloadedTracks.map((t) => t.track_id)

    const yearText =
      filters.yearMode === 'single'
        ? String(filters.singleYear)
        : `${filters.minYear} - ${filters.maxYear}`
    const genreText = getGenreForPlaylist(filters.genres, filters.subgenres)
    const pubText = getPublicationForPlaylist(filters.publications)
    let name = yearText
    if (genreText) name += ` ${genreText}`
    if (pubText) name += ` ${pubText}`

    const success = await createPlaylist(name, trackIds)
    if (success) {
      alert('Playlist created! Check your Apple Music library.')
    } else {
      alert('Failed to create playlist. Please try again.')
    }
  }

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <Sidebar label="Filters">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-300">
            Year Selection
          </label>
          <select
            value={filters.yearMode}
            onChange={(e) => filters.setYearMode(e.target.value as 'single' | 'range')}
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-base text-gray-200 sm:text-sm"
          >
            <option value="single">One Year</option>
            <option value="range">Multiple Years</option>
          </select>
        </div>

        <div>
          {filters.yearMode === 'single' ? (
            <YearSelector
              label="Year"
              value={filters.singleYear}
              onChange={filters.setSingleYear}
              reverse
            />
          ) : (
            <div className="grid grid-cols-2 gap-2">
              <YearSelector label="First Year" value={filters.minYear} onChange={filters.setMinYear} />
              <YearSelector
                label="Last Year"
                value={filters.maxYear}
                onChange={filters.setMaxYear}
                reverse
              />
            </div>
          )}
        </div>

        <div>
          <MultiSelect
            label="Genres"
            options={allGenres}
            selected={filters.genres}
            onChange={filters.setGenres}
          />
        </div>

        {filters.genres.length > 0 && (
          <div>
            <MultiSelect
              label="Subgenres"
              options={availableSubgenres}
              selected={filters.subgenres}
              onChange={filters.setSubgenres}
            />
          </div>
        )}

        <div>
          <MultiSelect
            label="Publications"
            options={allPublications}
            selected={filters.publications}
            onChange={filters.setPublications}
          />
        </div>

        <div>
          <MultiSelect
            label="Lists"
            options={relevantLists ?? []}
            selected={filters.lists}
            onChange={filters.setLists}
          />
        </div>

        <div>
          <MultiSelect
            label="Moods"
            options={moods ?? []}
            selected={filters.moods}
            onChange={filters.setMoods}
          />
        </div>

        {isAuthorized && (
          <div className="flex flex-col gap-2">
<button
              type="button"
              onClick={handlePlay}
              className="w-full rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500"
            >
              Play in Browser
            </button>
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
        {albumsLoading ? (
          <LoadingSpinner />
        ) : albums && albums.length > 0 ? (
          <AlbumGrid
            albums={albums}
            accolades={accolades}
            showPositions
            showSubgenres={filters.subgenres.length > 0}
            endIndex={50}
          />
        ) : (
          <p className="py-10 text-center text-gray-500">
            No albums found for the selected filters.
          </p>
        )}
      </div>
    </div>
  )
}
