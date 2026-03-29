export const providers = [
  {
    key: "aia",
    name: "AIA Singapore",
    website: "https://www.aia.com.sg/en/index",
    focus: "Health, life, and personal protection"
  },
  {
    key: "china_life",
    name: "China Life Singapore",
    website: "https://www.chinalife.com.sg/",
    focus: "Medical, life, and savings plans"
  },
  {
    key: "chubb",
    name: "Chubb Insurance (Singapore)",
    website: "https://www.chubb.com/sg-en/",
    focus: "Personal and commercial protection"
  },
  {
    key: "great_eastern",
    name: "Great Eastern Singapore",
    website: "https://www.greateasternlife.com/sg/en/personal-insurance.html",
    focus: "Life, health, and long-term planning"
  },
  {
    key: "hsbc",
    name: "HSBC Singapore Insurance",
    website: "https://www.insurance.hsbc.com.sg/",
    focus: "Retail protection and medical products"
  },
  {
    key: "iii",
    name: "India International Insurance (Singapore)",
    website: "https://www.iii.com.sg/",
    focus: "General insurance and medical options"
  },
  {
    key: "singlife",
    name: "Singlife",
    website: "https://singlife.com/en",
    focus: "Digital protection, health, and life"
  },
  {
    key: "sunlife",
    name: "Sun Life",
    website: "https://www.sunlife.com/en/",
    focus: "Health and life solutions"
  },
  {
    key: "tokio_marine",
    name: "Tokio Marine Insurance Group",
    website: "https://www.tokiomarine.com/sg/en.html",
    focus: "Medical, motor, and personal protection"
  },
  {
    key: "uoi",
    name: "United Overseas Insurance Limited (UOI)",
    website: "https://www.uoi.com.sg/index.page",
    focus: "General and accident-linked protection"
  }
]

export function buildPlanKey(providerKey, planName) {
  return `${providerKey}::${planName}`
}
