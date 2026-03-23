import type { Metadata } from "next";
import { Inter, Syne, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { AppProvider } from "@/lib/store";

const inter = Inter({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-inter" });
const syne = Syne({ subsets: ["latin"], weight: ["700"], variable: "--font-syne" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], weight: ["400"], variable: "--font-jetbrains-mono" });

export const metadata: Metadata = {
  title: "NotionClip | Stop Watching. Start Knowing.",
  description: "AI-Powered Study and Work Notes pushed to Notion.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body className={`${inter.variable} ${syne.variable} ${jetbrainsMono.variable} font-sans antialiased text-foreground selection:bg-primary/20 bg-background min-h-screen relative overflow-x-hidden`}>
        <AppProvider>
          <div className="pointer-events-none fixed inset-0 z-0 bg-background" />
          <div className="pointer-events-none fixed top-0 right-0 w-[600px] h-[600px] rounded-full opacity-[0.08] bg-orb-blue blur-[80px] -translate-y-[30%] translate-x-[30%] z-0" />
          <div className="pointer-events-none fixed bottom-0 left-0 w-[600px] h-[600px] rounded-full opacity-[0.08] bg-orb-purple blur-[80px] translate-y-[30%] -translate-x-[30%] z-0" />

          <div className="relative z-10 flex flex-col min-h-screen">
            {children}
          </div>
        </AppProvider>
      </body>
    </html>
  );
}
