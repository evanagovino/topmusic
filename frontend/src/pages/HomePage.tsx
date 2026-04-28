import AlbumCardCompact from '../components/ui/AlbumCardCompact'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import { useRelevantAlbums } from '../api/hooks/useRelevantAlbums'
import { useUserTrackData } from '../api/hooks/useUserTrackData'
import { useSimilarAlbumsForGenre } from '../api/hooks/useSimilarAlbumsForGenre'
import { useAuthStore } from '../store/authStore'

const CURRENT_YEAR = 2026

interface AlbumRowProps {
  title: string
  isLoading: boolean
  albums?: { album_key: string; artist: string; album: string; year: number; image_url: string; apple_music_album_url?: string }[]
}

function AlbumRow({ title, isLoading, albums }: AlbumRowProps) {
  return (
    <section className="flex flex-col gap-3">
      <h2 className="px-4 text-lg font-bold text-white sm:px-6">{title}</h2>
      {isLoading ? (
        <div className="px-4 sm:px-6">
          <LoadingSpinner />
        </div>
      ) : albums && albums.length > 0 ? (
        <div className="flex gap-4 overflow-x-auto px-4 pb-2 sm:px-6 [&::-webkit-scrollbar]:hidden">
          {albums.slice(0, 25).map((a) => (
            <AlbumCardCompact
              key={a.album_key}
              artist={a.artist}
              album={a.album}
              year={a.year}
              imageUrl={a.image_url}
              appleMusicUrl={a.apple_music_album_url}
            />
          ))}
        </div>
      ) : (
        <p className="px-4 text-sm text-gray-500 sm:px-6">No albums found.</p>
      )}
    </section>
  )
}

function GenreAlbumRow({ topic, type, albumKeys }: { topic: string; type: string; albumKeys: string[] }) {
  const { data, isLoading } = useSimilarAlbumsForGenre(albumKeys)
  const title = type === 'artist' ? `More Albums Like ${topic}` : `Recommended ${topic} Albums`
  return (
    <AlbumRow
      title={title}
      isLoading={isLoading}
      albums={data}
    />
  )
}

function DefaultRows() {
  const { data: topThisYear, isLoading: loadingThisYear } = useRelevantAlbums({
    minYear: CURRENT_YEAR,
    maxYear: CURRENT_YEAR,
  })

  const { data: recentlyAdded, isLoading: loadingRecent } = useRelevantAlbums({
    minYear: CURRENT_YEAR,
    maxYear: CURRENT_YEAR,
    orderByRecency: true,
  })

  const { data: topSince1959, isLoading: loadingSince1959 } = useRelevantAlbums({
    minYear: 1959,
    maxYear: CURRENT_YEAR,
  })

  return (
    <>
      <AlbumRow title={`Top Albums of ${CURRENT_YEAR}`} isLoading={loadingThisYear} albums={topThisYear} />
      <AlbumRow title="Recently Added Albums" isLoading={loadingRecent} albums={recentlyAdded} />
      <AlbumRow title="Top Albums Since 1959" isLoading={loadingSince1959} albums={topSince1959} />
    </>
  )
}

export default function HomePage() {
  const isAuthorized = useAuthStore((s) => s.isAuthorized)
  const musicInstance = useAuthStore((s) => s.musicInstance)
  const musicUserToken = musicInstance?.musicUserToken ?? null

  const { data: userTrackData, isError, isLoading: loadingUserData } = useUserTrackData(
    musicUserToken,
    isAuthorized,
  )

  const showPersonalized = isAuthorized && !isError && (loadingUserData || (userTrackData && userTrackData.length > 0))

  return (
    <div className="flex flex-col gap-8 overflow-y-auto py-6">
      {showPersonalized ? (
        loadingUserData ? (
          <div className="px-4 sm:px-6"><LoadingSpinner /></div>
        ) : (
          userTrackData!.map((item) => (
            <GenreAlbumRow key={item.topic} topic={item.topic} type={item.type} albumKeys={item.album_keys} />
          ))
        )
      ) : (
        <DefaultRows />
      )}
    </div>
  )
}
