"use client";

interface Props {
  score: number | null; // 0-1
}

export default function ConfidenceIndicator({ score }: Props) {
  if (score == null) return <span className="text-sm text-gray-400">--</span>;

  const pct = Math.round(score * 100);
  const color =
    pct >= 80 ? "text-green-600" : pct >= 50 ? "text-yellow-600" : "text-red-600";
  const bg =
    pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-yellow-500" : "bg-red-500";

  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-gray-200">
        <div className={`h-full rounded-full ${bg}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-sm font-medium ${color}`}>{pct}%</span>
    </div>
  );
}
