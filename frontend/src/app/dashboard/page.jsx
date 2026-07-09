"use client";

// ─── Static data (no backend fetch) ──────────────────────────────────────────
const STATIC = {
  users: 1000,
  problems: 10864,
  submissions: 918763,
  model: "Hybrid SVD",
  evaluated_users: 1000,
  performance: {
    k: 5,
    precision:    0.8143,
    recall:       0.3672,
    f1_score:     0.4963,
    accuracy:     0.3560,
    tag_coverage: 0.3672,
    weak_hit_at_k: 0.8990,
  },
  confusion: {
    avg_tp: 10.18,
    avg_fp: 0.95,
    avg_fn: 14.19,
  },
};

// ─── Stat card ────────────────────────────────────────────────────────────────
function StatCard({ label, value, color, sub }) {
  return (
    <div className="rounded-xl bg-slate-900 border border-slate-800 p-6 flex flex-col gap-1">
      <p className="text-sm text-slate-400">{label}</p>
      <h2 className={`text-3xl font-bold ${color}`}>{value}</h2>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  );
}

// ─── Metric row with progress bar ─────────────────────────────────────────────
function MetricRow({ label, value, pct, barColor, valueLabel }) {
  const display = valueLabel ?? `${(pct ?? value * 100).toFixed(2)}%`;
  return (
    <div className="flex items-center gap-4 py-3 border-b border-slate-800 last:border-0">
      <span className="text-slate-300 w-44 shrink-0 text-sm">{label}</span>
      <div className="flex-1 bg-slate-800 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${Math.min(pct ?? value * 100, 100).toFixed(1)}%` }}
        />
      </div>
      <span className="font-semibold tabular-nums text-sm w-16 text-right text-slate-100">
        {display}
      </span>
    </div>
  );
}

// ─── Simple KV row ────────────────────────────────────────────────────────────
function KVRow({ label, value, valueClass = "text-slate-100" }) {
  return (
    <div className="flex justify-between items-center py-3 border-b border-slate-800 last:border-0 text-sm">
      <span className="text-slate-400">{label}</span>
      <span className={`font-semibold ${valueClass}`}>{value}</span>
    </div>
  );
}

// ─── Confusion cell ───────────────────────────────────────────────────────────
function ConfusionCell({ label, value, color }) {
  return (
    <div className={`rounded-lg border ${color} p-4 text-center`}>
      <p className="text-xs text-slate-400 mb-1">{label}</p>
      <p className="text-2xl font-bold text-slate-100">{value}</p>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const data = STATIC;
  const perf = data.performance;
  const conf = data.confusion;
  const K    = perf.k;

  return (
    <div className="space-y-8">

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="mt-2 text-slate-400">
          A Hybrid Recommendation and Team Formation System for Competitive Programming
        </p>
      </div>

      {/* ── Top stat cards ── */}
      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Users"       value={data.users.toLocaleString()}       color="text-blue-400"   sub="training set" />
        <StatCard label="Problems"    value={data.problems.toLocaleString()}    color="text-green-400"  sub="unique problems" />
        <StatCard label="Submissions" value={data.submissions.toLocaleString()} color="text-orange-400" sub="total interactions" />
        <StatCard label="Model"       value={data.model}                         color="text-purple-400" sub={`evaluated on ${data.evaluated_users.toLocaleString()} users`} />
      </div>

      {/* ── Weakness Metrics + Dataset Info ── */}
      <div className="grid gap-6 lg:grid-cols-2">

        {/* Weakness Learning Metrics */}
        <div className="rounded-xl bg-slate-900 border border-slate-800 p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-xl font-semibold">Weakness Learning Metrics</h2>
            <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded-full">K = {K}</span>
          </div>
          <div>
            <MetricRow label="Precision"       value={perf.precision}      barColor="bg-green-500"  />
            <MetricRow label="Recall"          value={perf.recall}         barColor="bg-blue-500"   />
            <MetricRow label="F1 Score"        value={perf.f1_score}       barColor="bg-violet-500" />
            <MetricRow label="Accuracy"        value={perf.accuracy}       barColor="bg-rose-500"   />
            <MetricRow label="Tag Coverage"    value={perf.tag_coverage}   barColor="bg-amber-500"  />
            <MetricRow label={`Weak Hit@${K}`} value={perf.weak_hit_at_k}  barColor="bg-cyan-500"   />
          </div>
        </div>

        {/* Dataset Summary */}
        <div className="rounded-xl bg-slate-900 border border-slate-800 p-6">
          <h2 className="text-xl font-semibold mb-5">Dataset Summary</h2>
          <KVRow label="Total Users"         value={data.users.toLocaleString()} />
          <KVRow label="Total Problems"      value={data.problems.toLocaleString()} />
          <KVRow label="Total Submissions"   value={data.submissions.toLocaleString()} />
          <KVRow label="Users Evaluated"     value={data.evaluated_users.toLocaleString()} valueClass="text-blue-400" />
          <KVRow label="Recommendation Type" value="Hybrid SVD" valueClass="text-purple-400" />
        </div>

      </div>

      {/* ── Confusion Matrix + Metric Details ── */}
      <div className="grid gap-6 lg:grid-cols-2">

        {/* Weakness Confusion Matrix */}
        <div className="rounded-xl bg-slate-900 border border-slate-800 p-6">
          <h2 className="text-xl font-semibold mb-2">Weakness Confusion Matrix</h2>
          <p className="text-xs text-slate-500 mb-4">
            Average TP / FP / FN per user across {data.evaluated_users.toLocaleString()} evaluated users
          </p>
          <div className="grid grid-cols-3 gap-3">
            <ConfusionCell label="Avg TP" value={conf.avg_tp.toFixed(2)} color="border-green-800 bg-green-950/30" />
            <ConfusionCell label="Avg FP" value={conf.avg_fp.toFixed(2)} color="border-red-800 bg-red-950/30" />
            <ConfusionCell label="Avg FN" value={conf.avg_fn.toFixed(2)} color="border-amber-800 bg-amber-950/30" />
          </div>
          <p className="text-xs text-slate-600 mt-4 leading-relaxed">
            TP = weak tags covered · FP = non-weak-tag recs · FN = missed weak tags
          </p>
        </div>

        {/* Quick Metric Reference */}
        <div className="rounded-xl bg-slate-900 border border-slate-800 p-6">
          <h2 className="text-xl font-semibold mb-5">Metric Reference</h2>
          <KVRow label="Precision"       value={(perf.precision    * 100).toFixed(2) + "%"} valueClass="text-green-400"  />
          <KVRow label="Recall"          value={(perf.recall       * 100).toFixed(2) + "%"} valueClass="text-blue-400"   />
          <KVRow label="F1 Score"        value={(perf.f1_score     * 100).toFixed(2) + "%"} valueClass="text-violet-400" />
          <KVRow label="Accuracy"        value={(perf.accuracy     * 100).toFixed(2) + "%"} valueClass="text-rose-400"   />
          <KVRow label="Tag Coverage"    value={(perf.tag_coverage * 100).toFixed(2) + "%"} valueClass="text-amber-400"  />
          <KVRow label={`Weak Hit@${K}`} value={(perf.weak_hit_at_k * 100).toFixed(2) + "%"} valueClass="text-cyan-400" />
        </div>

      </div>

    </div>
  );
}