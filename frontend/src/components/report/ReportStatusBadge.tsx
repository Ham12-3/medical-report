"use client";

import { getStatusConfig } from "@/lib/status-config";

interface Props {
  status: string;
}

export default function ReportStatusBadge({ status }: Props) {
  const cfg = getStatusConfig(status);

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${cfg.bg} ${cfg.text}`}
    >
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  );
}
