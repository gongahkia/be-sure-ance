import * as Sentry from '@sentry/vue'

const SENSITIVE_KEYS = new Set([
  'authorization',
  'apikey',
  'cookie',
  'set-cookie',
  'x-supabase-key',
  'supabase_secret_key',
  'supabase_service_role_key',
  'telegram_bot_token',
  'sentry_dsn',
])
const SECRET_PATTERNS = [
  /sb_secret_[A-Za-z0-9_-]+/g,
  /Bearer\s+[A-Za-z0-9._-]+/gi,
  /eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g,
]

export function initializeObservability(app) {
  const dsn = import.meta.env.VITE_SENTRY_DSN
  if (!dsn) {
    return false
  }

  Sentry.init({
    app,
    dsn,
    environment: import.meta.env.VITE_SENTRY_ENVIRONMENT || import.meta.env.MODE,
    release: import.meta.env.VITE_SENTRY_RELEASE,
    tracesSampleRate: sampleRate(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE),
    sendDefaultPii: false,
    beforeSend: sanitizeEvent,
  })
  Sentry.setTag('surface', 'frontend')
  return true
}

export function captureFrontendError(error, context = {}) {
  Sentry.withScope((scope) => {
    scope.setTag('surface', 'frontend')
    scope.setContext('frontend', scrub(context))
    Sentry.captureException(error)
  })
}

export function sanitizeEvent(event) {
  return scrub(structuredCloneSafe(event))
}

function structuredCloneSafe(value) {
  try {
    return structuredClone(value)
  } catch {
    try {
      return JSON.parse(JSON.stringify(value || {}))
    } catch {
      return {}
    }
  }
}

function sampleRate(value) {
  const parsed = Number(value || 0)
  return Number.isFinite(parsed) ? parsed : 0
}

function scrub(value) {
  if (Array.isArray(value)) {
    return value.map((item) => scrub(item))
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).map(([key, child]) => [
        key,
        SENSITIVE_KEYS.has(key.toLowerCase()) ? '[redacted]' : scrub(child),
      ]),
    )
  }
  if (typeof value === 'string') {
    return SECRET_PATTERNS.reduce((text, pattern) => text.replace(pattern, '[redacted]'), value)
  }
  return value
}
