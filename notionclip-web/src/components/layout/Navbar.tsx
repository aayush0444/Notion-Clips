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
    <nav className="fixed top-0 left-0 right-0 h-20 border-b border-border bg-background/90 backdrop-blur-2xl z-50 shadow-[0_8px_32px_rgba(61,36,102,0.1)]">
      <div className="max-w-[1440px] mx-auto px-10 h-full flex items-center justify-between">
        <div className="flex flex-col leading-tight">
          <Link href="/" className="text-3xl font-bold tracking-tight text-[#3D2466] hover:text-[#2C1F3E] transition-colors drop-shadow-[0_1px_0_rgba(255,255,255,0.65)]">
            NotionClip
          </Link>
          <Link href="/" className="text-xs text-muted tracking-[0.16em] uppercase hover:text-[#7A5BB5] transition-colors mt-0.5">
            Watch less. Know more
          </Link>
        </div>

        <div className="flex items-center gap-4">
          <Link
            href="/app"
            className={`px-5 py-2.5 rounded-xl text-sm font-semibold border transition-all ${
              isHome
                ? "bg-[#EDE6FA] text-[#3D2466] border-[#CDBAEF] shadow-[0_2px_4px_rgba(122,91,181,0.12)]"
                : "bg-card hover:bg-[#F0EBF8] text-foreground/80 border-border hover:-translate-y-0.5"
            }`}
          >
            Home
          </Link>
          <Link
            href="/library"
            className={`px-5 py-2.5 rounded-xl text-sm font-semibold border transition-all ${
              isLibrary
                ? "bg-[#EDE6FA] text-[#3D2466] border-[#CDBAEF] shadow-[0_2px_4px_rgba(122,91,181,0.12)]"
                : "bg-card hover:bg-[#F0EBF8] text-foreground/80 border-border hover:-translate-y-0.5"
            }`}
          >
            Library
          </Link>
          {isAuthenticated ? (
            <button
              onClick={signOutGoogle}
                className="px-5 py-2.5 rounded-xl text-sm font-semibold bg-card hover:bg-[#FAEFF5] text-foreground/70 border border-border hover:border-[#E6C7D6] transition-all hover:-translate-y-0.5"
                title={userEmail || "Signed in"}
              >
              {userEmail ? `Sign out (${userEmail.split('@')[0]})` : "Sign out"}
            </button>
          ) : (
            <Button
              variant="outline"
              onClick={signInWithGoogle}
                className="px-6 py-2.5 rounded-xl text-base font-semibold bg-card hover:bg-[#F0EBF8] text-foreground border border-border hover:border-[#BDA4E2] transition-all hover:-translate-y-0.5"
              >
                Sign in with Google
              </Button>
            )}
          {isConnected ? (
            <>
              <div className="flex items-center gap-3 px-5 py-2.5 rounded-xl bg-[#F0F8F2] text-[#2E7D57] border border-[#CBE3D0] shadow-sm">
                <Check className="w-5 h-5" />
                <span className="text-sm font-bold">Connected to Notion</span>
              </div>
              <button
                onClick={disconnectNotion}
                className="p-2.5 rounded-xl bg-card hover:bg-[#FAEFF5] text-muted hover:text-[#A0527A] border border-border hover:border-[#E6C7D6] transition-all shadow-sm"
                title="Disconnect Notion"
              >
                <X className="w-5 h-5" />
              </button>
            </>
          ) : (
            <Button
              variant="outline"
              onClick={handleConnectNotion}
              className="px-6 py-2.5 rounded-xl text-base font-semibold bg-card hover:bg-[#F0EBF8] text-foreground border border-border hover:border-[#BDA4E2] transition-all hover:-translate-y-0.5"
            >
              Connect Notion
            </Button>
          )}
        </div>
      </div>
    </nav>
  )
}
