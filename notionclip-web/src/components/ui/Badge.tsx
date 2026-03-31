import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "outline" | "secondary" | "success" | "danger" | "warning"
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variants = {
    default: "bg-primary/20 text-primary border-primary/20",
    secondary: "bg-white/80 text-slate-700 border-[#ddd4f6]",
    outline: "text-muted border-border",
    success: "bg-success/20 text-success border-success/20",
    danger: "bg-danger/20 text-danger border-danger/20",
    warning: "bg-warning/20 text-warning border-warning/20"
  }
  
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        variants[variant],
        className
      )}
      {...props}
    />
  )
}

export { Badge }
