const MISSING_VALUES = new Set(['', '-', 'n/a', 'na', 'none', 'null', 'undefined', 'unknown']);

const ACTIVITY_RULES = [
  { label: 'Running', keywords: ['running', ' run', 'jog', 'runner'] },
  { label: 'Walking', keywords: ['walking', ' walk', 'hike', 'hiking', 'stroll'] },
  { label: 'Cycling', keywords: ['cycling', ' cycle', 'bike', 'biking', 'ride'] }
];

const TERRAIN_RULES = [
  { label: 'Mixed', keywords: ['mixed', 'multi-use', 'boardwalk', 'connector'] },
  { label: 'Off-Road', keywords: ['off-road', 'trail', 'forest', 'dirt', 'mud', 'rugged', 'park', 'nature'] },
  { label: 'Road', keywords: ['road', 'paved', 'street', 'urban', 'promenade', 'waterfront'] }
];

function trimValue(value: unknown) {
  return typeof value === 'string' ? value.replace(/\s+/g, ' ').trim() : '';
}

function isMissing(value: unknown) {
  const candidate = trimValue(value).toLowerCase();
  return !candidate || MISSING_VALUES.has(candidate);
}

function classifyValue(value: unknown, rules: Array<{ label: string; keywords: string[] }>) {
  if (isMissing(value)) {
    return 'Missing';
  }

  const candidate = ` ${trimValue(value).toLowerCase()} `;
  const match = rules.find((rule) => rule.keywords.some((keyword) => candidate.includes(keyword)));
  return match ? match.label : 'Unclassified';
}

export function safeExternalUrl(value: unknown) {
  if (typeof value !== 'string' || !value.trim()) {
    return null;
  }

  try {
    const parsed = new URL(value);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:' ? parsed.toString() : null;
  } catch {
    return null;
  }
}

function formatMetric(value: unknown, fallback: string) {
  const trimmed = trimValue(value);
  return trimmed || fallback;
}

function formatText(value: unknown, fallback: string) {
  const trimmed = trimValue(value);
  return trimmed || fallback;
}

export function sourceLabel(value: unknown) {
  const safeUrl = safeExternalUrl(value);
  if (!safeUrl) {
    return 'Unavailable';
  }

  return new URL(safeUrl).hostname.replace(/^www\./, '');
}

export function excerpt(value: unknown, maxLength = 132) {
  const trimmed = trimValue(value);
  if (!trimmed) {
    return 'No descriptive summary was captured for this route.';
  }

  if (trimmed.length <= maxLength) {
    return trimmed;
  }

  return `${trimmed.slice(0, maxLength - 1).trim()}…`;
}

export function normalizeRoute(route: Record<string, unknown>) {
  const safeUrl = safeExternalUrl(route.route_url);
  const activityRaw = trimValue(route.route_activity_type);
  const terrainRaw = trimValue(route.route_terrain_type);
  const countryLabel = formatText(route.country, 'Country not listed');
  const locationLabel = formatText(route.location, 'Location not listed');

  return {
    ...route,
    id: String(route.ID ?? `${route.route_name ?? 'route'}-${route.location ?? 'unknown'}`),
    routeName: formatText(route.route_name, 'Untitled route'),
    activityRaw,
    terrainRaw,
    activityLabel: classifyValue(activityRaw, ACTIVITY_RULES),
    terrainLabel: classifyValue(terrainRaw, TERRAIN_RULES),
    distanceLabel: formatMetric(route.route_distance, 'Distance not listed'),
    elevationLabel: formatMetric(route.route_elevation_gain, 'Elevation not listed'),
    locationLabel,
    countryLabel,
    viewsLabel: formatMetric(route.route_number_views, 'Views not listed'),
    safeUrl,
    sourceLabel: sourceLabel(route.route_url),
    summary: excerpt(activityRaw || terrainRaw || route.route_name),
    searchText: [
      route.route_name,
      route.location,
      route.country,
      activityRaw,
      terrainRaw,
      sourceLabel(route.route_url)
    ]
      .map((value) => trimValue(value))
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
  };
}
