"use client";

import * as React from "react"
import { cn } from "@/lib/utils"
import { motion, HTMLMotionProps } from "framer-motion"

export interface ButtonProps extends HTMLMotionProps<"button"> {
  variant?: "default" | "outline" | "ghost" | "gradient" | "glass"
  size?: "default" | "sm" | "lg"
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    const baseStyles = "inline-flex items-center justify-center whitespace-nowrap rounded-[10px] font-medium transition-colors focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50"
    
    const variants = {
      default: "bg-primary text-primary-foreground hover:bg-primary/90",
      outline: "border border-border bg-transparent hover:bg-slate-100/80 text-slate-700",
      ghost: "hover:bg-slate-100/80 hover:text-slate-900 text-muted",
      gradient: "bg-gradient-to-r from-[#60A5FA] to-[#A78BFA] text-white hover:opacity-90 font-semibold border-0",
      glass: "bg-white/75 border border-[#ddd4f6] backdrop-blur-md text-slate-800 hover:bg-white"
    }
    
    const sizes = {
      default: "h-10 px-4 py-2",
      sm: "h-9 rounded-md px-3",
      lg: "h-12 rounded-[12px] px-8 text-lg"
    }

    return (
      <motion.button
        ref={ref}
        whileHover={{ translateY: -2 }}
        whileTap={{ scale: 0.97 }}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
