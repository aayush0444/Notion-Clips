const PROD_API_BASE = "https://notion-clips-production.up.railway.app"
const DEV_API_BASE = "http://127.0.0.1:8000"

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "")
}

const configuredBase =
  process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL

const fallbackBase =
  process.env.NODE_ENV === "development" ? DEV_API_BASE : PROD_API_BASE

const rawApiBase = (configuredBase || fallbackBase).trim()

export const API_BASE = trimTrailingSlash(rawApiBase)

export function backendUrl(path: string): string {
  if (!path) return API_BASE
  if (/^https?:\/\//i.test(path)) return path
  const normalized = path.startsWith("/") ? path : `/${path}`
  return `${API_BASE}${normalized}`
}
