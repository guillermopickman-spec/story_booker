import { JobStatus } from "@/lib/types"
import { cn } from "@/lib/utils"
import { Clock, Loader2, CheckCircle2, XCircle } from "lucide-react"

interface StatusBadgeProps {
  status: JobStatus
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const variants = {
    pending: {
      bg: "bg-yellow-100",
      text: "text-yellow-800",
      border: "border-yellow-300",
      icon: Clock,
      label: "Pending",
    },
    processing: {
      bg: "bg-blue-100",
      text: "text-blue-800",
      border: "border-blue-300",
      icon: Loader2,
      label: "Processing",
    },
    completed: {
      bg: "bg-green-100",
      text: "text-green-800",
      border: "border-green-300",
      icon: CheckCircle2,
      label: "Completed",
    },
    failed: {
      bg: "bg-red-100",
      text: "text-red-800",
      border: "border-red-300",
      icon: XCircle,
      label: "Failed",
    },
  }

  const variant = variants[status]
  const Icon = variant.icon

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 px-3 py-1.5 rounded-full border-2 font-semibold text-sm",
        variant.bg,
        variant.text,
        variant.border,
        className
      )}
    >
      <Icon
        className={cn(
          "h-4 w-4",
          status === "processing" && "animate-spin"
        )}
      />
      <span>{variant.label}</span>
    </div>
  )
}
