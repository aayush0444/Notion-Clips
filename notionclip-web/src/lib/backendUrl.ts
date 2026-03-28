const DEFAULT_API_BASE = "https://notion-clips-production.up.railway.app"

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "")
}

const rawApiBase = (
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  DEFAULT_API_BASE
).trim()

export const API_BASE = trimTrailingSlash(rawApiBase)

export function backendUrl(path: string): string {
  if (!path) return API_BASE
  if (/^https?:\/\//i.test(path)) return path
  const normalized = path.startsWith("/") ? path : `/${path}`
  return `${API_BASE}${normalized}`
}
