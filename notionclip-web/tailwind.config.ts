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
        background: "#FAF7F2",
        foreground: "#2C1F3E",
        primary: "#7A5BB5",
        accent: "#9B7FD4",
        success: "#5A8A63",
        danger: "#A0527A",
        warning: "#FCD34D",
        muted: "#8B7AA8",
        border: "rgba(155, 127, 212, 0.15)",
        "border-hover": "rgba(155, 127, 212, 0.35)",
        card: "#FFFFFF",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "sans-serif"],
        display: ["var(--font-space-grotesk)", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #9B7FD4, #7A5BB5)',
        'gradient-deep': 'linear-gradient(135deg, #7A5BB5, #3D2466)',
        'orb-blue': 'radial-gradient(circle, rgba(155,127,212,0.25) 0%, transparent 70%)',
        'orb-purple': 'radial-gradient(circle, rgba(232,180,206,0.3) 0%, transparent 70%)',
      }
    },
  },
  plugins: [],
};
export default config;
