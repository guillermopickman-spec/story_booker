import * as React from "react"
import { cn } from "@/lib/utils"

export interface CheckboxProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, ...props }, ref) => {
    return (
      <input
        type="checkbox"
        ref={ref}
        className={cn(
          "h-5 w-5 rounded border-2 border-gray-300 text-[#6366f1] focus:ring-2 focus:ring-[#6366f1] focus:ring-offset-2 cursor-pointer transition-colors",
          className
        )}
        {...props}
      />
    )
  }
)
Checkbox.displayName = "Checkbox"

export { Checkbox }
