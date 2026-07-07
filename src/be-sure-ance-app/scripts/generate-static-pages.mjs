import { mkdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const appRoot = path.resolve(__dirname, '..')
const distDir = resolvePath(process.env.STATIC_PLAN_DIST_DIR, path.join(appRoot, 'dist'))
const siteOrigin = normalizeOrigin(process.env.VITE_SITE_ORIGIN || process.env.URL)
const indexPath = path.join(distDir, 'index.html')
const keyRoutes = ['/', '/matrix/panel-hospitals', '/status']

const providerNames = {
  aia: 'AIA Singapore',
  china_life: 'China Life Singapore',
  chubb: 'Chubb Insurance (Singapore)',
  great_eastern: 'Great Eastern Singapore',
  hsbc: 'HSBC Singapore Insurance',
  iii: 'India International Insurance (Singapore)',
  singlife: 'Singlife',
  sunlife: 'Sun Life',
  tokio_marine: 'Tokio Marine Insurance Group',
  uoi: 'United Overseas Insurance Limited (UOI)',
}

async function main() {
  const template = await readFile(indexPath, 'utf8')
  const { plans, planFacts } = await loadStaticData()
  const normalizedPlans = normalizePlans(plans)
  const factsByPlan = groupFactsByPlan(planFacts)
  const planUrls = []

  for (const plan of normalizedPlans) {
    const facts = factsByPlan.get(planKey(plan.insurer, plan.plan_slug)) || []
    const routePath = planRoutePath(plan)
    const canonicalUrl = absoluteUrl(routePath)
    const pageHtml = renderPlanPage(template, plan, facts, canonicalUrl)
    const outputPath = path.join(distDir, ...routePath.split('/').filter(Boolean), 'index.html')

    await mkdir(path.dirname(outputPath), { recursive: true })
    await writeFile(outputPath, pageHtml)
    planUrls.push(canonicalUrl)
  }

  await writeFile(
    path.join(distDir, 'sitemap.xml'),
    renderSitemap([...keyRoutes.map(absoluteUrl), ...planUrls]),
  )
  await writeFile(path.join(distDir, 'robots.txt'), `Sitemap: ${absoluteUrl('/sitemap.xml')}\n`)
  console.log(`static_pages: ${normalizedPlans.length}`)
}

async function loadStaticData() {
  const candidatePaths = [
    process.env.STATIC_PLAN_EXPORT_PATH
      ? resolvePath(process.env.STATIC_PLAN_EXPORT_PATH, process.cwd())
      : '',
    path.join(distDir, 'data', 'app-data.json'),
    path.join(appRoot, 'public', 'data', 'app-data.json'),
  ].filter(Boolean)

  for (const payloadPath of candidatePaths) {
    try {
      const payload = JSON.parse(await readFile(payloadPath, 'utf8'))
      const source = payload.tables || payload
      return {
        plans: source.plans || [],
        planFacts: source.plan_facts || source.planFacts || [],
      }
    } catch (error) {
      if (process.env.STATIC_PLAN_EXPORT_PATH) {
        throw error
      }
    }
  }

  console.log('static_pages: skipped_missing_static_data')
  return { plans: [], planFacts: [] }
}

function normalizePlans(plans) {
  return (plans || [])
    .map((plan) => ({
      ...plan,
      insurer: cleanText(plan?.insurer),
      plan_name: cleanText(plan?.plan_name),
      plan_slug: cleanText(plan?.plan_slug) || slugify(plan?.plan_name),
      providerName: providerNames[cleanText(plan?.insurer)] || cleanText(plan?.insurer),
    }))
    .filter((plan) => plan.insurer && plan.plan_name && plan.plan_slug)
    .sort((a, b) => planRoutePath(a).localeCompare(planRoutePath(b)))
}

function groupFactsByPlan(planFacts) {
  const groupedFacts = new Map()

  for (const fact of planFacts || []) {
    if (!fact?.insurer || !fact?.plan_slug || !fact?.field_name) {
      continue
    }
    const key = planKey(fact.insurer, fact.plan_slug)
    if (!groupedFacts.has(key)) {
      groupedFacts.set(key, [])
    }
    groupedFacts.get(key).push(fact)
  }

  return groupedFacts
}

function renderPlanPage(template, plan, facts, canonicalUrl) {
  const title = `${plan.plan_name} | ${plan.providerName} | Be-sure-ance`
  const description = metaDescription(plan)
  const sourceFacts = facts.filter((fact) => safeHttpUrl(fact.source_url))
  const jsonLd = financialProductJsonLd(plan, facts, canonicalUrl, description)
  const staticMarkup = renderStaticPlanMarkup(plan, sourceFacts)
  const headMarkup = [
    `<title>${escapeHtml(title)}</title>`,
    `<meta name="description" content="${escapeHtml(description)}" />`,
    `<link rel="canonical" href="${escapeHtml(canonicalUrl)}" />`,
    `<script type="application/ld+json">${jsonForScript(jsonLd)}</script>`,
  ].join('\n    ')

  return template
    .replace(/<title>.*?<\/title>/, headMarkup)
    .replace('<div id="app"></div>', `<div id="app">${staticMarkup}</div>`)
}

function renderStaticPlanMarkup(plan, facts) {
  const sourceRows =
    facts.length > 0
      ? facts.map(renderFactArticle).join('\n')
      : '<p class="static-muted">No source-traceable facts have been published for this plan page yet.</p>'
  const planUrl = safeHttpUrl(plan.plan_url)
  const brochureUrl = safeHttpUrl(plan.product_brochure_url)

  return `
    <main class="static-plan-page">
      <header class="static-topbar">
        <a href="/" class="static-brand"><span>B</span> Be-sure-ance</a>
        <nav>
          <a href="/">Models</a>
          <a href="/matrix/panel-hospitals">Datasets</a>
          <a href="/status">Status</a>
        </nav>
      </header>
      <section class="static-repo-heading">
        <div>
          <p>${escapeHtml(plan.providerName)}</p>
          <h1>${escapeHtml(plan.plan_name)}</h1>
          <p>${escapeHtml(plan.plan_description || plan.plan_overview || 'Source-traceable qualitative plan metadata.')}</p>
          <p class="static-disclaimer">Research only. Not financial advice, insurance advice, a quote, ranking, or recommendation.</p>
        </div>
        <nav>
          ${planUrl ? `<a href="${escapeHtml(planUrl)}">Carrier product page</a>` : ''}
          ${brochureUrl ? `<a href="${escapeHtml(brochureUrl)}">Brochure</a>` : ''}
        </nav>
      </section>
      <nav class="static-tabs">
        <a href="/">Model card</a>
        <a href="/">Facts</a>
        <a href="/">Files and versions</a>
      </nav>
      <section class="static-facts">
        <h2>Source-traceable facts</h2>
        ${sourceRows}
      </section>
    </main>`
}

function renderFactArticle(fact) {
  const sourceUrl = safeHttpUrl(fact.source_url)
  return `
    <article class="static-fact-card">
      <h3>${escapeHtml(fieldLabel(fact.field_name))}</h3>
      <p>${escapeHtml(summarizeFieldValue(fact.field_value))}</p>
      <p>
        Source:
        <a href="${escapeHtml(sourceUrl)}">${escapeHtml(hostname(sourceUrl))}</a>
        <span>${escapeHtml(fact.source_type || 'source')}</span>
        <span>${escapeHtml(dateLabel(fact.last_verified_at || fact.scraped_at))}</span>
      </p>
    </article>`
}

function financialProductJsonLd(plan, facts, canonicalUrl, description) {
  const carrierUrl = safeHttpUrl(plan.plan_url)
  const brochureUrl = safeHttpUrl(plan.product_brochure_url)
  const sourceUrls = unique([
    ...facts.map((fact) => safeHttpUrl(fact.source_url)).filter(Boolean),
    brochureUrl,
    carrierUrl,
  ]).filter(Boolean)
  return cleanObject({
    '@context': 'https://schema.org',
    '@type': 'FinancialProduct',
    name: plan.plan_name,
    description,
    url: canonicalUrl,
    mainEntityOfPage: canonicalUrl,
    category: 'Insurance plan qualitative metadata',
    serviceType: 'Insurance plan',
    areaServed: 'Singapore',
    brand: organization(plan.providerName),
    provider: organization(plan.providerName),
    sameAs: carrierUrl,
    subjectOf: sourceUrls.slice(0, 8).map((sourceUrl) => ({
      '@type': 'CreativeWork',
      url: sourceUrl,
    })),
  })
}

function organization(name) {
  return name ? { '@type': 'Organization', name } : null
}

function renderSitemap(urls) {
  const items = unique(urls)
    .map((url) => `  <url><loc>${escapeXml(url)}</loc></url>`)
    .join('\n')
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${items}\n</urlset>\n`
}

function planKey(insurer, planSlug) {
  return `${insurer}::${planSlug}`
}

function planRoutePath(plan) {
  return `/plan/${encodeURIComponent(plan.insurer)}/${encodeURIComponent(plan.plan_slug)}`
}

function absoluteUrl(routePath) {
  return `${siteOrigin}${routePath}`
}

function normalizeOrigin(value) {
  const fallback = 'https://example.com'
  const rawValue = cleanText(value) || fallback
  try {
    const url = new URL(rawValue)
    return url.origin
  } catch {
    return fallback
  }
}

function resolvePath(value, fallback) {
  if (!value) {
    return fallback
  }
  return path.isAbsolute(value) ? value : path.resolve(process.cwd(), value)
}

function safeHttpUrl(value) {
  if (!value) {
    return ''
  }
  try {
    const url = new URL(value)
    return ['http:', 'https:'].includes(url.protocol) ? url.toString() : ''
  } catch {
    return ''
  }
}

function cleanText(value) {
  return String(value || '')
    .replace(/\s+/g, ' ')
    .trim()
}

function slugify(value) {
  return cleanText(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

function metaDescription(plan) {
  const base = cleanText(plan.plan_description || plan.plan_overview)
  if (base) {
    return base.slice(0, 155)
  }
  return `Source-traceable qualitative metadata for ${plan.providerName} ${plan.plan_name}.`
}

function summarizeFieldValue(fieldValue) {
  if (!fieldValue || typeof fieldValue !== 'object') {
    return 'Unknown'
  }
  if (fieldValue.status && fieldValue.status !== 'known') {
    return fieldLabel(fieldValue.status)
  }
  if (Array.isArray(fieldValue.items) && fieldValue.items.length > 0) {
    return fieldValue.items.map(itemLabel).filter(Boolean).join(', ')
  }
  if (fieldValue.value !== undefined && fieldValue.value !== null) {
    return summarizeValue(fieldValue.value)
  }
  return 'Known'
}

function summarizeValue(value) {
  if (['string', 'number', 'boolean'].includes(typeof value)) {
    return cleanText(value)
  }
  if (Array.isArray(value)) {
    return value.map(itemLabel).filter(Boolean).join(', ')
  }
  if (value && typeof value === 'object') {
    if (value.duration_days !== undefined && value.basis) {
      return `${value.duration_days} days (${value.basis})`
    }
    if (value.duration_days !== undefined) {
      return `${value.duration_days} days`
    }
    if (value.sha256) {
      return `Brochure captured: ${String(value.sha256).slice(0, 12)}`
    }
    return Object.entries(value)
      .filter(([, entryValue]) => ['string', 'number', 'boolean'].includes(typeof entryValue))
      .slice(0, 4)
      .map(([key, entryValue]) => `${fieldLabel(key)}: ${entryValue}`)
      .join(', ')
  }
  return 'Known'
}

function itemLabel(item) {
  if (['string', 'number', 'boolean'].includes(typeof item)) {
    return cleanText(item)
  }
  return cleanText(
    item?.normalized_name ||
      item?.name ||
      item?.label ||
      item?.condition ||
      item?.event ||
      item?.basis ||
      item?.source_label ||
      item?.details ||
      item?.raw_text,
  )
}

function fieldLabel(value) {
  return cleanText(value)
    .split(/[_-]+/)
    .filter(Boolean)
    .map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`)
    .join(' ')
}

function dateLabel(value) {
  if (!value) {
    return 'Verification date unavailable'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return 'Verification date unavailable'
  }
  return `Verified ${date.toISOString().slice(0, 10)}`
}

function hostname(value) {
  try {
    return new URL(value).hostname.replace(/^www\./, '')
  } catch {
    return value
  }
}

function unique(values) {
  return Array.from(new Set(values))
}

function cleanObject(value) {
  return Object.fromEntries(
    Object.entries(value).filter(([, entryValue]) => {
      if (Array.isArray(entryValue)) {
        return entryValue.length > 0
      }
      return entryValue !== null && entryValue !== undefined && entryValue !== ''
    }),
  )
}

function escapeHtml(value) {
  return cleanText(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function escapeXml(value) {
  return escapeHtml(value)
}

function jsonForScript(value) {
  return JSON.stringify(value)
    .replaceAll('<', '\\u003c')
    .replaceAll('>', '\\u003e')
    .replaceAll('&', '\\u0026')
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
