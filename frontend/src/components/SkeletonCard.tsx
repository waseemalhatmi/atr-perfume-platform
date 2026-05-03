/**
 * SkeletonCard — Loading placeholder that mirrors the dimensions of ItemCard.
 * Uses `.glass` (defined in index.css) for the card shell, and `.skeleton`
 * (Tailwind animate-pulse utility defined in tailwind.config.js) for the
 * shimmer effect on each placeholder block.
 */
export default function SkeletonCard() {
  return (
    <div className="glass rounded-2xl overflow-hidden">
      {/* Image placeholder — same aspect ratio as ItemCard (3/4) */}
      <div className="skeleton aspect-[3/4] w-full" />

      <div className="p-5 space-y-3">
        {/* Brand + rating row */}
        <div className="flex justify-between">
          <div className="skeleton h-3 w-20 rounded-full" />
          <div className="skeleton h-3 w-10 rounded-full" />
        </div>
        {/* Name */}
        <div className="skeleton h-4 w-3/4 rounded" />
        {/* Price + category row */}
        <div className="flex justify-between mt-4">
          <div className="skeleton h-5 w-24 rounded" />
          <div className="skeleton h-5 w-16 rounded" />
        </div>
      </div>
    </div>
  )
}
