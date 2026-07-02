const MAX_PLANS_PER_BRIEF = 3
const QUALITATIVE_FIELDS = [
  ['coverage_tags', 'Coverage'],
  ['panel_hospitals', 'Panel hospitals'],
  ['waiting_periods', 'Waiting periods'],
  ['claim_deadlines', 'Claim deadlines'],
  ['claim_sla', 'Claim SLA'],
  ['exclusions', 'Exclusions'],
  ['source_notes', 'Source notes'],
]
const NO_ADVICE_DISCLAIMER =
  'This brief is for pre-meeting research only. It is not financial advice, insurance advice, legal advice, a recommendation, a ranking, a quote, or a policy transaction. Verify every fact against the carrier source, compareFIRST where applicable, and the adviser licensed compliance workflow.'

export default async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 204 })
  }
  if (req.method !== 'POST') {
    return jsonError('Method not allowed.', 405)
  }

  let payload
  try {
    payload = await req.json()
  } catch {
    return jsonError('Invalid JSON payload.', 400)
  }

  const plans = Array.isArray(payload?.plans) ? payload.plans : []
  if (plans.length === 0 || plans.length > MAX_PLANS_PER_BRIEF) {
    return jsonError(`PDF briefs support 1-${MAX_PLANS_PER_BRIEF} plans.`, 400)
  }

  const pdf = buildPdf(briefLines(plans, payload?.branding || {}))
  return new Response(pdf, {
    headers: {
      'Content-Type': 'application/pdf',
      'Content-Disposition': 'attachment; filename="be-sure-ance-client-brief.pdf"',
      'Cache-Control': 'no-store',
    },
  })
}

export const config = {
  method: ['OPTIONS', 'POST'],
  path: '/briefs/client.pdf',
}

function jsonError(message, status) {
  return Response.json({ detail: message }, { status })
}

function briefLines(plans, branding) {
  const lines = [
    'Be-sure-ance Client Brief',
    `Generated at ${new Date().toISOString().replace(/\.\d{3}Z$/, '+00:00')}`,
    '',
    NO_ADVICE_DISCLAIMER,
    '',
    brandingFooterText(branding),
    '',
  ]

  for (const plan of plans) {
    lines.push(planHeading(plan))
    for (const [fieldName, label] of QUALITATIVE_FIELDS) {
      lines.push(`${label}: ${fieldText(plan, fieldName)}`)
    }
    const sources = sourceLines(plan)
    lines.push('Sources:')
    lines.push(...(sources.length ? sources : ['No sources']))
    lines.push('')
  }
  return lines.flatMap((line) => wrapLine(line, 92)).slice(0, 62)
}

function planHeading(plan) {
  const provider = safeText(plan.canonical_carrier_name || plan.providerName || plan.insurer)
  const planName = safeText(plan.plan_name)
  return provider ? `${provider}: ${planName}` : planName
}

function fieldText(plan, fieldName) {
  const fieldValue = plan?.facts?.[fieldName]?.field_value || {}
  if (fieldValue.status && fieldValue.status !== 'known') {
    return safeText(fieldValue.status)
  }
  if (fieldName === 'claim_sla') {
    const value = fieldValue.value || {}
    if (value.duration_days) {
      return `${value.duration_days} days${value.basis ? ` (${safeText(value.basis)})` : ''}`
    }
  }
  const items = Array.isArray(fieldValue.items) ? fieldValue.items : []
  return items.map((item) => itemText(item, fieldName)).filter(Boolean).join('; ') || 'Unknown'
}

function itemText(item, fieldName) {
  if (typeof item === 'string') {
    return safeText(item)
  }
  if (!item || typeof item !== 'object') {
    return ''
  }
  if (fieldName === 'waiting_periods' && item.duration_days !== undefined) {
    return `${safeText(item.condition)}: ${item.duration_days} days`
  }
  if (fieldName === 'claim_deadlines' && item.deadline_days !== undefined) {
    return `${safeText(item.event)}: ${item.deadline_days} days`
  }
  return safeText(
    item.normalized_name ||
      item.name ||
      item.label ||
      item.condition ||
      item.event ||
      item.details ||
      item.raw_text,
  )
}

function sourceLines(plan) {
  return QUALITATIVE_FIELDS.map(([fieldName, label]) => {
    const fact = plan?.facts?.[fieldName] || {}
    if (!fact.source_url) {
      return ''
    }
    const sourceType = fact.source_type || 'source'
    const verifiedAt = fact.last_verified_at || 'verification missing'
    return `${label}: ${sourceType}; verified ${verifiedAt}; ${fact.source_url}`
  }).filter(Boolean)
}

function brandingFooterText(branding) {
  const agentName = safeText(branding.agent_name || branding.agentName)
  const masRepNumber = safeText(branding.mas_rep_number || branding.masRepNumber)
  if (agentName && masRepNumber) {
    return `Prepared by ${agentName} | MAS rep no. ${masRepNumber}`
  }
  if (agentName) {
    return `Prepared by ${agentName} | MAS rep no. not provided`
  }
  if (masRepNumber) {
    return `Prepared by unbranded adviser | MAS rep no. ${masRepNumber}`
  }
  return 'Prepared by unbranded adviser | MAS rep no. not provided'
}

function buildPdf(lines) {
  const textOps = lines
    .map((line, index) => `1 0 0 1 50 ${790 - index * 12} Tm (${pdfText(line)}) Tj`)
    .join('\n')
  const content = `BT\n/F1 9 Tf\n11 TL\n${textOps}\nET`
  const objects = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
    `<< /Length ${Buffer.byteLength(content)} >>\nstream\n${content}\nendstream`,
  ]
  const chunks = ['%PDF-1.4\n']
  const offsets = [0]
  for (const [index, object] of objects.entries()) {
    offsets.push(Buffer.byteLength(chunks.join('')))
    chunks.push(`${index + 1} 0 obj\n${object}\nendobj\n`)
  }
  const xrefOffset = Buffer.byteLength(chunks.join(''))
  chunks.push(`xref\n0 ${objects.length + 1}\n`)
  chunks.push('0000000000 65535 f \n')
  for (const offset of offsets.slice(1)) {
    chunks.push(`${String(offset).padStart(10, '0')} 00000 n \n`)
  }
  chunks.push(
    `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`,
  )
  return Buffer.from(chunks.join(''))
}

function wrapLine(value, limit) {
  const words = safeText(value).split(' ')
  const lines = []
  let current = ''
  for (const word of words) {
    if (`${current} ${word}`.trim().length > limit) {
      lines.push(current)
      current = word
    } else {
      current = `${current} ${word}`.trim()
    }
  }
  if (current || lines.length === 0) {
    lines.push(current)
  }
  return lines
}

function pdfText(value) {
  return safeText(value).replace(/[\\()]/g, '\\$&')
}

function safeText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim()
}
