import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0a0a",
        foreground: "#F8FAFC",
        primary: "#60A5FA",
        accent: "#A78BFA",
        success: "#34D399",
        danger: "#F87171",
        warning: "#FCD34D",
        muted: "#64748B",
        border: "rgba(255, 255, 255, 0.08)",
        "border-hover": "rgba(255, 255, 255, 0.16)",
        card: "rgba(255, 255, 255, 0.03)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "sans-serif"],
        display: ["var(--font-syne)", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #60A5FA, #A78BFA)',
        'gradient-deep': 'linear-gradient(135deg, #3B82F6, #7C3AED)',
        'orb-blue': 'radial-gradient(circle, rgba(59,130,246,0.5) 0%, transparent 70%)',
        'orb-purple': 'radial-gradient(circle, rgba(168,85,247,0.5) 0%, transparent 70%)',
      }
    },
  },
  plugins: [],
};
export default config;
