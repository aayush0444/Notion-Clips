"use client"

import { Check, X } from "lucide-react"
import { useAppStore } from "@/lib/store"
import { Button } from "@/components/ui/Button"
import Link from "next/link"
import { backendUrl } from "@/lib/backendUrl"
import { usePathname } from "next/navigation"

export function Navbar() {
  const { isConnected, sessionId, userId, disconnectNotion, isAuthenticated, signInWithGoogle, signOutGoogle, userEmail, getCurrentUserId } = useAppStore()
  const pathname = usePathname()
  const isHome = pathname === "/app"
  const isLibrary = pathname.startsWith("/library")

  const handleConnectNotion = async () => {
    if (!sessionId) return
    const resolvedUserId = userId || await getCurrentUserId()
    const userQuery = resolvedUserId ? `&user_id=${encodeURIComponent(resolvedUserId)}` : ""
    const frontendUrl = encodeURIComponent(window.location.origin)
    window.location.href = `${backendUrl('/auth/notion')}?session_id=${sessionId}${userQuery}&frontend_url=${frontendUrl}`
  }

  return (
    <nav className="fixed top-0 left-0 right-0 h-16 border-b border-border bg-background/90 backdrop-blur-2xl z-50 shadow-[0_8px_26px_rgba(61,36,102,0.08)]">
      <div className="max-w-[1440px] mx-auto px-8 h-full flex items-center justify-between">
        <div className="flex flex-col leading-tight">
          <Link href="/" className="text-2xl font-bold tracking-tight text-[#3D2466] hover:text-[#2C1F3E] transition-colors drop-shadow-[0_1px_0_rgba(255,255,255,0.65)]">
            NotionClip
          </Link>
          <Link href="/" className="text-[11px] text-muted tracking-[0.12em] uppercase hover:text-[#7A5BB5] transition-colors">
            Watch less. Know more
          </Link>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/app"
            className={`px-3 py-2 rounded-lg text-xs border transition-colors ${
              isHome
                ? "bg-[#EDE6FA] text-[#3D2466] border-[#CDBAEF] shadow-[0_1px_0_rgba(255,255,255,0.7)]"
                : "bg-card hover:bg-[#F0EBF8] text-foreground/80 border-border"
            }`}
          >
            Home
          </Link>
          <Link
            href="/library"
            className={`px-3 py-2 rounded-lg text-xs border transition-colors ${
              isLibrary
                ? "bg-[#EDE6FA] text-[#3D2466] border-[#CDBAEF] shadow-[0_1px_0_rgba(255,255,255,0.7)]"
                : "bg-card hover:bg-[#F0EBF8] text-foreground/80 border-border"
            }`}
          >
            Library
          </Link>
          {isAuthenticated ? (
            <button
              onClick={signOutGoogle}
                className="px-3 py-2 rounded-lg text-xs bg-card hover:bg-[#F0EBF8] text-foreground/70 border border-border transition-colors"
                title={userEmail || "Signed in"}
              >
              {userEmail ? `Sign out (${userEmail})` : "Sign out"}
            </button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={signInWithGoogle}
                className="px-4 py-2 rounded-lg text-sm bg-card hover:bg-[#F0EBF8] text-foreground border border-border hover:border-border-hover transition-colors"
              >
                Sign in with Google
              </Button>
            )}
          {isConnected ? (
            <>
              <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#F0F8F2] text-[#5A8A63] border border-[#CBE3D0]">
                <Check className="w-4 h-4" />
                <span className="text-sm">Connected to Notion</span>
              </div>
              <button
                onClick={disconnectNotion}
                className="p-2 rounded-lg bg-card hover:bg-[#FAEFF5] text-muted hover:text-[#A0527A] border border-border hover:border-[#E6C7D6] transition-all"
                title="Disconnect Notion"
              >
                <X className="w-4 h-4" />
              </button>
            </>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={handleConnectNotion}
              className="px-4 py-2 rounded-lg text-sm bg-card hover:bg-[#F0EBF8] text-foreground border border-border hover:border-border-hover"
            >
              Connect Notion
            </Button>
          )}
        </div>
      </div>
    </nav>
  )
}
