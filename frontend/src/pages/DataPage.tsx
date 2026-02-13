import { useMemo, useState } from 'react'
import Sidebar from '../components/layout/Sidebar'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import { useArtists } from '../api/hooks/useArtists'
import { useSimilarArtists } from '../api/hooks/useSimilarArtists'
import { useSimilarAlbums } from '../api/hooks/useSimilarAlbums'
import { sortList } from '../utils/helpers'
import { useQuery } from '@tanstack/react-query'
import client from '../api/client'
import type { ArtistsAlbumsListResponse } from '../api/types'

function useArtistsAlbums() {
  return useQuery({
    queryKey: ['artistsAlbums'],
    queryFn: async () => {
      const { data } = await client.get<ArtistsAlbumsListResponse>('/web/artists_albums/')
      return data.albums
    },
  })
}

export default function DataPage() {
  const { data: artistsPayload } = useArtists()
  const { data: allAlbums } = useArtistsAlbums()

  const allArtists = useMemo(
    () => (artistsPayload ? sortList(Object.keys(artistsPayload)) : []),
    [artistsPayload],
  )

  const [selectedArtist, setSelectedArtist] = useState<string | null>(null)
  const [selectedAlbumId, setSelectedAlbumId] = useState<string | null>(null)

  const artistId = selectedArtist && artistsPayload ? artistsPayload[selectedArtist] : null

  const availableAlbums = useMemo(() => {
    if (!allAlbums || !artistId) return []
    return allAlbums.filter((a) => a.artist_id === artistId)
  }, [allAlbums, artistId])

  const { data: similarArtists, isLoading: artistsLoading } = useSimilarArtists(artistId)

  const { data: similarAlbums, isLoading: albumsLoading } = useSimilarAlbums(selectedAlbumId)

  // Map artist IDs back to names
  const artistIdToName = useMemo(() => {
    if (!artistsPayload) return {}
    const map: Record<string, string> = {}
    for (const [name, id] of Object.entries(artistsPayload)) {
      map[id] = name
    }
    return map
  }, [artistsPayload])

  return (
    <div className="flex h-full">
      <Sidebar>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-300">Artist</label>
          <select
            value={selectedArtist ?? ''}
            onChange={(e) => {
              setSelectedArtist(e.target.value || null)
              setSelectedAlbumId(null)
            }}
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-base text-gray-200 sm:text-sm"
          >
            <option value="">Select an artist</option>
            {allArtists.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>

        {availableAlbums.length > 0 && (
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-300">Album</label>
            <select
              value={selectedAlbumId ?? ''}
              onChange={(e) => setSelectedAlbumId(e.target.value || null)}
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-base text-gray-200 sm:text-sm"
            >
              <option value="">Select an album</option>
              {availableAlbums.map((a) => (
                <option key={a.album_id} value={a.album_id}>
                  {a.album_name}
                </option>
              ))}
            </select>
          </div>
        )}
      </Sidebar>

      <div className="flex-1 overflow-y-auto p-4 sm:p-6">
        {/* Similar Artists Table */}
        {artistsLoading && <LoadingSpinner />}
        {similarArtists && similarArtists.length > 0 && (
          <div className="mb-8">
            <h2 className="mb-4 text-xl font-bold text-white">Similar Artists</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-gray-700 text-gray-400">
                  <tr>
                    <th className="px-3 py-2">Artist</th>
                    <th className="px-3 py-2">Total Score</th>
                    <th className="px-3 py-2">Genre</th>
                    <th className="px-3 py-2">Publication</th>
                    <th className="px-3 py-2">Track Details</th>
                  </tr>
                </thead>
                <tbody>
                  {similarArtists.map((a, i) => (
                    <tr key={a.artist_id + i} className="border-b border-gray-800 hover:bg-gray-800/50">
                      <td className="px-3 py-2 text-gray-200">
                        {artistIdToName[a.artist_id] ?? a.artist_id}
                      </td>
                      <td className="px-3 py-2 text-gray-300">
                        {a.estimated_total_score?.toFixed(4)}
                      </td>
                      <td className="px-3 py-2 text-gray-300">
                        {a.genre_similarity?.toFixed(4)}
                      </td>
                      <td className="px-3 py-2 text-gray-300">
                        {a.publication_similarity?.toFixed(4)}
                      </td>
                      <td className="px-3 py-2 text-gray-300">
                        {a.track_details_similarity?.toFixed(4)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Similar Albums Table */}
        {albumsLoading && <LoadingSpinner />}
        {similarAlbums && similarAlbums.length > 0 && (
          <div>
            <h2 className="mb-4 text-xl font-bold text-white">Similar Albums</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-gray-700 text-gray-400">
                  <tr>
                    <th className="px-3 py-2">Album</th>
                    <th className="px-3 py-2">Artist</th>
                    <th className="px-3 py-2">Total Score</th>
                    <th className="px-3 py-2">Publication</th>
                    <th className="px-3 py-2">Track Details</th>
                  </tr>
                </thead>
                <tbody>
                  {similarAlbums.map((a, i) => (
                    <tr key={(a.album_id ?? '') + i} className="border-b border-gray-800 hover:bg-gray-800/50">
                      <td className="px-3 py-2 text-gray-200">{a.album ?? a.album_name}</td>
                      <td className="px-3 py-2 text-gray-300">{a.artist}</td>
                      <td className="px-3 py-2 text-gray-300">
                        {a.estimated_total_score?.toFixed(4)}
                      </td>
                      <td className="px-3 py-2 text-gray-300">
                        {a.publication_similarity?.toFixed(4)}
                      </td>
                      <td className="px-3 py-2 text-gray-300">
                        {a.track_details_similarity?.toFixed(4)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {!selectedArtist && (
          <p className="py-10 text-center text-gray-500">
            Select an artist to explore similarity data.
          </p>
        )}
      </div>
    </div>
  )
}
