"use client";

import { useState } from "react";
import { fetchFromAPI } from "@/services/api";

export default function Weakness() {
  const [handle, setHandle]   = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");
  const [result, setResult]   = useState(null); // {weak_tags, strong_tags, coverage}

  const handleSubmit = async (e) => {
    e?.preventDefault();
    const h = handle.trim();
    if (!h) { setError("Please enter a Codeforces handle."); return; }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await fetchFromAPI(`/weakness/${encodeURIComponent(h)}`);
      setResult(data);
    } catch (err) {
      let msg = "Failed to fetch weakness data.";
      try {
        const body = JSON.parse(err.message.split(": ").slice(2).join(": "));
        if (body?.message) msg = body.message;
      } catch {}
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const weakTags   = result?.weak_tags   ?? [];
  const strongTags = result?.strong_tags ?? [];
  const coverage   = result?.coverage    ?? null;

  return (
    <div className="space-y-8">

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Weakness Analysis</h1>
        <p className="mt-2 text-slate-400">
          Analyze a user&apos;s weak topics and tag coverage.
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
            id="weak-handle-input"
            type="text"
            value={handle}
            onChange={(e) => setHandle(e.target.value)}
            placeholder="e.g. tourist"
            className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-blue-500 transition"
          />
          <button
            id="weak-submit-btn"
            type="submit"
            disabled={loading}
            className="rounded-lg bg-blue-600 px-6 py-3 font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {loading ? "Analysing…" : "Analyse"}
          </button>
        </div>

        {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
      </form>

      {/* Coverage stat — shown after result */}
      {(loading || result) && (
        <div className="grid gap-6 md:grid-cols-3">

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
            <p className="text-slate-400">Overall Coverage</p>
            {loading ? (
              <div className="mt-3 h-9 w-20 rounded bg-slate-700 animate-pulse" />
            ) : (
              <h2 className="mt-3 text-3xl font-bold text-green-400">
                {coverage != null ? `${(coverage * 100).toFixed(1)}%` : "—"}
              </h2>
            )}
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
            <p className="text-slate-400">Weak Topics</p>
            {loading ? (
              <div className="mt-3 h-9 w-16 rounded bg-slate-700 animate-pulse" />
            ) : (
              <h2 className="mt-3 text-3xl font-bold text-red-400">
                {weakTags.length}
              </h2>
            )}
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
            <p className="text-slate-400">Strong Topics</p>
            {loading ? (
              <div className="mt-3 h-9 w-16 rounded bg-slate-700 animate-pulse" />
            ) : (
              <h2 className="mt-3 text-3xl font-bold text-blue-400">
                {strongTags.length}
              </h2>
            )}
          </div>

        </div>
      )}

      {/* Weak Tags */}
      {(loading || weakTags.length > 0) && (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="mb-5 text-xl font-semibold">
            ⚠ Weak Topics
            <span className="ml-2 text-sm font-normal text-slate-400">
              — focus here to improve
            </span>
          </h2>

          {loading ? (
            <div className="flex flex-wrap gap-3 animate-pulse">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-8 w-24 rounded-full bg-slate-700" />
              ))}
            </div>
          ) : (
            <div className="flex flex-wrap gap-3">
              {weakTags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-red-500/20 px-4 py-2 text-red-400 text-sm font-medium"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Strong Tags */}
      {(loading || strongTags.length > 0) && (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="mb-5 text-xl font-semibold">
            ✅ Strong Topics
          </h2>

          {loading ? (
            <div className="flex flex-wrap gap-3 animate-pulse">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="h-8 w-20 rounded-full bg-slate-700" />
              ))}
            </div>
          ) : (
            <div className="flex flex-wrap gap-3">
              {strongTags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-green-500/20 px-4 py-2 text-green-400 text-sm font-medium"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!loading && !result && (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-8 text-center text-slate-500">
          Enter a handle above and click <strong className="text-slate-300">Analyse</strong> to see results.
        </div>
      )}

    </div>
  );
}
