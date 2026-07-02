export const APP_DATA_PATH = import.meta.env.VITE_STATIC_DATA_PATH || '/data/app-data.json'

export const APP_TABLES = [
  'plans',
  'plan_comparison_facts',
  'plan_facts',
  'specialist_resources',
  'claim_turnaround_metrics',
  'mas_regulatory_events',
  'brochure_change_alerts',
  'carrier_canonical_names',
  'scraper_health',
]

export async function loadAppData(fetcher = fetch) {
  const response = await fetcher(APP_DATA_PATH, {
    headers: { Accept: 'application/json' },
    cache: 'no-cache',
  })
  if (!response.ok) {
    throw new Error(`Static data load failed with ${response.status}`)
  }
  return normalizeAppData(await response.json())
}

export function normalizeAppData(payload) {
  const source = payload?.tables || payload || {}
  return Object.fromEntries(APP_TABLES.map((table) => [table, normalizeRows(source[table])]))
}

function normalizeRows(rows) {
  return Array.isArray(rows) ? rows.filter((row) => row && typeof row === 'object') : []
}
