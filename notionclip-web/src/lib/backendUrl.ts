function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "")
}

const configuredBase =
  process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL || process.env.API_BASE_URL

const rawApiBase = (configuredBase || "").trim()

if (!rawApiBase) {
  throw new Error("Missing API base URL. Set NEXT_PUBLIC_API_URL or NEXT_PUBLIC_BACKEND_URL (for local use .env.local).")
}

export const API_BASE = trimTrailingSlash(rawApiBase)

export function backendUrl(path: string): string {
  if (!path) return API_BASE
  if (/^https?:\/\//i.test(path)) return path
  const normalized = path.startsWith("/") ? path : `/${path}`
  return `${API_BASE}${normalized}`
}
