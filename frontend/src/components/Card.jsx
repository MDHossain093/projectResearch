export default function Card({ title, children, className = "" }) {
  return (
    <div className={`bg-white border border-zinc-200 dark:bg-black dark:border-zinc-800 rounded-xl p-6 shadow-sm ${className}`}>
      {title && (
        <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-4 border-b border-zinc-100 dark:border-zinc-900 pb-2">
          {title}
        </h3>
      )}
      <div className="text-zinc-600 dark:text-zinc-400">{children}</div>
    </div>
  );
}
