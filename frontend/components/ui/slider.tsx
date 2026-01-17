import * as React from "react"
import { cn } from "@/lib/utils"

export interface SliderProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  value?: number
  onValueChange?: (value: number) => void
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ className, value, onValueChange, ...props }, ref) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = Number(e.target.value)
      onValueChange?.(newValue)
    }

    return (
      <div className="relative w-full">
        <input
          type="range"
          ref={ref}
          value={value}
          onChange={handleChange}
          className={cn(
            "w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#6366f1]",
            className
          )}
          style={{
            background: `linear-gradient(to right, #6366f1 0%, #6366f1 ${((value || 0) - (props.min as number || 0)) / ((props.max as number || 10) - (props.min as number || 0)) * 100}%, #e5e7eb ${((value || 0) - (props.min as number || 0)) / ((props.max as number || 10) - (props.min as number || 0)) * 100}%, #e5e7eb 100%)`,
          }}
          {...props}
        />
      </div>
    )
  }
)
Slider.displayName = "Slider"

export { Slider }
