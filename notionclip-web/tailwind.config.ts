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
        background: "#0a0a14",
        foreground: "#F8FAFC",
        primary: "#60A5FA",
        accent: "#A78BFA",
        success: "#34D399",
        danger: "#F87171",
        warning: "#FCD34D",
        muted: "#64748B",
        card: {
          DEFAULT: "rgba(255, 255, 255, 0.03)",
          border: "rgba(255, 255, 255, 0.08)",
          hover: "rgba(255, 255, 255, 0.16)",
        }
      },
      fontFamily: {
        sans: ["var(--font-inter)", "sans-serif"],
        display: ["var(--font-syne)", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #60A5FA, #A78BFA)',
        'gradient-deep': 'linear-gradient(135deg, #3B82F6, #7C3AED)',
      }
    },
  },
  plugins: [],
};
export default config;
