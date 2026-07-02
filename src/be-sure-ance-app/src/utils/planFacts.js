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
