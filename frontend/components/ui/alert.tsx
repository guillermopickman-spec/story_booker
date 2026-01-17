import * as React from "react"
import { cn } from "@/lib/utils"
import { AlertCircle, CheckCircle2, XCircle, Info } from "lucide-react"

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "success" | "error" | "warning" | "info"
}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = "default", children, ...props }, ref) => {
    const variants = {
      default: "bg-blue-50 border-blue-200 text-blue-900",
      success: "bg-green-50 border-green-200 text-green-900",
      error: "bg-red-50 border-red-200 text-red-900",
      warning: "bg-yellow-50 border-yellow-200 text-yellow-900",
      info: "bg-blue-50 border-blue-200 text-blue-900",
    }

    const icons = {
      default: <Info className="h-5 w-5" />,
      success: <CheckCircle2 className="h-5 w-5" />,
      error: <XCircle className="h-5 w-5" />,
      warning: <AlertCircle className="h-5 w-5" />,
      info: <Info className="h-5 w-5" />,
    }

    return (
      <div
        ref={ref}
        className={cn(
          "relative w-full rounded-xl border-2 p-4 flex items-start gap-3",
          variants[variant],
          className
        )}
        {...props}
      >
        <div className="flex-shrink-0 mt-0.5">{icons[variant]}</div>
        <div className="flex-1">{children}</div>
      </div>
    )
  }
)
Alert.displayName = "Alert"

export { Alert }
