"use client"

import { useMemo, useState } from "react"

type TimestampMoment = {
  label: string
  seconds: number
  title: string
  note: string
}

function parseTimestampToSeconds(value: string): number | null {
  const parts = value.split(":").map((part) => Number(part))
  if (parts.some((part) => Number.isNaN(part))) return null

  if (parts.length === 2) {
    const [minutes, seconds] = parts
    return minutes * 60 + seconds
  }

  if (parts.length === 3) {
    const [hours, minutes, seconds] = parts
    return hours * 3600 + minutes * 60 + seconds
  }

  return null
}

function secondsToLabel(totalSeconds: number): string {
  const safe = Math.max(0, Math.floor(totalSeconds))
  const hours = Math.floor(safe / 3600)
  const minutes = Math.floor((safe % 3600) / 60)
  const seconds = safe % 60

  if (hours > 0) {
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`
  }
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`
}

function normalizeText(value: string): string {
  return value.replace(/\s+/g, " ").trim()
}

function buildMomentTitle(value: string, fallbackLabel?: string): string {
  const cleaned = normalizeText(value).replace(/^[\-:,.\s]+/, "")
  if (!cleaned) return fallbackLabel ? `Moment at ${fallbackLabel}` : "Important concept marker"

  const words = cleaned.split(" ")
  const clipped = words.slice(0, 10).join(" ")
  return words.length > 10 ? `${clipped}...` : clipped
}

function extractLeadingSentence(value: string): string {
  const cleaned = normalizeText(value)
  if (!cleaned) return ""

  const sentences = cleaned.split(/(?<=[.!?])\s+/)
  return sentences[0] || cleaned
}

function isYoutubeUrl(url: string | undefined): boolean {
  if (!url) return false
  return /youtu\.be|youtube\.com/i.test(url)
}

function buildTimestampUrl(url: string, seconds: number): string {
  try {
    const parsed = new URL(url)
    parsed.searchParams.set("t", String(seconds))
    return parsed.toString()
  } catch {
    const separator = url.includes("?") ? "&" : "?"
    return `${url}${separator}t=${seconds}`
  }
}

function collectMomentsFromObject(data: unknown, limit: number): TimestampMoment[] {
  const stack: unknown[] = [data]
  const moments: TimestampMoment[] = []
  const seen = new Set<string>()
  const timestampRegex = /(\b\d{1,2}:\d{2}(?::\d{2})?\b)/g

  while (stack.length > 0 && moments.length < limit) {
    const node = stack.pop()
    if (!node) continue

    if (Array.isArray(node)) {
      for (const item of node) stack.push(item)
      continue
    }

    if (typeof node === "object") {
      const record = node as Record<string, unknown>
      const display = typeof record.timestamp_display === "string" ? record.timestamp_display : null
      const rawTimestamp =
        typeof record.timestamp === "string"
          ? record.timestamp
          : typeof record.time === "string"
          ? record.time
          : null
      const rawSeconds =
        typeof record.timestamp_seconds === "number"
          ? record.timestamp_seconds
          : typeof record.seconds === "number"
          ? record.seconds
          : null
      const explicitTitle =
        typeof record.title === "string"
          ? record.title
          : typeof record.topic === "string"
          ? record.topic
          : typeof record.concept === "string"
          ? record.concept
          : typeof record.key_point === "string"
          ? record.key_point
          : typeof record.point === "string"
          ? record.point
          : typeof record.fact === "string"
          ? record.fact
          : null
      const note =
        typeof record.quote === "string"
          ? record.quote
          : typeof record.description === "string"
          ? record.description
          : typeof record.relevance === "string"
          ? record.relevance
          : typeof record.note === "string"
          ? record.note
          : null

      const derivedSeconds = rawSeconds ?? (rawTimestamp ? parseTimestampToSeconds(rawTimestamp) : null)
      if (derivedSeconds !== null) {
        const label = display || rawTimestamp || secondsToLabel(derivedSeconds)
        const fallbackNote = `Key moment at ${label}`
        const resolvedNote = extractLeadingSentence(note || "") || fallbackNote
        const title = buildMomentTitle(explicitTitle || resolvedNote, label)
        const key = `${derivedSeconds}-${title}`
        if (!seen.has(key)) {
          seen.add(key)
          moments.push({ label, seconds: derivedSeconds, title, note: resolvedNote })
          if (moments.length >= limit) break
        }
      }

      for (const value of Object.values(record)) stack.push(value)
      continue
    }

    if (typeof node === "string") {
      timestampRegex.lastIndex = 0
      let match: RegExpExecArray | null
      while ((match = timestampRegex.exec(node)) !== null) {
        const label = match[1]
        const seconds = parseTimestampToSeconds(label)
        if (seconds === null) continue
        const cleaned = extractLeadingSentence(node.replace(label, "").replace(/^[\s\-:.,]+/, ""))
        const fallbackNote = `Key moment at ${label}`
        const note = cleaned.length > 0 ? cleaned : fallbackNote
        const title = buildMomentTitle(note, label)
        const key = `${seconds}-${title}`
        if (!seen.has(key)) {
          seen.add(key)
          moments.push({ label, seconds, title, note })
          if (moments.length >= limit) break
        }
      }
    }
  }

  return moments.sort((a, b) => a.seconds - b.seconds)
}

export function TimestampMomentsPanel({
  data,
  sourceUrl,
}: {
  data: unknown
  sourceUrl?: string
}) {
  const isYoutube = isYoutubeUrl(sourceUrl)
  const moments = useMemo(() => collectMomentsFromObject(data, 8), [data])
  const [isOpen, setIsOpen] = useState(true)

  if (!isYoutube && moments.length === 0) return null

  return (
    <section className="rounded-xl border border-[#DCCFF3] bg-[#F8F5FE] p-5 sm:p-6">
      <div className="rounded-lg border border-[#E4D9F5] bg-white/90">
        <div className="flex items-center justify-between border-b border-[#EDE3FA] px-3 py-2.5 sm:px-4">
          <div className="text-xs font-semibold uppercase tracking-[0.12em] text-[#6B55A4]">
            Important Timestamps
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          className="flex w-full items-center justify-between px-4 py-3 text-left"
        >
          <div>
            <div className="text-xs text-[#7A6A98]">
              {moments.length > 0
                ? `${moments.length} detected moments with context labels`
                : "No auto-detected moments yet"}
            </div>
          </div>
          <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[#6B55A4]">
            {isOpen ? "Hide" : "Show"}
          </span>
        </button>

        {isOpen && (
          <div className="border-t border-[#EDE3FA] px-3 py-3 sm:px-4">
            {moments.length > 0 ? (
              <div className="space-y-2.5">
                {moments.map((moment, idx) => (
                  <div
                    key={`${moment.seconds}-${idx}`}
                    className="flex flex-wrap items-start gap-3 rounded-lg border border-[#E9DFF8] bg-white px-3 py-3"
                  >
                    {isYoutube && sourceUrl ? (
                      <a
                        href={buildTimestampUrl(sourceUrl, moment.seconds)}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center rounded-md border border-[#D2C2EC] bg-[#F8F4FF] px-2.5 py-1 text-sm font-medium text-[#5A3E8B] transition-colors hover:bg-[#EFE6FF]"
                      >
                        {moment.label}
                      </a>
                    ) : (
                      <span className="inline-flex items-center rounded-md border border-[#D2C2EC] bg-[#F8F4FF] px-2.5 py-1 text-sm font-medium text-[#5A3E8B]">
                        {moment.label}
                      </span>
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="text-base font-semibold leading-relaxed text-[#403255]">{moment.title}</p>
                      <p className="mt-1 text-sm leading-relaxed text-[#5C4C79]">{moment.note}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-lg border border-dashed border-[#D8C9EE] bg-white/80 px-4 py-3 text-sm text-[#6A5A88]">
                No timestamp markers were detected in this output yet. Add a question before processing to get more precise moments.
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  )
}