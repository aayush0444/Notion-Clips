"use client"
import { AppProvider } from '@/lib/store'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <AppProvider>{children}</AppProvider>
}
