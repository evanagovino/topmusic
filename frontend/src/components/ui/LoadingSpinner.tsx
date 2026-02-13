export default function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-gray-600 border-t-indigo-500" />
    </div>
  )
}
