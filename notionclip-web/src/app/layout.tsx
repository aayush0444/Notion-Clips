import type { Metadata } from "next";
import { Inter, Syne, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-inter" });
const syne = Syne({ subsets: ["latin"], weight: ["700", "800"], variable: "--font-syne" });
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
        {/* Minimalist solid background overlay */}
        <div className="pointer-events-none fixed inset-0 z-0 bg-background" />
        
        <div className="pointer-events-none fixed top-[-120px] right-[-100px] w-[500px] h-[500px] rounded-full bg-blue-500/[0.06] blur-[120px] z-0" />
        <div className="pointer-events-none fixed bottom-[40px] left-[-80px] w-[400px] h-[400px] rounded-full bg-purple-500/[0.06] blur-[120px] z-0" />
        
        <div className="relative z-10 flex flex-col min-h-screen">
          {children}
        </div>
      </body>
    </html>
  );
}
