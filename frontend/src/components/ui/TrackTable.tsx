import type { Track } from '../../api/types'

interface TrackTableProps {
  tracks: Track[]
}

export default function TrackTable({ tracks }: TrackTableProps) {
  if (tracks.length === 0) {
    return <p className="text-gray-500">No tracks to display</p>
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-gray-700 text-gray-400">
          <tr>
            <th className="px-3 py-2">#</th>
            <th className="px-3 py-2">Track</th>
            <th className="px-3 py-2">Artist</th>
            <th className="px-3 py-2">Album</th>
            <th className="px-3 py-2">Genre</th>
          </tr>
        </thead>
        <tbody>
          {tracks.map((t, i) => (
            <tr key={t.track_id + i} className="border-b border-gray-800 hover:bg-gray-800/50">
              <td className="px-3 py-2 text-gray-500">{i + 1}</td>
              <td className="px-3 py-2 text-gray-200">{t.track_name}</td>
              <td className="px-3 py-2 text-gray-300">{t.artist}</td>
              <td className="px-3 py-2 text-gray-300">{t.album_name}</td>
              <td className="px-3 py-2 text-gray-400">{t.genre}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
