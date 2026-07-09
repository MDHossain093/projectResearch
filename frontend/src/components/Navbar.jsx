export default function Navbar() {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900 px-6 flex items-center justify-between">
      <div>
        <h1 className="text-xl font-bold text-white">
          CF Recommender
        </h1>
        <p className="text-sm text-slate-400">
          A Hybrid Recommendation and Team Formation System for Competitive Programming
        </p>
      </div>

      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center font-semibold">
          FH
        </div>
      </div>
    </header>
  );
}