"use client";

import { useState } from "react";
import { Plus, Trash2, Users } from "lucide-react";
import { fetchFromAPI } from "@/services/api";

export default function Team() {
  const [handle, setHandle]   = useState("");
  const [handles, setHandles] = useState([]);
  const [error, setError]     = useState("");
  const [loading, setLoading] = useState(false);
  const [teams, setTeams]     = useState([]);
  const [apiError, setApiError] = useState("");

  const addHandle = () => {
    const value = handle.trim();

    if (!value) {
      setError("Please enter a Codeforces handle.");
      return;
    }

    if (handles.includes(value)) {
      setError("Handle already added.");
      return;
    }

    setHandles([...handles, value]);
    setHandle("");
    setError("");
  };

  const removeHandle = (index) => {
    setHandles(handles.filter((_, i) => i !== index));
  };

  const isValid =
    handles.length >= 3 && handles.length % 3 === 0;

  const remaining =
    handles.length === 0
      ? 3
      : handles.length % 3 === 0
        ? 0
        : 3 - (handles.length % 3);

  const generateTeams = async () => {
    setLoading(true);
    setApiError("");
    setTeams([]);
    try {
      const data = await fetchFromAPI("/team", {
        method: "POST",
        body: JSON.stringify({ users: handles }),
      });
      setTeams(data.teams ?? []);
    } catch (err) {
      let msg = "Failed to generate teams.";
      try {
        const body = JSON.parse(err.message.split(": ").slice(2).join(": "));
        if (body?.message) msg = body.message;
      } catch {}
      setApiError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">

      {/* Header */}

      <div>
        <h1 className="text-3xl font-bold">
          Team Builder
        </h1>

        <p className="mt-2 text-slate-400">
          Add Codeforces handles and generate the best team combinations.
        </p>
      </div>

      {/* Add Handle */}

      <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">

        <h2 className="mb-5 text-xl font-semibold">
          Add Codeforces Handle
        </h2>

        <div className="flex gap-3">

          <input
            type="text"
            placeholder="Enter Codeforces handle"
            value={handle}
            onChange={(e) => setHandle(e.target.value)}
            className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-blue-500"
          />

          <button
            onClick={addHandle}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-3 hover:bg-blue-700"
          >
            <Plus size={18} />
            Add
          </button>

        </div>

        {error && (
          <p className="mt-3 text-sm text-red-400">
            {error}
          </p>
        )}
      </div>

      {/* Added Handles */}

      <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">

        <div className="mb-5 flex items-center gap-2">
          <Users size={20} />
          <h2 className="text-xl font-semibold">
            Added Handles
          </h2>
        </div>

        {handles.length === 0 ? (
          <p className="text-slate-400">
            No handles added yet.
          </p>
        ) : (
          <div className="space-y-3">

            {handles.map((item, index) => (

              <div
                key={index}
                className="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-950 px-4 py-3"
              >

                <span>{item}</span>

                <button
                  onClick={() => removeHandle(index)}
                  className="text-red-400 hover:text-red-500"
                >
                  <Trash2 size={18} />
                </button>

              </div>

            ))}

          </div>
        )}

        {/* Footer */}

        <div className="mt-6 border-t border-slate-700 pt-5">

          <p>
            <span className="font-semibold">
              Total Handles:
            </span>{" "}
            {handles.length}
          </p>

          {isValid ? (
            <p className="mt-2 text-green-400">
              ✅ Ready to generate teams.
            </p>
          ) : (
            <p className="mt-2 text-yellow-400">
              ⚠ Number of handles must be divisible by 3.
              {handles.length > 0 && (
                <>
                  {" "}
                  Add{" "}
                  <strong>{remaining}</strong>{" "}
                  more handle
                  {remaining > 1 ? "s" : ""}.
                </>
              )}
            </p>
          )}

          <button
            onClick={generateTeams}
            disabled={!isValid || loading}
            className={`mt-5 rounded-lg px-6 py-3 font-semibold transition ${isValid && !loading
                ? "bg-blue-600 hover:bg-blue-700"
                : "cursor-not-allowed bg-slate-700 text-slate-400"
              }`}
          >
            {loading ? "Building teams…" : "Generate Teams"}
          </button>

          {apiError && (
            <p className="mt-3 text-sm text-red-400">{apiError}</p>
          )}

        </div>

      </div>

      {/* Team Results */}

      <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">

        <h2 className="mb-5 text-xl font-semibold">Generated Teams</h2>

        {loading && (
          <div className="space-y-4 animate-pulse">
            {[1, 2].map((i) => (
              <div key={i} className="rounded-lg border border-slate-700 bg-slate-950 p-4">
                <div className="h-4 w-20 rounded bg-slate-700 mb-3" />
                <div className="flex gap-2">
                  {[...Array(3)].map((_, j) => (
                    <div key={j} className="h-6 w-24 rounded-full bg-slate-700" />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && teams.length === 0 && (
          <p className="text-slate-400">
            Generated team combinations will appear here after clicking
            <strong> Generate Teams</strong>.
          </p>
        )}

        {!loading && teams.length > 0 && (
          <div className="space-y-4">
            {teams.map((team) => (
              <div
                key={team.team_no}
                className="rounded-lg border border-slate-700 bg-slate-950 p-5"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-semibold text-blue-400">
                    Team {team.team_no}
                  </span>
                  <div className="flex gap-4 text-xs text-slate-400">
                    <span>Compatibility: <strong className="text-slate-200">{(team.compatibility * 100).toFixed(1)}%</strong></span>
                    <span>Coverage: <strong className="text-green-400">{(team.coverage * 100).toFixed(1)}%</strong></span>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {team.members.map((m) => (
                    <span
                      key={m}
                      className="rounded-full bg-blue-500/20 px-4 py-1.5 text-sm text-blue-300 font-medium"
                    >
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

      </div>

    </div>
  );
}