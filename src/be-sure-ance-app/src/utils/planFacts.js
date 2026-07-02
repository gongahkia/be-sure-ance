const STALE_AFTER_DAYS = 30

const FIELD_LABELS = {
  coverage_tags: 'Coverage',
  panel_hospitals: 'Network',
  waiting_periods: 'Waiting periods',
  claim_deadlines: 'Claim deadlines',
  claim_sla: 'Claim SLA',
  exclusions: 'Exclusions',
  brochure_metadata: 'Brochure',
  source_notes: 'Source notes',
  plan_profile: 'Plan profile',
}

const SOURCE_TYPE_LABELS = {
  brochure_pdf: 'Brochure PDF',
  product_page: 'Product page',
  manual_entry: 'Manual entry',
}

export function knownFieldValue(facts, fieldName) {
  const fieldValue = facts?.[fieldName]?.field_value
  return fieldValue?.status === 'known' ? fieldValue : null
}

export function factItems(facts, fieldName) {
  const fieldValue = knownFieldValue(facts, fieldName)
  return Array.isArray(fieldValue?.items) ? fieldValue.items : []
}

export function factValue(facts, fieldName) {
  return knownFieldValue(facts, fieldName)?.value || null
}

export function factStateText(facts, fieldName, fallback = 'Unknown') {
  const status = facts?.[fieldName]?.field_value?.status
  if (status === 'not_found') {
    return 'Not found'
  }
  if (status === 'not_applicable') {
    return 'Not applicable'
  }
  if (status === 'unknown') {
    return 'Unknown'
  }
  return fallback
}

export function coverageTagsForPlan(plan) {
  const factTags = factItems(plan?.facts, 'coverage_tags')
  if (plan?.facts?.coverage_tags) {
    return factTags
  }
  return plan?.comparisonFact?.coverage_tags || []
}

export function labelForTag(tag) {
  return String(tag)
    .split('_')
    .filter(Boolean)
    .map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`)
    .join(' ')
}

export function itemLabel(item) {
  if (typeof item === 'string') {
    return item
  }
  return (
    item?.normalized_name ||
    item?.name ||
    item?.label ||
    item?.condition ||
    item?.event ||
    item?.source_label ||
    item?.details ||
    item?.raw_text ||
    ''
  )
}

export function listText(items, fallback = 'Unknown') {
  const labels = (items || []).map(itemLabel).filter(Boolean)
  return labels.length > 0 ? labels.join(', ') : fallback
}

export function durationText(item, fieldName = 'duration_days') {
  const label = itemLabel(item)
  const days = item?.[fieldName]
  if (days !== null && days !== undefined && label) {
    return `${label}: ${days} days`
  }
  if (days !== null && days !== undefined) {
    return `${days} days`
  }
  return label
}

export function claimSlaText(facts) {
  const claimSla = factValue(facts, 'claim_sla')
  if (claimSla?.duration_days !== null && claimSla?.duration_days !== undefined) {
    return claimSla.basis
      ? `${claimSla.duration_days} days (${claimSla.basis})`
      : `${claimSla.duration_days} days`
  }
  return itemLabel(claimSla)
}

export function provenanceEntriesForFields(facts, fieldNames) {
  const groupedEntries = new Map()
  const missingFields = []

  for (const fieldName of fieldNames) {
    const fact = facts?.[fieldName]
    if (!fact) {
      missingFields.push(fieldLabel(fieldName))
      continue
    }

    const key = [
      fact.source_url || '',
      fact.source_type || '',
      fact.scraped_at || '',
      fact.last_verified_at || '',
    ].join('|')

    if (!groupedEntries.has(key)) {
      groupedEntries.set(key, {
        key: `source:${key}`,
        fields: [],
        sourceUrl: fact.source_url || '',
        sourceType: fact.source_type || '',
        scrapedAt: fact.scraped_at || '',
        lastVerifiedAt: fact.last_verified_at || '',
      })
    }

    groupedEntries.get(key).fields.push(fieldLabel(fieldName))
  }

  if (missingFields.length > 0) {
    groupedEntries.set(`missing:${missingFields.join('|')}`, {
      key: `missing:${missingFields.join('|')}`,
      fields: missingFields,
      sourceUrl: '',
      sourceType: '',
      scrapedAt: '',
      lastVerifiedAt: '',
      missing: true,
    })
  }

  return Array.from(groupedEntries.values())
}

export function profileProvenanceEntry(plan) {
  return [
    {
      key: 'plan-profile',
      fields: [fieldLabel('plan_profile')],
      sourceUrl: plan?.plan_url || plan?.product_brochure_url || '',
      sourceType: 'product_page',
      scrapedAt: plan?.scraped_at || '',
      lastVerifiedAt: plan?.scraped_at || '',
    },
  ]
}

export function fieldLabel(fieldName) {
  return FIELD_LABELS[fieldName] || labelForTag(fieldName)
}

export function sourceTypeLabel(sourceType) {
  return SOURCE_TYPE_LABELS[sourceType] || 'Source'
}

export function formatFactDate(value) {
  if (!value) {
    return ''
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }

  return new Intl.DateTimeFormat('en-SG', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date)
}

export function provenanceState(entry, now = new Date()) {
  if (entry?.missing || !entry?.sourceUrl || !entry?.scrapedAt || !entry?.lastVerifiedAt) {
    return 'Source incomplete'
  }

  const verifiedAt = new Date(entry.lastVerifiedAt)
  if (Number.isNaN(verifiedAt.getTime())) {
    return 'Verification missing'
  }

  const ageDays = (now.getTime() - verifiedAt.getTime()) / 86400000
  return ageDays > STALE_AFTER_DAYS ? 'Stale verification' : 'Verified'
}
