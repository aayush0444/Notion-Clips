"use client"
import Link from 'next/link'
import { Button } from '@/components/ui/Button'
import { useAppStore } from '@/lib/store'

export function Navbar() {
  const { sessionId } = useAppStore()

  const handleConnect = () => {
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/auth/notion?session_id=${sessionId}`
  }
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/app" className="flex items-center">
          <span className="font-display text-xl font-bold text-white tracking-tight">
            NotionClip
          </span>
        </Link>
        <div className="flex items-center space-x-4">
          <Button variant="outline" onClick={handleConnect}>Connect Notion</Button>
        </div>
      </div>
    </nav>
  )
}
