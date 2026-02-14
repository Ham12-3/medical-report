export interface StatusConfig {
  label: string;
  bg: string;
  text: string;
  dot: string;
  isError: boolean;
}

const configs: Record<string, StatusConfig> = {
  uploaded: {
    label: "Uploaded",
    bg: "bg-yellow-50",
    text: "text-yellow-700",
    dot: "bg-yellow-400",
    isError: false,
  },
  image_analyzed: {
    label: "Analyzed",
    bg: "bg-blue-50",
    text: "text-blue-700",
    dot: "bg-blue-400",
    isError: false,
  },
  research_complete: {
    label: "Researched",
    bg: "bg-indigo-50",
    text: "text-indigo-700",
    dot: "bg-indigo-400",
    isError: false,
  },
  report_generated: {
    label: "Generated",
    bg: "bg-purple-50",
    text: "text-purple-700",
    dot: "bg-purple-400",
    isError: false,
  },
  complete: {
    label: "Complete",
    bg: "bg-green-50",
    text: "text-green-700",
    dot: "bg-green-500",
    isError: false,
  },
  analysis_failed: {
    label: "Analysis Failed",
    bg: "bg-red-50",
    text: "text-red-700",
    dot: "bg-red-500",
    isError: true,
  },
  research_failed: {
    label: "Research Failed",
    bg: "bg-red-50",
    text: "text-red-700",
    dot: "bg-red-500",
    isError: true,
  },
  generation_failed: {
    label: "Generation Failed",
    bg: "bg-red-50",
    text: "text-red-700",
    dot: "bg-red-500",
    isError: true,
  },
  safety_failed: {
    label: "Safety Failed",
    bg: "bg-red-50",
    text: "text-red-700",
    dot: "bg-red-500",
    isError: true,
  },
};

const fallback: StatusConfig = {
  label: "Unknown",
  bg: "bg-gray-50",
  text: "text-gray-700",
  dot: "bg-gray-400",
  isError: false,
};

export function getStatusConfig(status: string): StatusConfig {
  return configs[status] || fallback;
}
