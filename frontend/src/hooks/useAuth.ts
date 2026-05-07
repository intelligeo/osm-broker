/**
 * useAuth — integrazione osm-auth (OAuth2 PKCE, singlepage mode).
 *
 * Flusso:
 *  1. signIn()  → osm-auth redirige a OSM /oauth2/authorize
 *  2. OSM torna all'app con ?code=...  (stessa URL, singlepage)
 *  3. useAuth rileva ?code= al mount → chiama auth.authenticate()
 *     → osm-auth scambia code→access_token internamente
 *  4. Passiamo l'access_token a POST /api/auth/exchange
 *  5. Backend restituisce session_token + profilo utente
 *  6. Salviamo session_token in localStorage; setUser(user)
 *
 * Se AUTH_ENABLED=false il hook è no-op (user = null, authEnabled = false).
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { osmAuth } from 'osm-auth'
import type { OsmUserPublic } from '../types'
import { exchangeOsmToken, apiLogout } from '../services/api'

const AUTH_ENABLED = import.meta.env.VITE_AUTH_ENABLED === 'true'
const CLIENT_ID    = import.meta.env.VITE_OSM_CLIENT_ID ?? ''

/** La redirect_uri deve corrispondere esattamente a quanto registrato su OSM. */
function getRedirectUri(): string {
  return window.location.origin + window.location.pathname
}

export interface UseAuthResult {
  user: OsmUserPublic | null
  isLoading: boolean
  isAuthenticated: boolean
  authEnabled: boolean
  signIn: () => void
  signOut: () => Promise<void>
}

export function useAuth(): UseAuthResult {
  const [user, setUser]         = useState<OsmUserPublic | null>(null)
  const [isLoading, setLoading] = useState(false)
  // Ref stabile all'istanza osm-auth (non deve causare re-render)
  const authRef = useRef<ReturnType<typeof osmAuth> | null>(null)

  // ── Inizializza istanza osm-auth ────────────────────────────────────────
  function getAuth() {
    if (!authRef.current && AUTH_ENABLED && CLIENT_ID) {
      authRef.current = new osmAuth({
        client_id:    CLIENT_ID,
        redirect_uri: getRedirectUri(),
        scope:        'read_prefs',
        singlepage:   true,
      })
    }
    return authRef.current
  }

  // ── Scambia token OSM con session JWT backend ───────────────────────────
  const exchangeWithBackend = useCallback(async (auth: ReturnType<typeof osmAuth>) => {
    const osmToken = auth.getAccessToken()
    if (!osmToken) return
    try {
      setLoading(true)
      const { session_token, user: profile } = await exchangeOsmToken(osmToken)
      localStorage.setItem('osm_broker_token', session_token)
      setUser(profile)
    } catch (err) {
      console.error('[useAuth] exchange failed', err)
      auth.logout()
      localStorage.removeItem('osm_broker_token')
    } finally {
      setLoading(false)
    }
  }, [])

  // ── Al mount: ripristina sessione o completa callback OAuth ────────────
  useEffect(() => {
    if (!AUTH_ENABLED || !CLIENT_ID) return
    const auth = getAuth()!

    const params = new URLSearchParams(window.location.search)
    const hasCode = params.has('code')

    if (hasCode) {
      // Siamo nella redirect URI dopo che OSM ha inviato il code
      setLoading(true)
      auth.authenticate((err: Error | null) => {
        if (err) {
          console.error('[useAuth] authenticate error', err)
          setLoading(false)
          return
        }
        // Pulisce ?code= dall'URL senza reload
        const clean = window.location.pathname
        window.history.replaceState({}, '', clean)
        exchangeWithBackend(auth)
      })
    } else if (auth.authenticated()) {
      // Sessione osm-auth ancora attiva in localStorage; verifica session JWT
      const saved = localStorage.getItem('osm_broker_token')
      if (saved) {
        // Ricarica profilo già salvato (minimizza chiamate API)
        // Il JWT contiene il payload — decodifica lato client solo per display
        try {
          const payload = JSON.parse(atob(saved.split('.')[1]))
          setUser({ osm_id: Number(payload.sub), display_name: payload.name, account_created: '' })
        } catch {
          // token malformato → logout
          auth.logout()
          localStorage.removeItem('osm_broker_token')
        }
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ── signIn ────────────────────────────────────────────────────────────
  const signIn = useCallback(() => {
    if (!AUTH_ENABLED || !CLIENT_ID) {
      console.warn('[useAuth] AUTH_ENABLED o VITE_OSM_CLIENT_ID non configurati.')
      return
    }
    const auth = getAuth()!
    auth.authenticate((err: Error | null) => {
      if (err) { console.error('[useAuth] signIn error', err); return }
      exchangeWithBackend(auth)
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [exchangeWithBackend])

  // ── signOut ───────────────────────────────────────────────────────────
  const signOut = useCallback(async () => {
    const auth = getAuth()
    const token = localStorage.getItem('osm_broker_token')
    if (token) {
      try { await apiLogout(token) } catch { /* ignora errori di rete */ }
    }
    auth?.logout()
    localStorage.removeItem('osm_broker_token')
    setUser(null)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    authEnabled: AUTH_ENABLED && !!CLIENT_ID,
    signIn,
    signOut,
  }
}
