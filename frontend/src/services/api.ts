import axios from 'axios'
import type { ExportRequest, Job } from '../types'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
  timeout: 30_000,
})

// ── Intercept per future auth headers ──────────────────────────────────────
// Quando AUTH_ENABLED=true il backend emetterà un JWT da passare qui.
// Per ora è un no-op pronto per OAuth2.
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('osm_broker_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ── API calls ───────────────────────────────────────────────────────────────

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
