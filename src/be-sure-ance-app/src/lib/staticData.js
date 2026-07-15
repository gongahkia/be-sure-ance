export const APP_DATA_PATH = import.meta.env.VITE_STATIC_DATA_PATH || '/data/app-data.json'
export const LIVE_SCRAPE_MODE = import.meta.env.VITE_LIVE_SCRAPE_MODE === 'true'
export const LIVE_TABLES_PATH = import.meta.env.VITE_LIVE_TABLES_PATH || '/data/tables'

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
  if (LIVE_SCRAPE_MODE) {
    return loadLiveTables(fetcher)
  }

  const response = await fetcher(APP_DATA_PATH, {
    headers: { Accept: 'application/json' },
    cache: 'no-cache',
  })
  if (!response.ok) {
    throw new Error(`Static data load failed with ${response.status}`)
  }
  return normalizeAppData(await response.json())
}

async function loadLiveTables(fetcher) {
  const tables = await Promise.all(
    APP_TABLES.map(async (table) => {
      try {
        const response = await fetcher(`${LIVE_TABLES_PATH}/${table}.json`, {
          headers: { Accept: 'application/json' },
          cache: 'no-cache',
        })
        if (!response.ok) {
          return [table, []]
        }
        return [table, normalizeRows(await response.json())]
      } catch {
        return [table, []]
      }
    }),
  )
  return Object.fromEntries(tables)
}

export function normalizeAppData(payload) {
  const source = payload?.tables || payload || {}
  return Object.fromEntries(APP_TABLES.map((table) => [table, normalizeRows(source[table])]))
}

function normalizeRows(rows) {
  return Array.isArray(rows) ? rows.filter((row) => row && typeof row === 'object') : []
}
