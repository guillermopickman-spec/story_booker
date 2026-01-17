import * as React from "react"
import { cn } from "@/lib/utils"

export interface ProgressProps
  extends React.HTMLAttributes<HTMLDivElement> {
  value?: number
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "relative h-4 w-full overflow-hidden rounded-full bg-gray-200",
          className
        )}
        {...props}
      >
        <div
          className="h-full w-full flex-1 bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] transition-all duration-500 ease-out rounded-full"
          style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
        />
      </div>
    )
  }
)
Progress.displayName = "Progress"

export { Progress }
