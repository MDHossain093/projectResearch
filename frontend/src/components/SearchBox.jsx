export default function SearchBox({ value, onChange, placeholder = "Search...", className = "" }) {
  return (
    <div className={`relative w-full max-w-md ${className}`}>
      <input
        type="text"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="w-full px-4 py-2 border border-zinc-200 dark:border-zinc-800 rounded-lg bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-50 focus:outline-none focus:ring-2 focus:ring-zinc-500 transition-all text-sm"
      />
    </div>
  );
}
