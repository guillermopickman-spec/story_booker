import * as React from "react"
import { cn } from "@/lib/utils"

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[120px] w-full rounded-xl border-2 border-gray-200 bg-white px-4 py-3 text-sm ring-offset-background placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#6366f1] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-colors resize-none",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea }
