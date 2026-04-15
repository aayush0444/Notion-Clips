"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useCallback, useEffect, useState, type MouseEvent as ReactMouseEvent } from "react"

export default function HomePage() {
  const router = useRouter()
  const [isTransitioning, setIsTransitioning] = useState(false)

  const handleAppNavigation = useCallback((event: ReactMouseEvent<HTMLAnchorElement>) => {
    if (
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    ) {
      return
    }
    event.preventDefault()
    if (isTransitioning) return
    setIsTransitioning(true)
    window.setTimeout(() => {
      router.push("/app")
    }, 220)
  }, [isTransitioning, router])

  useEffect(() => {
    const cursor = document.getElementById("cursor")
    const ring = document.getElementById("cursor-ring")

    let mx = 0
    let my = 0
    let rx = 0
    let ry = 0
    let cursorFrame = 0

    const onMouseMove = (e: globalThis.MouseEvent) => {
      mx = e.clientX
      my = e.clientY
    }

    const animateCursor = () => {
      rx += (mx - rx) * 0.15
      ry += (my - ry) * 0.15

      if (cursor) {
        cursor.style.left = `${mx}px`
        cursor.style.top = `${my}px`
      }
      if (ring) {
        ring.style.left = `${rx}px`
        ring.style.top = `${ry}px`
      }
      cursorFrame = requestAnimationFrame(animateCursor)
    }

    const hoverTargets = document.querySelectorAll(
      "a,button,.tilt-card,.bento-cell,.mode-tab,.pricing-card,.testimonial-card"
    )

    const onMouseEnter = () => {
      if (!cursor || !ring) return
      cursor.style.width = "14px"
      cursor.style.height = "14px"
      ring.style.width = "48px"
      ring.style.height = "48px"
      ring.style.borderColor = "rgba(122,91,181,0.65)"
    }

    const onMouseLeave = () => {
      if (!cursor || !ring) return
      cursor.style.width = "8px"
      cursor.style.height = "8px"
      ring.style.width = "32px"
      ring.style.height = "32px"
      ring.style.borderColor = "rgba(155,127,212,0.45)"
    }

    hoverTargets.forEach((el) => {
      el.addEventListener("mouseenter", onMouseEnter)
      el.addEventListener("mouseleave", onMouseLeave)
    })

    const nav = document.getElementById("nav")
    const onScroll = () => {
      if (nav) {
        nav.classList.toggle("scrolled", window.scrollY > 40)
      }
    }

    let ox = 0
    let oy = 0
    const onMouseMoveParallax = (e: globalThis.MouseEvent) => {
      ox = (e.clientX / window.innerWidth - 0.5) * 2
      oy = (e.clientY / window.innerHeight - 0.5) * 2
    }

    const blob1 = document.getElementById("blob1")
    const blob2 = document.getElementById("blob2")
    const blob3 = document.getElementById("blob3")
    let blobFrame = 0

    const animateBlobs = () => {
      if (blob1) blob1.style.transform = `translate(${ox * 24}px,${oy * 16}px)`
      if (blob2) blob2.style.transform = `translate(${ox * -18}px,${oy * -20}px)`
      if (blob3) blob3.style.transform = `translate(${ox * 12}px,${oy * 18}px)`
      blobFrame = requestAnimationFrame(animateBlobs)
    }

    const mockupWrapper = document.getElementById("mockupWrapper")

    const initTilt = (selector: string, deg: number) => {
      document.querySelectorAll(selector).forEach((element) => {
        const el = element as HTMLElement
        const onMove = (e: Event) => {
          const evt = e as globalThis.MouseEvent
          const rect = el.getBoundingClientRect()
          const dx = (evt.clientX - rect.left - rect.width / 2) / (rect.width / 2)
          const dy = (evt.clientY - rect.top - rect.height / 2) / (rect.height / 2)
          el.style.transform = `perspective(900px) rotateY(${dx * deg}deg) rotateX(${-dy * deg}deg) translateZ(5px)`
          el.style.setProperty("--mx", `${((evt.clientX - rect.left) / rect.width) * 100}%`)
          el.style.setProperty("--my", `${((evt.clientY - rect.top) / rect.height) * 100}%`)
        }
        const onLeave = () => {
          el.style.transform = "perspective(900px) rotateY(0) rotateX(0) translateZ(0)"
        }
        el.addEventListener("mousemove", onMove)
        el.addEventListener("mouseleave", onLeave)
      })
    }

    initTilt("[data-tilt]", 6)
    initTilt("[data-tilt-card]", 4)
    initTilt("[data-bento]", 5)

    const heroVisual = document.getElementById("heroVisual")
    let heroRaf = 0
    let heroDx = 0
    let heroDy = 0
    let onHeroMove: ((e: Event) => void) | null = null
    let onHeroLeave: (() => void) | null = null
    if (heroVisual && mockupWrapper) {
      onHeroMove = (e: Event) => {
        const evt = e as globalThis.MouseEvent
        const rect = heroVisual.getBoundingClientRect()
        heroDx = (evt.clientX - rect.left - rect.width / 2) / (rect.width / 2)
        heroDy = (evt.clientY - rect.top - rect.height / 2) / (rect.height / 2)

        if (heroRaf) return
        heroRaf = requestAnimationFrame(() => {
          mockupWrapper.style.animation = "none"
          mockupWrapper.style.transform = `perspective(1400px) rotateY(${heroDx * 6}deg) rotateX(${-heroDy * 3.2}deg) translate3d(0,-6px,0)`
          heroRaf = 0
        })
      }

      onHeroLeave = () => {
        if (heroRaf) {
          cancelAnimationFrame(heroRaf)
          heroRaf = 0
        }
        mockupWrapper.style.animation = "floatLight 7s ease-in-out infinite"
        mockupWrapper.style.transform = ""
      }

      heroVisual.addEventListener("mousemove", onHeroMove)
      heroVisual.addEventListener("mouseleave", onHeroLeave)
    }

    const modeTabs = document.querySelectorAll(".mode-tab")
    modeTabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        modeTabs.forEach((t) => t.classList.remove("active"))
        document.querySelectorAll(".mode-panel").forEach((p) => p.classList.remove("active"))
        tab.classList.add("active")
        const mode = tab.getAttribute("data-mode")
        const panel = document.getElementById(`panel-${mode}`)
        if (panel) panel.classList.add("active")
      })
    })

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible")
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.1 }
    )
    document.querySelectorAll(".reveal").forEach((el) => observer.observe(el))

    document.addEventListener("mousemove", onMouseMove)
    document.addEventListener("mousemove", onMouseMoveParallax)
    window.addEventListener("scroll", onScroll)

    animateCursor()
    animateBlobs()
    onScroll()

    return () => {
      cancelAnimationFrame(cursorFrame)
      cancelAnimationFrame(blobFrame)
      if (heroRaf) cancelAnimationFrame(heroRaf)
      document.removeEventListener("mousemove", onMouseMove)
      document.removeEventListener("mousemove", onMouseMoveParallax)
      window.removeEventListener("scroll", onScroll)
      if (heroVisual && onHeroMove) {
        heroVisual.removeEventListener("mousemove", onHeroMove)
      }
      if (heroVisual && onHeroLeave) {
        heroVisual.removeEventListener("mouseleave", onHeroLeave)
      }
      hoverTargets.forEach((el) => {
        el.removeEventListener("mouseenter", onMouseEnter)
        el.removeEventListener("mouseleave", onMouseLeave)
      })
      observer.disconnect()
    }
  }, [])

  return (
    <>
      <style suppressHydrationWarning dangerouslySetInnerHTML={{ __html: `
        .landing-page *, .landing-page *::before, .landing-page *::after { box-sizing: border-box; margin: 0; padding: 0; }

        .landing-page {
          --cream: #faf7f2;
          --cream-warm: #f5f0e8;
          --lilac-pale: #f0ebf8;
          --lilac-soft: #e4d9f5;
          --lilac: #9b7fd4;
          --lilac-deep: #7a5bb5;
          --lilac-dark: #3d2466;
          --blush: #f5e6ef;
          --sage: #d4e8d8;
          --sage-deep: #5a8a63;
          --ink: #2c1f3e;
          --ink-mid: #5a4a72;
          --ink-soft: #8b7aa8;
          --ink-muted: #b8aacc;
          --border: rgba(155, 127, 212, 0.15);
          --border-mid: rgba(155, 127, 212, 0.28);
          --border-deep: rgba(155, 127, 212, 0.45);
          --shadow-soft: 0 4px 24px rgba(61, 36, 102, 0.07);
          --shadow-mid: 0 12px 48px rgba(61, 36, 102, 0.1);
          --shadow-lift: 0 24px 80px rgba(61, 36, 102, 0.13);
          --serif: var(--font-space-grotesk), 'Inter', 'Segoe UI', sans-serif;
          --sans: var(--font-inter), 'Inter', 'Segoe UI', sans-serif;
          --radius: 16px;
          --radius-lg: 24px;
          --radius-xl: 32px;

          background: var(--cream);
          color: var(--ink);
          font-family: var(--sans);
          font-size: 16px;
          line-height: 1.65;
          -webkit-font-smoothing: antialiased;
          overflow-x: hidden;
          cursor: none;
          min-height: 100vh;
          position: relative;
        }

        .landing-page a { color: inherit; }
        .landing-page .container { max-width: 1120px; margin: 0 auto; padding: 0 36px; position: relative; z-index: 1; }

        #cursor {
          position: fixed;
          width: 8px;
          height: 8px;
          background: var(--lilac-deep);
          border-radius: 50%;
          pointer-events: none;
          z-index: 9999;
          transform: translate(-50%, -50%);
          transition: width 0.25s, height 0.25s;
          mix-blend-mode: multiply;
        }
        #cursor-ring {
          position: fixed;
          width: 32px;
          height: 32px;
          border: 1.5px solid rgba(155, 127, 212, 0.45);
          border-radius: 50%;
          pointer-events: none;
          z-index: 9998;
          transform: translate(-50%, -50%);
          transition: transform 0.16s ease, width 0.25s, height 0.25s;
        }

        .landing-page::before {
          content: '';
          position: fixed;
          inset: 0;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.025'/%3E%3C/svg%3E");
          pointer-events: none;
          z-index: 0;
        }

        .blob { position: fixed; border-radius: 50%; pointer-events: none; z-index: 0; filter: blur(90px); will-change: transform; }
        .blob-1 { width: 580px; height: 580px; background: radial-gradient(circle, #e4d9f5, #f0ebf8); opacity: 0.7; top: -160px; right: -120px; }
        .blob-2 { width: 420px; height: 420px; background: radial-gradient(circle, #f5e6ef, #faf0f5); opacity: 0.55; bottom: 60px; left: -130px; }
        .blob-3 { width: 300px; height: 300px; background: radial-gradient(circle, #d4e8d8, #eaf4ec); opacity: 0.45; top: 50%; right: 8%; }

        nav { position: fixed; top: 0; left: 0; right: 0; z-index: 100; padding: 22px 0; transition: background 0.35s, box-shadow 0.35s; box-shadow: 0 10px 26px rgba(61, 36, 102, 0.08); }
        nav.scrolled { background: rgba(250, 247, 242, 0.88); backdrop-filter: blur(20px) saturate(1.6); box-shadow: 0 1px 0 var(--border), 0 12px 30px rgba(61, 36, 102, 0.12); }
        .nav-inner { max-width: 1120px; margin: 0 auto; padding: 0 36px; display: flex; align-items: center; justify-content: space-between; }
        .nav-logo { font-family: var(--serif); font-size: 21px; color: var(--ink); text-decoration: none; letter-spacing: -0.02em; font-weight: 600; }
        .nav-logo span { color: var(--lilac-deep); }
        .nav-links { display: flex; align-items: center; gap: 38px; }
        .nav-links a { font-size: 14px; color: var(--ink-mid); text-decoration: none; font-weight: 400; transition: color 0.2s; letter-spacing: 0.01em; }
        .nav-links a:hover { color: var(--ink); }
        .nav-cta { background: var(--lilac-deep) !important; color: #fff !important; padding: 9px 22px !important; border-radius: 100px !important; font-size: 14px !important; font-weight: 500 !important; transition: background 0.2s, transform 0.15s, box-shadow 0.2s !important; box-shadow: 0 4px 20px rgba(122, 91, 181, 0.25) !important; }
        .nav-cta:hover { background: var(--lilac-dark) !important; transform: translateY(-1px) !important; box-shadow: 0 8px 32px rgba(122, 91, 181, 0.32) !important; }

        .hero { padding: 185px 0 100px; text-align: center; position: relative; }
        .hero-eyebrow { display: inline-flex; align-items: center; gap: 8px; background: var(--lilac-pale); border: 1px solid var(--border-mid); border-radius: 100px; padding: 7px 20px; font-size: 11px; color: var(--lilac-deep); letter-spacing: 0.1em; text-transform: uppercase; font-weight: 500; margin-bottom: 40px; animation: fadeUp 0.65s ease both; }
        .eyebrow-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--lilac); animation: pulse 2.4s infinite; }
        .hero-headline { font-family: var(--serif); font-size: clamp(50px, 7vw, 90px); line-height: 1.04; letter-spacing: -0.025em; color: var(--ink); margin-bottom: 28px; animation: fadeUp 0.65s ease 0.1s both; font-weight: 700; }
        .hero-headline em { font-style: normal; color: var(--lilac-deep); font-weight: 700; }
        .hero-headline .muted { color: var(--ink-soft); }
        .hero-sub { font-size: 18px; color: var(--ink-mid); max-width: 500px; margin: 0 auto 52px; font-weight: 300; line-height: 1.8; animation: fadeUp 0.65s ease 0.2s both; }
        .hero-actions { display: flex; align-items: center; justify-content: center; gap: 16px; margin-bottom: 80px; animation: fadeUp 0.65s ease 0.3s both; }

        .btn-primary { background: var(--lilac-deep); color: #fff; padding: 15px 36px; border-radius: 100px; font-size: 15px; font-weight: 500; text-decoration: none; transition: background 0.2s, transform 0.2s, box-shadow 0.2s; box-shadow: 0 6px 32px rgba(122, 91, 181, 0.28); letter-spacing: 0.01em; position: relative; overflow: hidden; }
        .btn-primary::after { content: ''; position: absolute; inset: 0; background: linear-gradient(135deg, rgba(255, 255, 255, 0.18), transparent); opacity: 0; transition: opacity 0.2s; }
        .btn-primary:hover { background: var(--lilac-dark); transform: translateY(-2px); box-shadow: 0 12px 48px rgba(122, 91, 181, 0.35); }
        .btn-primary:hover::after { opacity: 1; }
        .btn-ghost { color: var(--ink-mid); padding: 15px 20px; border-radius: 100px; font-size: 15px; font-weight: 400; text-decoration: none; transition: color 0.2s; display: flex; align-items: center; gap: 6px; }
        .btn-ghost:hover { color: var(--ink); }
        .btn-ghost .arrow { transition: transform 0.25s; display: inline-block; }
        .btn-ghost:hover .arrow { transform: translateX(5px); }

        .hero-visual { animation: fadeUp 0.9s ease 0.4s both; position: relative; max-width: 820px; margin: 0 auto; perspective: 1400px; }
        .mockup-wrapper { animation: floatLight 7s ease-in-out infinite; transform-style: preserve-3d; will-change: transform; }
        .notion-mockup { background: #fffef9; border: 1px solid rgba(155, 127, 212, 0.2); border-radius: var(--radius-lg); overflow: hidden; box-shadow: 0 1px 0 rgba(255, 255, 255, 0.9) inset, 0 40px 100px rgba(61, 36, 102, 0.1), 0 0 0 1px rgba(155, 127, 212, 0.08); transition: box-shadow 0.4s; }
        .notion-mockup:hover { box-shadow: 0 1px 0 rgba(255, 255, 255, 0.9) inset, 0 50px 120px rgba(61, 36, 102, 0.14), 0 0 0 1px rgba(155, 127, 212, 0.15), 0 0 60px rgba(155, 127, 212, 0.06); }
        .notion-topbar { background: #f8f4ee; padding: 13px 20px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid rgba(155, 127, 212, 0.1); }
        .traffic-lights { display: flex; gap: 7px; }
        .tl { width: 11px; height: 11px; border-radius: 50%; }
        .tl-r { background: #ff6b6b; }
        .tl-y { background: #ffd93d; }
        .tl-g { background: #6bcb77; }
        .notion-url { flex: 1; text-align: center; font-size: 12px; color: var(--ink-muted); font-weight: 300; }
        .notion-body { padding: 36px 48px 44px; text-align: left; }
        .notion-emoji { font-size: 30px; margin-bottom: 14px; display: block; }
        .notion-title { font-family: var(--serif); font-size: 24px; font-weight: 500; color: var(--ink); margin-bottom: 22px; letter-spacing: -0.015em; }
        .notion-callout { background: var(--lilac-pale); border: 1px solid var(--border-mid); border-radius: 10px; padding: 14px 18px; font-size: 13px; color: var(--ink-mid); line-height: 1.65; margin-bottom: 20px; display: flex; gap: 12px; }
        .notion-h2 { font-size: 10px; font-weight: 500; color: var(--ink-muted); letter-spacing: 0.1em; text-transform: uppercase; margin: 20px 0 10px; }
        .notion-formula { background: #f0f8f2; border: 1px solid rgba(90, 138, 99, 0.2); border-radius: 8px; padding: 10px 14px; font-family: 'Courier New', monospace; font-size: 12px; color: var(--sage-deep); margin: 6px 0; }
        .notion-toggle { border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; font-size: 13px; color: var(--ink-mid); margin: 4px 0; display: flex; gap: 10px; transition: border-color 0.2s, background 0.2s; }
        .notion-toggle:hover { border-color: var(--border-mid); background: var(--lilac-pale); }
        .verdict-badge { display: inline-flex; align-items: center; gap: 6px; background: var(--sage); border: 1px solid rgba(90, 138, 99, 0.25); border-radius: 8px; padding: 6px 12px; font-size: 12px; color: var(--sage-deep); font-weight: 500; margin-bottom: 16px; }
        .mockup-shadow { position: absolute; bottom: -20px; left: 10%; right: 10%; height: 40px; background: radial-gradient(ellipse, rgba(122, 91, 181, 0.12), transparent 70%); filter: blur(12px); }

        .proof-bar { padding: 36px 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: center; gap: 56px; flex-wrap: wrap; margin-top: 90px; }
        .proof-stat { text-align: center; }
        .proof-number { font-family: var(--serif); font-size: 30px; color: var(--ink); display: block; letter-spacing: -0.02em; font-weight: 700; }
        .proof-label { font-size: 13px; color: var(--ink-muted); font-weight: 300; margin-top: 2px; }
        .proof-divider { width: 1px; height: 44px; background: var(--border-mid); }

        .section-tag { display: inline-block; font-size: 11px; color: var(--lilac); letter-spacing: 0.1em; text-transform: uppercase; font-weight: 500; margin-bottom: 14px; }
        .section-headline { font-family: var(--serif); font-size: clamp(34px, 4.5vw, 54px); line-height: 1.1; letter-spacing: -0.02em; color: var(--ink); margin-bottom: 18px; font-weight: 700; }
        .section-headline em { font-style: normal; color: var(--lilac-deep); font-weight: 700; }
        .section-sub { font-size: 17px; color: var(--ink-mid); font-weight: 300; max-width: 480px; line-height: 1.8; }

        .problem { padding: 130px 0; }
        .problem-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 72px; align-items: center; }
        .problem-cards { display: flex; flex-direction: column; gap: 14px; }
        .tilt-card { background: #fff; border: 1px solid var(--border); border-radius: var(--radius); padding: 22px 24px; display: flex; gap: 16px; align-items: flex-start; box-shadow: var(--shadow-soft); transition: border-color 0.3s, box-shadow 0.3s, transform 0.3s; transform-style: preserve-3d; will-change: transform; }
        .tilt-card:hover { border-color: var(--border-deep); box-shadow: var(--shadow-lift); }
        .problem-icon { width: 40px; height: 40px; border-radius: 10px; background: var(--lilac-pale); border: 1px solid var(--border-mid); display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
        .problem-text-head { font-size: 14px; font-weight: 500; color: var(--ink); margin-bottom: 5px; }
        .problem-text-body { font-size: 13px; color: var(--ink-soft); line-height: 1.6; font-weight: 300; }

        .modes { padding: 130px 0; }
        .modes-tabs { display: flex; gap: 4px; margin-bottom: 52px; border-bottom: 1px solid var(--border); }
        .mode-tab { padding: 12px 26px; font-size: 14px; font-weight: 400; color: var(--ink-muted); cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; transition: color 0.22s, border-color 0.22s; }
        .mode-tab.active { color: var(--ink); border-bottom-color: var(--lilac-deep); }
        .mode-panel { display: none; }
        .mode-panel.active { display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: start; }
        .mode-content h3 { font-family: var(--serif); font-size: 33px; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 16px; line-height: 1.2; }
        .mode-content h3 em { font-style: normal; font-weight: 700; color: var(--lilac-deep); }
        .mode-content p { font-size: 16px; color: var(--ink-mid); font-weight: 300; line-height: 1.8; margin-bottom: 28px; }
        .mode-features { display: flex; flex-direction: column; gap: 10px; }
        .mode-feature { display: flex; gap: 12px; align-items: flex-start; font-size: 14px; color: var(--ink-mid); padding: 5px 0; }
        .feature-check { width: 18px; height: 18px; border-radius: 50%; background: var(--lilac-pale); border: 1px solid var(--border-mid); display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 1px; font-size: 10px; color: var(--lilac-deep); }
        .mode-output-card { background: #fff; border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 28px; box-shadow: var(--shadow-mid); transition: transform 0.4s ease, box-shadow 0.4s ease; transform-style: preserve-3d; will-change: transform; }
        .mode-output-card:hover { transform: translateY(-6px) rotateX(1.5deg); box-shadow: var(--shadow-lift); }
        .output-label { font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-muted); margin-bottom: 16px; font-weight: 500; }
        .output-row { display: flex; flex-direction: column; gap: 8px; }
        .output-item { background: var(--cream); border: 1px solid var(--border); border-radius: 10px; padding: 12px 16px; font-size: 13px; color: var(--ink-mid); line-height: 1.6; }
        .output-item-tag { font-size: 10px; font-weight: 500; letter-spacing: 0.07em; text-transform: uppercase; color: var(--lilac); margin-bottom: 4px; }
        .output-formula { font-family: 'Courier New', monospace; font-size: 12px; color: var(--sage-deep); background: #f2f8f3; border: 1px solid rgba(90, 138, 99, 0.2); border-radius: 8px; padding: 9px 13px; }

        .features { padding: 130px 0; }
        .bento-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px; margin-top: 64px; }
        .bento-cell { background: #fff; border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 30px 26px; box-shadow: var(--shadow-soft); transition: border-color 0.3s, box-shadow 0.3s, transform 0.3s; transform-style: preserve-3d; will-change: transform; position: relative; overflow: hidden; }
        .bento-cell:hover { border-color: var(--border-deep); box-shadow: var(--shadow-lift); }
        .bento-wide { grid-column: span 4; }
        .bento-narrow { grid-column: span 2; }
        .bento-mid { grid-column: span 3; }
        .bento-icon { width: 44px; height: 44px; border-radius: 12px; background: var(--lilac-pale); border: 1px solid var(--border-mid); display: flex; align-items: center; justify-content: center; font-size: 20px; margin-bottom: 20px; }
        .bento-title { font-size: 16px; font-weight: 500; color: var(--ink); margin-bottom: 9px; letter-spacing: -0.01em; }
        .bento-desc { font-size: 14px; color: var(--ink-soft); line-height: 1.65; font-weight: 300; }
        .bento-tag { display: inline-block; margin-top: 16px; background: var(--lilac-pale); border: 1px solid var(--border-mid); border-radius: 100px; padding: 4px 14px; font-size: 11px; color: var(--lilac-deep); font-weight: 500; letter-spacing: 0.04em; }

        .testimonials { padding: 130px 0; }
        .testimonial-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 64px; }
        .testimonial-card { background: #fff; border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 30px; box-shadow: var(--shadow-soft); transition: border-color 0.3s, transform 0.4s, box-shadow 0.4s; transform-style: preserve-3d; }
        .testimonial-card:hover { border-color: var(--border-mid); transform: translateY(-7px); box-shadow: var(--shadow-lift); }
        .stars { display: flex; gap: 3px; margin-bottom: 16px; }
        .star { color: #e8a020; font-size: 13px; }
        .testimonial-quote { font-family: var(--sans); font-weight: 400; font-size: 15px; color: var(--ink-mid); line-height: 1.75; margin-bottom: 22px; }
        .testimonial-author { display: flex; align-items: center; gap: 12px; }
        .author-avatar { width: 38px; height: 38px; border-radius: 50%; background: var(--lilac-pale); border: 1px solid var(--border-mid); display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 500; color: var(--lilac-deep); }
        .author-name { font-size: 13px; font-weight: 500; color: var(--ink); }
        .author-role { font-size: 12px; color: var(--ink-muted); font-weight: 300; }

        .pricing { padding: 130px 0; }
        .pricing-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; max-width: 780px; margin: 64px auto 0; }
        .pricing-card { background: #fff; border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 38px; box-shadow: var(--shadow-soft); transition: border-color 0.3s, transform 0.3s, box-shadow 0.3s; }
        .pricing-card:hover { border-color: var(--border-mid); transform: translateY(-4px); box-shadow: var(--shadow-lift); }
        .pricing-card.featured { border-color: var(--border-deep); background: linear-gradient(160deg, #fefbff 0%, #f8f3fe 100%); position: relative; }
        .pricing-card.featured::before { content: 'Most Popular'; position: absolute; top: -13px; left: 50%; transform: translateX(-50%); background: var(--lilac-deep); color: #fff; font-size: 11px; font-weight: 500; padding: 4px 16px; border-radius: 100px; letter-spacing: 0.05em; white-space: nowrap; box-shadow: 0 4px 16px rgba(122, 91, 181, 0.3); }
        .pricing-plan { font-size: 11px; color: var(--ink-muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 14px; }
        .pricing-price { font-family: var(--serif); font-size: 50px; font-weight: 700; color: var(--ink); letter-spacing: -0.02em; line-height: 1; margin-bottom: 6px; }
        .pricing-price span { font-size: 18px; color: var(--ink-muted); font-family: var(--sans); font-style: normal; }
        .pricing-period { font-size: 13px; color: var(--ink-muted); font-weight: 300; margin-bottom: 28px; }
        .pricing-features { list-style: none; margin-bottom: 32px; }
        .pricing-features li { font-size: 14px; color: var(--ink-mid); padding: 8px 0; display: flex; gap: 10px; align-items: center; border-bottom: 1px solid var(--border); font-weight: 300; }
        .pricing-check { color: var(--lilac-deep); font-size: 12px; }
        .pricing-btn { display: block; text-align: center; padding: 14px; border-radius: 100px; font-size: 14px; font-weight: 500; text-decoration: none; transition: all 0.2s; border: none; }
        .pricing-btn-ghost { background: transparent; border: 1px solid var(--border-mid); color: var(--ink); }
        .pricing-btn-solid { background: var(--lilac-deep); color: #fff; box-shadow: 0 6px 24px rgba(122, 91, 181, 0.28); }

        .cta-section { padding: 130px 0 160px; text-align: center; }
        .cta-inner { background: linear-gradient(160deg, var(--lilac-pale) 0%, var(--blush) 60%, var(--cream-warm) 100%); border: 1px solid var(--border-mid); border-radius: var(--radius-xl); padding: 90px 64px; position: relative; overflow: hidden; box-shadow: var(--shadow-mid); }
        .cta-headline { font-family: var(--serif); font-size: clamp(38px, 5.5vw, 66px); letter-spacing: -0.02em; line-height: 1.08; margin-bottom: 22px; font-weight: 700; }
        .cta-headline em { font-style: normal; color: var(--lilac-deep); font-weight: 700; }
        .cta-sub { font-size: 18px; color: var(--ink-mid); max-width: 420px; margin: 0 auto 44px; font-weight: 300; line-height: 1.8; }
        .cta-note { font-size: 13px; color: var(--ink-muted); margin-top: 18px; }

        footer { border-top: 1px solid var(--border); padding: 44px 0; background: var(--cream); }
        .footer-inner { display: flex; align-items: center; justify-content: space-between; }
        .footer-logo { font-family: var(--serif); font-size: 18px; font-weight: 600; color: var(--ink-mid); }
        .footer-logo span { color: var(--lilac-deep); }
        .footer-links { display: flex; gap: 28px; }
        .footer-links a { font-size: 13px; color: var(--ink-muted); text-decoration: none; transition: color 0.2s; font-weight: 300; }
        .footer-copy { font-size: 12px; color: var(--ink-muted); font-weight: 300; }

        @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.75); } }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(22px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes floatLight { 0%, 100% { transform: translateY(0) rotateX(1.5deg); } 50% { transform: translateY(-12px) rotateX(0deg); } }

        .route-transition {
          position: fixed;
          inset: 0;
          z-index: 220;
          pointer-events: none;
          opacity: 0;
          background:
            radial-gradient(900px 420px at 20% 20%, rgba(122, 91, 181, 0.22), transparent 70%),
            radial-gradient(760px 360px at 80% 75%, rgba(80, 140, 100, 0.16), transparent 72%),
            rgba(245, 240, 252, 0.22);
          backdrop-filter: blur(0px);
          transition: opacity 220ms ease, backdrop-filter 220ms ease;
        }
        .route-transition.active {
          opacity: 1;
          backdrop-filter: blur(4px);
        }

        .reveal { opacity: 0; transform: translateY(26px); transition: opacity 0.75s ease, transform 0.75s ease; }
        .reveal.visible { opacity: 1; transform: translateY(0); }

        @media (max-width: 768px) {
          .landing-page { cursor: auto; }
          #cursor, #cursor-ring { display: none; }
          .nav-links { display: none; }
          .hero { padding: 150px 0 80px; }
          .problem-grid, .mode-panel.active, .testimonial-grid, .pricing-grid { grid-template-columns: 1fr; }
          .bento-grid { grid-template-columns: 1fr; }
          .bento-wide, .bento-narrow, .bento-mid { grid-column: span 1; }
          .proof-bar { gap: 24px; }
          .proof-divider { display: none; }
          .cta-inner { padding: 52px 28px; }
          .footer-inner { flex-direction: column; gap: 20px; text-align: center; }
        }
      ` }} />

      <div className={`route-transition ${isTransitioning ? "active" : ""}`} aria-hidden="true" />
      <main className="landing-page">
        <div id="cursor" />
        <div id="cursor-ring" />
        <div className="blob blob-1" id="blob1" />
        <div className="blob blob-2" id="blob2" />
        <div className="blob blob-3" id="blob3" />

        <nav id="nav">
          <div className="nav-inner">
            <Link href="/" className="nav-logo">Notion<span>Clip</span></Link>
            <div className="nav-links">
              <a href="#how">How it works</a>
              <a href="#modes">Modes</a>
              <a href="#pricing">Pricing</a>
              <Link href="/app" onClick={handleAppNavigation} className="nav-cta">Get Started →</Link>
            </div>
          </div>
        </nav>

        <section className="hero">
          <div className="container">
            <div className="hero-eyebrow">
              <div className="eyebrow-dot" />
              Intent-first content intelligence
            </div>
            <h1 className="hero-headline">
              Get the answer.<br />
              <span className="muted">Skip the</span> <em>rabbit hole.</em>
            </h1>
            <p className="hero-sub">
              Paste any YouTube video. Tell NotionClip why you&apos;re watching.
              Get structured notes built for your intent — pushed directly to Notion.
            </p>
            <div className="hero-actions">
              <Link href="/app" onClick={handleAppNavigation} className="btn-primary">Start for free</Link>
              <a href="#how" className="btn-ghost">See how it works <span className="arrow">→</span></a>
            </div>

            <div className="hero-visual" id="heroVisual">
              <div className="mockup-wrapper" id="mockupWrapper">
                <div className="notion-mockup">
                  <div className="notion-topbar">
                    <div className="traffic-lights">
                      <div className="tl tl-r" /><div className="tl tl-y" /><div className="tl tl-g" />
                    </div>
                    <div className="notion-url">notion.so / Study Notes / Single Slit Diffraction</div>
                  </div>
                  <div className="notion-body">
                    <span className="notion-emoji">📐</span>
                    <div className="notion-title">Single Slit Diffraction — Physics 301</div>
                    <div className="verdict-badge">✓ Watch — Core exam topic, 3 derivations you need</div>
                    <div className="notion-callout">
                      <span style={{ fontSize: "16px", flexShrink: 0, marginTop: "1px" }}>🧠</span>
                      <span>The intensity minimum occurs when path difference between edges equals one full wavelength. Narrower slit = wider angular spread — smaller <em>a</em>, larger separation.</span>
                    </div>
                    <div className="notion-h2">Formula Sheet</div>
                    <div className="notion-formula">a · sin θ = nλ → First minimum: θ = λ/a</div>
                    <div className="notion-formula">I(θ) = I₀ · [sin(α)/α]² where α = πa·sinθ/λ</div>
                    <div className="notion-h2">Self-Test Questions</div>
                    <div className="notion-toggle"><span style={{ color: "var(--ink-muted)", fontSize: "10px", marginTop: "3px" }}>▶</span><span>What happens to the central maximum if you halve the slit width?</span></div>
                    <div className="notion-toggle"><span style={{ color: "var(--ink-muted)", fontSize: "10px", marginTop: "3px" }}>▶</span><span>Derive the condition for secondary maxima using the phasor method.</span></div>
                  </div>
                </div>
                <div className="mockup-shadow" />
              </div>
            </div>
          </div>
        </section>

        <div className="container" id="how">
          <div className="proof-bar reveal">
            <div className="proof-stat"><span className="proof-number">45 min</span><span className="proof-label">video → 3 min notes</span></div>
            <div className="proof-divider" />
            <div className="proof-stat"><span className="proof-number">3</span><span className="proof-label">intent-based modes</span></div>
            <div className="proof-divider" />
            <div className="proof-stat"><span className="proof-number">Study · Work · Quick</span><span className="proof-label">different outputs, different you</span></div>
            <div className="proof-divider" />
            <div className="proof-stat"><span className="proof-number">1 click</span><span className="proof-label">straight to your Notion</span></div>
          </div>
        </div>

        <section className="problem">
          <div className="container">
            <div className="problem-grid">
              <div className="reveal">
                <div className="section-tag">The problem</div>
                <h2 className="section-headline">You don&apos;t have a content problem.<br />You have an <em>extraction</em> problem.</h2>
                <p className="section-sub">The answer exists — buried in a 45-minute video. Every tool gives you a generic summary. None of them ask <em>why</em> you&apos;re watching.</p>
              </div>
              <div className="problem-cards reveal">
                <div className="tilt-card" data-tilt><div className="problem-icon">🕳️</div><div><div className="problem-text-head">The rabbit hole trap</div><div className="problem-text-body">One video leads to six more. Two hours lost. Still no answer to the original question.</div></div></div>
                <div className="tilt-card" data-tilt><div className="problem-icon">💤</div><div><div className="problem-text-head">Passive watching = zero retention</div><div className="problem-text-body">Watching creates a false sense of learning. Without structured extraction, nothing sticks.</div></div></div>
                <div className="tilt-card" data-tilt><div className="problem-icon">⏱️</div><div><div className="problem-text-head">45 minutes to know if it&apos;s worth it</div><div className="problem-text-body">You can&apos;t judge a video until you&apos;ve watched it. NotionClip tells you before you start.</div></div></div>
                <div className="tilt-card" data-tilt><div className="problem-icon">📄</div><div><div className="problem-text-head">Generic summaries help no one</div><div className="problem-text-body">A student needs formulas. A developer needs tools. One output shape fits neither.</div></div></div>
              </div>
            </div>
          </div>
        </section>

        <section className="modes" id="modes">
          <div className="container">
            <div className="reveal">
              <div className="section-tag">Three modes</div>
              <h2 className="section-headline">Built for <em>why</em> you&apos;re watching,<br />not just what.</h2>
              <p className="section-sub" style={{ marginBottom: "52px" }}>Declare your intent before processing. The output changes completely.</p>
            </div>
            <div className="modes-tabs">
              <div className="mode-tab active" data-mode="study">📚 Study Mode</div>
              <div className="mode-tab" data-mode="work">💼 Work Mode</div>
              <div className="mode-tab" data-mode="quick">⚡ Quick Mode</div>
            </div>

            <div className="mode-panel active" id="panel-study">
              <div className="mode-content reveal">
                <h3>For lectures, tutorials, <em>and courses.</em></h3>
                <p>You need precision, not polish. NotionClip extracts exactly what you&apos;d need on exam day — formulas defined, common mistakes, self-test questions with hidden answers.</p>
                <div className="mode-features">
                  <div className="mode-feature"><div className="feature-check">✓</div> Formula sheet with variable definitions</div>
                  <div className="mode-feature"><div className="feature-check">✓</div> Self-test questions (toggle to reveal answers)</div>
                  <div className="mode-feature"><div className="feature-check">✓</div> Common mistakes the video warns against</div>
                  <div className="mode-feature"><div className="feature-check">✓</div> Prerequisites + further reading</div>
                  <div className="mode-feature"><div className="feature-check">✓</div> Core concept callout — the one thing to memorise</div>
                </div>
              </div>
              <div className="mode-output-card reveal" data-tilt-card>
                <div className="output-label">Study Mode output preview</div>
                <div className="output-row">
                  <div className="output-item"><div className="output-item-tag">Core concept</div>Destructive interference occurs when path difference between edges equals one full wavelength λ.</div>
                  <div className="output-formula">a · sinθ = nλ → θ_min = λ/a (first minimum)</div>
                  <div className="output-item"><div className="output-item-tag">Common mistake</div>Students confuse central maximum width with slit width — they are inversely related.</div>
                  <div className="output-item" style={{ borderColor: "var(--border-mid)", background: "var(--lilac-pale)" }}><div className="output-item-tag">Self-test</div>▶ What happens to fringe width if wavelength doubles?</div>
                </div>
              </div>
            </div>

            <div className="mode-panel" id="panel-work">
              <div className="mode-content">
                <h3>For tech talks, industry videos, <em>team content.</em></h3>
                <p>You need to know if a video is worth your team&apos;s time, what decisions it surfaces, and what to do next — before your next standup.</p>
                <div className="mode-features">
                  <div className="mode-feature"><div className="feature-check">✓</div> Watch / Skim / Skip verdict with reasoning</div>
                  <div className="mode-feature"><div className="feature-check">✓</div> One-liner summary — Slack-ready</div>
                  <div className="mode-feature"><div className="feature-check">✓</div> Tools and frameworks mentioned</div>
                  <div className="mode-feature"><div className="feature-check">✓</div> Decisions your team needs to make</div>
                  <div className="mode-feature"><div className="feature-check">✓</div> Specific next actions, not vague suggestions</div>
                </div>
              </div>
              <div className="mode-output-card" data-tilt-card>
                <div className="output-label">Work Mode output preview</div>
                <div className="output-row">
                  <div className="output-item" style={{ background: "#f0faf4", borderColor: "rgba(90,138,99,0.25)" }}><div className="output-item-tag" style={{ color: "var(--sage-deep)" }}>Verdict</div>WATCH — Contains architectural decision your team will face in Q3.</div>
                  <div className="output-item"><div className="output-item-tag">One-liner</div>Why microservices fail at &lt;50 engineers and when to switch back to a monolith.</div>
                  <div className="output-item"><div className="output-item-tag">Tools mentioned</div>Kubernetes, Render, Turso, tRPC, Hono</div>
                  <div className="output-item"><div className="output-item-tag">Decision to make</div>Should we split auth service now or wait until 10k DAU?</div>
                </div>
              </div>
            </div>

            <div className="mode-panel" id="panel-quick">
              <div className="mode-content">
                <h3>For news, docs, <em>and casual content.</em></h3>
                <p>60 seconds and zero patience. The gist in plain language — conversational, no jargon, genuinely interesting. Things worth mentioning at dinner tonight.</p>
                <div className="mode-features">
                  <div className="mode-feature"><div className="feature-check">✓</div> 2-sentence summary, nothing more</div>
                  <div className="mode-feature"><div className="feature-check">✓</div> 3-5 things worth knowing (actually interesting)</div>
                  <div className="mode-feature"><div className="feature-check">✓</div> Written like a human, not a Wikipedia bot</div>
                  <div className="mode-feature"><div className="feature-check">✓</div> 1-2 actions only if genuinely useful</div>
                </div>
              </div>
              <div className="mode-output-card" data-tilt-card>
                <div className="output-label">Quick Mode output preview</div>
                <div className="output-row">
                  <div className="output-item"><div className="output-item-tag">Summary</div>DeepMind&apos;s AlphaFold solved a 50-year protein folding problem. This is biology&apos;s moon landing, and it happened quietly in London.</div>
                  <div className="output-item"><div className="output-item-tag">Worth knowing</div>Proteins fold into shapes that determine everything they do in your body — scientists had no idea how to predict that shape until now.</div>
                  <div className="output-item"><div className="output-item-tag">Worth knowing</div>The model is open-source. Every drug company on Earth is using it right now.</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="features" id="features">
          <div className="container">
            <div className="reveal" style={{ textAlign: "center" }}>
              <div className="section-tag" style={{ display: "block" }}>Everything you need</div>
              <h2 className="section-headline">Built different, <em>by design.</em></h2>
            </div>
            <div className="bento-grid reveal">
              <div className="bento-cell bento-wide" data-bento><div className="bento-icon">🔗</div><div className="bento-title">Cross-source synthesis</div><div className="bento-desc">Paste two videos and a PDF. Get one unified answer. Themes, contradictions, knowledge gaps — across all sources at once. Nobody else does this.</div><span className="bento-tag">Differentiator</span></div>
              <div className="bento-cell bento-narrow" data-bento><div className="bento-icon">❓</div><div className="bento-title">Question-first</div><div className="bento-desc">Tell NotionClip what you want before processing. The AI focuses entirely around your question.</div></div>
              <div className="bento-cell bento-narrow" data-bento><div className="bento-icon">⌚</div><div className="bento-title">Smart watch verdict</div><div className="bento-desc">Watch / Skim / Skip with a reason and timestamps. Know before you commit the time.</div></div>
              <div className="bento-cell bento-mid" data-bento><div className="bento-icon">⏱️</div><div className="bento-title">Timestamp-linked notes</div><div className="bento-desc">Every key point links back to the exact moment in the video. Click to jump. No scrubbing through 40 minutes to find what you need.</div></div>
              <div className="bento-cell bento-narrow" data-bento><div className="bento-icon">📓</div><div className="bento-title">Direct Notion push</div><div className="bento-desc">One click. Structured page in your workspace — right blocks, right hierarchy.</div></div>
              <div className="bento-cell bento-narrow" data-bento><div className="bento-icon">📤</div><div className="bento-title">Export anywhere</div><div className="bento-desc">Markdown, JSON, plain text. Obsidian, Bear, your stack. Your notes, your format.</div></div>
            </div>
          </div>
        </section>

        <section className="testimonials">
          <div className="container">
            <div className="reveal" style={{ textAlign: "center" }}>
              <div className="section-tag" style={{ display: "block" }}>What people say</div>
              <h2 className="section-headline">Real students. Real teams.<br /><em>Real notes.</em></h2>
            </div>
            <div className="testimonial-grid reveal">
              <div className="testimonial-card" data-tilt><div className="stars"><span className="star">★</span><span className="star">★</span><span className="star">★</span><span className="star">★</span><span className="star">★</span></div><p className="testimonial-quote">&quot;Study Mode is the first AI tool that gave me what I actually needed for exams. Formulas, definitions, self-test questions. I used it on 20 lectures this semester.&quot;</p><div className="testimonial-author"><div className="author-avatar">AR</div><div><div className="author-name">Arjun R.</div><div className="author-role">Engineering student, IIT Delhi</div></div></div></div>
              <div className="testimonial-card" data-tilt><div className="stars"><span className="star">★</span><span className="star">★</span><span className="star">★</span><span className="star">★</span><span className="star">★</span></div><p className="testimonial-quote">&quot;The Watch/Skip verdict alone saves my team 3 hours a week. We stop debating which conference talks are worth watching. NotionClip just tells us.&quot;</p><div className="testimonial-author"><div className="author-avatar">SK</div><div><div className="author-name">Sneha K.</div><div className="author-role">Engineering lead, early-stage startup</div></div></div></div>
              <div className="testimonial-card" data-tilt><div className="stars"><span className="star">★</span><span className="star">★</span><span className="star">★</span><span className="star">★</span><span className="star">★</span></div><p className="testimonial-quote">&quot;Synthesised four ML papers and two videos around one question. It found a contradiction neither paper mentioned explicitly. That was genuinely new.&quot;</p><div className="testimonial-author"><div className="author-avatar">PV</div><div><div className="author-name">Priya V.</div><div className="author-role">ML researcher</div></div></div></div>
            </div>
          </div>
        </section>

        {/* <section className="pricing" id="pricing">
          <div className="container" style={{ textAlign: "center" }}>
            <div className="reveal">
              <div className="section-tag" style={{ display: "block" }}>Pricing</div>
              <h2 className="section-headline">Simple. <em>No surprises.</em></h2>
            </div>
            <div className="pricing-grid reveal">
              <div className="pricing-card">
                <div className="pricing-plan">Free</div>
                <div className="pricing-price">₹0<span>/mo</span></div>
                <div className="pricing-period">Always free. No card needed.</div>
                <ul className="pricing-features">
                  <li><span className="pricing-check">✓</span> 5 extractions per day</li>
                  <li><span className="pricing-check">✓</span> All 3 modes</li>
                  <li><span className="pricing-check">✓</span> Notion push</li>
                  <li><span className="pricing-check">✓</span> 7-day history</li>
                  <li style={{ opacity: 0.35 }}><span>–</span> Cross-source synthesis</li>
                  <li style={{ opacity: 0.35 }}><span>–</span> Question-first mode</li>
                </ul>
                <Link href="/app" onClick={handleAppNavigation} className="pricing-btn pricing-btn-ghost">Get started free</Link>
              </div>
              <div className="pricing-card featured">
                <div className="pricing-plan">Pro</div>
                <div className="pricing-price">₹199<span>/mo</span></div>
                <div className="pricing-period">Less than a textbook. More useful.</div>
                <ul className="pricing-features">
                  <li><span className="pricing-check">✓</span> Unlimited extractions</li>
                  <li><span className="pricing-check">✓</span> All 3 modes</li>
                  <li><span className="pricing-check">✓</span> Cross-source synthesis</li>
                  <li><span className="pricing-check">✓</span> Question-first extraction</li>
                  <li><span className="pricing-check">✓</span> Smart watch verdict</li>
                  <li><span className="pricing-check">✓</span> Full history + export</li>
                </ul>
                <Link href="/app" onClick={handleAppNavigation} className="pricing-btn pricing-btn-solid">Start Pro free for 7 days</Link>
              </div>
            </div>
          </div>
        </section> */}

        <section className="cta-section">
          <div className="container">
            <div className="cta-inner reveal">
              <h2 className="cta-headline">Stop watching.<br /><em>Start knowing.</em></h2>
              <p className="cta-sub">The next 45-minute video you would have half-watched becomes 3 minutes of exactly what you needed.</p>
              <Link href="/app" onClick={handleAppNavigation} className="btn-primary" style={{ display: "inline-block" }}>Try NotionClip free →</Link>
              <p className="cta-note">No credit card · Works with any Notion workspace</p>
            </div>
          </div>
        </section>

        <footer>
          <div className="container">
            <div className="footer-inner">
              <div className="footer-logo">Notion<span>Clip</span></div>
              <div className="footer-links">
                <a href="#">Privacy</a>
                <a href="#">GitHub</a>
              </div>
              <div className="footer-copy">© 2026 NotionClip</div>
            </div>
          </div>
        </footer>
      </main>
    </>
  )
}
