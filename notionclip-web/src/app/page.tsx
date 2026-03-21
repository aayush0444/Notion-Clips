import { Navbar } from '@/components/layout/Navbar'
import { Hero } from '@/components/landing/Hero'
import { FeatureCards } from '@/components/landing/FeatureCards'
import { Comparison } from '@/components/landing/Comparison'
import { AppProvider } from '@/lib/store'

export default function LandingPage() {
  return (
    <AppProvider>
      <Navbar />
      <main className="flex-1 flex flex-col">
        <Hero />
        <FeatureCards />
        <Comparison />
      </main>
      <footer className="py-12 border-t border-border mt-8 text-center text-sm text-muted">
        <p>NotionClip · 2025</p>
      </footer>
    </AppProvider>
  )
}
