export function safeExternalUrl(value) {
  if (!value || typeof value !== 'string') {
    return ''
  }

  try {
    const url = new URL(value)
    if (url.protocol === 'http:' || url.protocol === 'https:') {
      return url.toString()
    }
  } catch {
    return ''
  }

  return ''
}

export function externalHostname(value) {
  const safeUrl = safeExternalUrl(value)
  if (!safeUrl) {
    return ''
  }

  return new URL(safeUrl).hostname.replace(/^www\./, '')
}
