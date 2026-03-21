import { Navbar } from '@/components/layout/Navbar'
import { Hero } from '@/components/landing/Hero'
import { FeatureCards } from '@/components/landing/FeatureCards'
import { Comparison } from '@/components/landing/Comparison'

export default function LandingPage() {
  return (
    <>
      <Navbar />
      <main className="flex-1 flex flex-col">
        <Hero />
        <FeatureCards />
        <Comparison />
      </main>
      <footer className="py-12 border-t border-border mt-8 text-center text-sm text-muted">
        <p>NotionClip · 2025 · Made with ❤️</p>
      </footer>
    </>
  )
}
