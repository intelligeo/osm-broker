import axios from 'axios'
import type { ExportRequest, Job, ExchangeResponse, OsmUserPublic } from '../types'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
  timeout: 30_000,
})

// ── Intercept per auth header ──────────────────────────────────────────────
// Inietta il session JWT interno (emesso da /api/auth/exchange) se presente.
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('osm_broker_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ── Export API ───────────────────────────────────────────────────────────────

/** Sottomette un nuovo job di export. Ritorna il job con id e status=pending. */
export async function submitExport(payload: ExportRequest): Promise<Job> {
  const { data } = await http.post<Job>('/jobs', payload)
  return data
}

/** Interroga lo stato di un job. */
export async function getJob(jobId: string): Promise<Job> {
  const { data } = await http.get<Job>(`/jobs/${jobId}`)
  return data
}

/** URL diretto per il download ZIP. */
export function downloadUrl(jobId: string): string {
  const base = import.meta.env.VITE_API_URL ?? '/api'
  return `${base}/jobs/${jobId}/download`
}

// ── Auth API ─────────────────────────────────────────────────────────────────

/**
 * Invia l'access_token OSM (ottenuto da osm-auth) al backend.
 * Il backend lo verifica con OSM, crea la sessione e ritorna session_token + user.
 */
export async function exchangeOsmToken(osmAccessToken: string): Promise<ExchangeResponse> {
  const { data } = await http.post<ExchangeResponse>('/auth/exchange', {
    access_token: osmAccessToken,
  })
  return data
}

/** Recupera il profilo dell'utente corrente dal session_token. */
export async function getMe(sessionToken: string): Promise<OsmUserPublic> {
  const { data } = await http.post<OsmUserPublic>('/auth/me', {
    session_token: sessionToken,
  })
  return data
}

/** Invalida la sessione backend (revoca Redis). */
export async function apiLogout(sessionToken: string): Promise<void> {
  await http.post('/auth/logout', { session_token: sessionToken })
}
