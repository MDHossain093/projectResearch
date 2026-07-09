"use client";

import { useState } from "react";
import { fetchFromAPI } from "@/services/api";

// ─── Rating badge colour ───────────────────────────────────────────────────
function ratingColor(r) {
  if (!r) return "text-slate-400";
  if (r >= 2400) return "text-red-400";
  if (r >= 2100) return "text-orange-400";
  if (r >= 1900) return "text-violet-400";
  if (r >= 1600) return "text-blue-400";
  if (r >= 1400) return "text-cyan-400";
  if (r >= 1200) return "text-green-400";
  return "text-slate-300";
}

// ─── Skeleton loader row ───────────────────────────────────────────────────
function SkeletonRow() {
  return (
    <tr className="border-b border-slate-800 animate-pulse">
      {[...Array(6)].map((_, i) => (
        <td key={i} className="py-4 pr-4">
          <div className="h-4 rounded bg-slate-700 w-full" />
        </td>
      ))}
    </tr>
  );
}

export default function Recommendation() {
  const [handle, setHandle] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null); // {user, recommendations}

  const handleSubmit = async (e) => {
    e?.preventDefault();
    const h = handle.trim();
    if (!h) { setError("Please enter a Codeforces handle."); return; }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await fetchFromAPI(`/recommend/${encodeURIComponent(h)}`);
      setResult(data);
    } catch (err) {
      // Try to parse the error body for a proper message
      let msg = "Failed to fetch recommendations.";
      try {
        const body = JSON.parse(err.message.split(": ").slice(2).join(": "));
        if (body?.message) msg = body.message;
      } catch {}
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const user = result?.user;
  const recs  = result?.recommendations ?? [];

  return (
    <div className="space-y-8">

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Problem Recommendation</h1>
        <p className="mt-2 text-slate-400">
          Enter a Codeforces handle to receive personalized recommendations.
        </p>
      </div>

      {/* Search Box */}
      <form
        onSubmit={handleSubmit}
        className="rounded-xl border border-slate-800 bg-slate-900 p-6"
      >
        <label className="block text-sm mb-2">Codeforces Handle</label>

        <div className="flex gap-4">
          <input
            id="rec-handle-input"
            type="text"
            value={handle}
            onChange={(e) => setHandle(e.target.value)}
            placeholder="e.g. tourist"
            className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-blue-500 transition"
          />

          <button
            id="rec-submit-btn"
            type="submit"
            disabled={loading}
            className="rounded-lg bg-blue-600 px-6 py-3 font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {loading ? "Loading…" : "Recommend"}
          </button>
        </div>

        {error && (
          <p className="mt-3 text-sm text-red-400">{error}</p>
        )}
      </form>

      {/* User Profile — shown only after a result */}
      {(loading || user) && (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-xl font-semibold mb-5">User Profile</h2>

          {loading ? (
            <div className="grid gap-4 md:grid-cols-3 animate-pulse">
              {[...Array(5)].map((_, i) => (
                <div key={i}>
                  <div className="h-3 w-24 rounded bg-slate-700 mb-2" />
                  <div className="h-5 w-16 rounded bg-slate-600" />
                </div>
              ))}
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <div>
                <p className="text-slate-400">Handle</p>
                <h3 className="font-semibold">{user.handle}</h3>
              </div>
              <div>
                <p className="text-slate-400">Current Rating</p>
                <h3 className={`font-semibold ${ratingColor(user.rating)}`}>
                  {user.rating || "Unrated"}
                </h3>
              </div>
              <div>
                <p className="text-slate-400">Max Rating</p>
                <h3 className={`font-semibold ${ratingColor(user.max_rating)}`}>
                  {user.max_rating || "—"}
                </h3>
              </div>
              <div>
                <p className="text-slate-400">Solved Problems</p>
                <h3 className="font-semibold">{user.solved ?? "—"}</h3>
              </div>
              <div>
                <p className="text-slate-400">Solve Rate</p>
                <h3 className="font-semibold">
                  {user.solve_rate != null
                    ? `${(user.solve_rate * 100).toFixed(1)}%`
                    : "—"}
                </h3>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recommendations Table */}
      {(loading || recs.length > 0) && (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-xl font-semibold mb-5">Recommended Problems</h2>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-slate-800">
                <tr className="text-left text-slate-400">
                  <th className="py-3 pr-4 w-8">#</th>
                  <th className="pr-4">Problem</th>
                  <th className="pr-4">Rating</th>
                  <th className="pr-4">Tags</th>
                  <th className="pr-4">Score</th>
                  <th></th>
                </tr>
              </thead>

              <tbody>
                {loading
                  ? [...Array(10)].map((_, i) => <SkeletonRow key={i} />)
                  : recs.map((rec, i) => (
                      <tr
                        key={`${rec.contestId}-${rec.index}`}
                        className="border-b border-slate-800 hover:bg-slate-800/40 transition"
                      >
                        <td className="py-4 pr-4 text-slate-500">{i + 1}</td>
                        <td className="pr-4 font-mono font-semibold">
                          {rec.contestId}{rec.index}
                        </td>
                        <td className={`pr-4 font-semibold ${ratingColor(rec.rating)}`}>
                          {rec.rating}
                        </td>
                        <td className="pr-4">
                          <div className="flex flex-wrap gap-1">
                            {rec.tags.slice(0, 3).map((tag) => (
                              <span
                                key={tag}
                                className="rounded-full bg-slate-700 px-2 py-0.5 text-xs text-slate-300"
                              >
                                {tag}
                              </span>
                            ))}
                            {rec.tags.length > 3 && (
                              <span className="text-slate-500 text-xs self-center">
                                +{rec.tags.length - 3}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="pr-4 text-green-400 font-mono text-xs">
                          {rec.score?.toFixed(4)}
                        </td>
                        <td>
                          <a
                            href={rec.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="rounded bg-blue-600 px-3 py-1 text-xs font-semibold hover:bg-blue-700 transition"
                          >
                            Solve →
                          </a>
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty state — after fetch with no results */}
      {!loading && result && recs.length === 0 && (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-8 text-center text-slate-400">
          No recommendations found for <strong>{user?.handle}</strong>.
        </div>
      )}

    </div>
  );
}
