"use client"
import Link from 'next/link'
import { Button } from '@/components/ui/Button'
import { useAppStore } from '@/lib/store'

export function AppHeader() {
  const { isConnected, sessionId, disconnectNotion } = useAppStore()

  const handleConnect = () => {
    if (!sessionId) return
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/auth/notion?session_id=${sessionId}`
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="font-display font-bold text-lg text-white tracking-tight">
          NotionClip
        </Link>
        <div>
          {isConnected ? (
            <div className="flex items-center space-x-3 text-sm font-medium text-white/80 bg-white/5 px-3 py-1.5 rounded-lg border border-white/10">
              <span className="flex items-center">
                <span className="h-2.5 w-2.5 rounded-full bg-success mr-2 animate-pulse" />
                Notion Connected
              </span>
              <button
                type="button"
                onClick={disconnectNotion}
                className="text-xs text-muted hover:text-danger transition-colors"
              >
                Disconnect
              </button>
            </div>
          ) : (
            <Button variant="outline" size="sm" onClick={handleConnect}>
              Connect Notion
            </Button>
          )}
        </div>
      </div>
    </header>
  )
}
