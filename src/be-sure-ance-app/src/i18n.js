import { ref } from 'vue'

export const messages = {
  en: {
    'language.label': 'Language',
    'hero.eyebrow': 'For Insurance Agents',
    'hero.title': 'Prepare carrier comparisons and provider lookups before the client meeting.',
    'hero.text':
      'Use the workspace to shortlist plans, open panel and specialist directories, and frame qualitative coverage signals instead of brochure-by-brochure guesswork.',
    'route.workspace': 'Plan workspace',
    'route.panelHospitals': 'Panel hospitals',
    'stats.carriers': 'Carriers tracked',
    'stats.plans': 'Plans loaded',
    'stats.briefReady': 'Brief-ready profiles',
    'stats.plansInBrief': 'Plans in brief',
    'workflow.meetingPrep.eyebrow': 'Meeting Prep',
    'workflow.meetingPrep.title': 'Build a three-plan brief fast.',
    'workflow.meetingPrep.text':
      'Keep shortlists tight, compare coverage signals side by side, and carry a cleaner story into the call.',
    'workflow.panelLookup.eyebrow': 'Panel Lookup',
    'workflow.panelLookup.title': 'Jump straight to provider directories.',
    'workflow.panelLookup.text':
      'Open hospital, panel, and specialist resources linked to the plan instead of hunting them down mid-conversation.',
    'workflow.carrierResearch.eyebrow': 'Carrier Research',
    'workflow.carrierResearch.title': 'Review one provider lane at a time.',
    'workflow.carrierResearch.text':
      'Use the provider rail to move through carriers quickly, then add only the plans worth presenting.',
    'status.loading': 'Loading plan data and qualitative facts...',
    'status.supabaseMissing':
      'Supabase configuration is missing. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.',
    'status.loadError': 'Unable to load qualitative plan data.',
    'shared.eyebrow': 'Shared Comparison',
    'shared.title': 'Shared plan set',
    'shared.created': 'Created {date} · {views}',
    'shared.back': 'Plan workspace',
    'shared.missingPlans':
      'Shared comparison found, but referenced plans are not loaded in the current dataset.',
    'shared.loading': 'Loading shared comparison...',
    'shared.notFound': 'Shared comparison not found.',
    'shared.loadError': 'Unable to load shared comparison.',
    'toolbar.activeProvider': 'Active Provider',
    'toolbar.copySuffix': 'Use this lane for carrier research and shortlist building.',
    'toolbar.searchPlaceholder': 'Search plans, benefits, notes, or provider resources',
    'toolbar.openCarrier': 'Open carrier site',
    'empty.routePlan': 'No plan matches this static plan URL yet.',
    'empty.provider': 'No supported plans are loaded for this provider yet.',
    'empty.search': 'No plans match the current provider and search filters.',
    'disclaimer.share':
      'This shared comparison is for pre-meeting research only. It is not financial advice, insurance advice, legal advice, a recommendation, a ranking, a quote, or a policy transaction. Verify every fact against the carrier source, compareFIRST where applicable, and the adviser compliance workflow.',
    'comparison.eyebrow': 'Comparison',
    'comparison.title': 'Client-ready comparison sheet',
    'comparison.copy':
      'Use this grid to frame what is covered, what is unknown, and where source links differ across shortlisted plans.',
    'comparison.empty': 'Select at least one plan to populate the comparison grid.',
    'comparison.field': 'Field',
    'field.coverage_tags': 'Coverage',
    'field.panel_hospitals': 'Network',
    'field.waiting_periods': 'Waiting periods',
    'field.claim_deadlines': 'Claim deadlines',
    'field.claim_sla': 'Claim SLA',
    'field.exclusions': 'Exclusions',
    'field.brochure_metadata': 'Brochure',
    'field.source_notes': 'Source notes',
    'sourceType.brochure_pdf': 'Brochure PDF',
    'sourceType.product_page': 'Product page',
    'sourceType.manual_entry': 'Manual entry',
    'sourceType.source': 'Source',
    'provenance.source': 'source',
    'provenance.sourceMissing': 'Source URL missing',
    'provenance.scraped': 'Scraped {date}',
    'provenance.verified': 'Verified {date}',
    'provenance.missing': 'missing',
    'provenance.state.verified': 'Verified',
    'provenance.state.sourceIncomplete': 'Source incomplete',
    'provenance.state.verificationMissing': 'Verification missing',
    'provenance.state.staleVerification': 'Stale verification',
    'plan.select': 'Add to brief',
    'plan.remove': 'Remove from brief',
    'plan.canonicalCarrier': 'Canonical carrier',
    'plan.details': 'Agent detail',
    'plan.productPage': 'Product page',
    'plan.brochureLink': 'Brochure',
    'plan.planPage': 'Plan page',
    'plan.coverage': 'Coverage',
    'plan.network': 'Network',
    'plan.process': 'Process',
    'plan.exclusions': 'Exclusions',
    'plan.brochure': 'Brochure',
    'plan.sourceNotes': 'Source notes',
    'plan.waitingPeriods': 'Waiting periods',
    'plan.claimDeadlines': 'Claim deadlines',
    'plan.claimSla': 'Claim SLA',
    'plan.tags': 'Tags',
  },
  'zh-SG': {
    'language.label': '语言',
    'hero.eyebrow': '给保险顾问',
    'hero.title': '在客户会面前准备保险公司比较和医疗网络查询。',
    'hero.text': '使用这个工作区筛选计划、打开医疗网络资料，并用定性保障信号整理会前研究。',
    'route.workspace': '计划工作区',
    'route.panelHospitals': '合作医院',
    'stats.carriers': '已追踪保险公司',
    'stats.plans': '已载入计划',
    'stats.briefReady': '可生成简报资料',
    'stats.plansInBrief': '简报中的计划',
    'workflow.meetingPrep.eyebrow': '会前准备',
    'workflow.meetingPrep.title': '快速建立三项计划简报。',
    'workflow.meetingPrep.text': '收窄候选计划，并排比较保障信号，让通话前的说明更清楚。',
    'workflow.panelLookup.eyebrow': '医疗网络查询',
    'workflow.panelLookup.title': '直接打开服务机构目录。',
    'workflow.panelLookup.text': '打开与计划相关的医院、合作网络和专科资源，减少临场查找。',
    'workflow.carrierResearch.eyebrow': '保险公司研究',
    'workflow.carrierResearch.title': '一次查看一个保险公司渠道。',
    'workflow.carrierResearch.text': '通过保险公司列表快速切换，只加入值得说明的计划。',
    'status.loading': '正在载入计划资料和定性事实...',
    'status.supabaseMissing':
      '缺少 Supabase 设置。请设置 VITE_SUPABASE_URL 和 VITE_SUPABASE_ANON_KEY。',
    'status.loadError': '无法载入定性计划资料。',
    'shared.eyebrow': '共享比较',
    'shared.title': '共享计划组合',
    'shared.created': '创建于 {date} · {views}',
    'shared.back': '计划工作区',
    'shared.missingPlans': '已找到共享比较，但当前数据集中没有载入引用的计划。',
    'shared.loading': '正在载入共享比较...',
    'shared.notFound': '找不到共享比较。',
    'shared.loadError': '无法载入共享比较。',
    'toolbar.activeProvider': '当前保险公司',
    'toolbar.copySuffix': '使用此渠道进行保险公司研究和候选计划整理。',
    'toolbar.searchPlaceholder': '搜索计划、利益、备注或服务机构资源',
    'toolbar.openCarrier': '打开保险公司网站',
    'empty.routePlan': '没有计划符合这个静态计划网址。',
    'empty.provider': '这个保险公司尚未载入受支持的计划。',
    'empty.search': '没有计划符合当前保险公司和搜索条件。',
    'disclaimer.share':
      '此共享比较仅供会前研究使用。它不是财务建议、保险建议、法律建议、推荐、排名、报价或保单交易。请根据保险公司来源、适用时的 compareFIRST，以及顾问的合规流程核实每一项事实。',
    'comparison.eyebrow': '比较',
    'comparison.title': '客户简报比较表',
    'comparison.copy': '使用此表说明已知保障、未知项目，以及候选计划之间的来源差异。',
    'comparison.empty': '请选择至少一项计划以填充比较表。',
    'comparison.field': '字段',
    'field.coverage_tags': '保障',
    'field.panel_hospitals': '网络',
    'field.waiting_periods': '等待期',
    'field.claim_deadlines': '索赔期限',
    'field.claim_sla': '索赔时限',
    'field.exclusions': '除外责任',
    'field.brochure_metadata': '产品册',
    'field.source_notes': '来源备注',
    'sourceType.brochure_pdf': 'PDF 产品册',
    'sourceType.product_page': '产品页面',
    'sourceType.manual_entry': '人工录入',
    'sourceType.source': '来源',
    'provenance.source': '来源',
    'provenance.sourceMissing': '缺少来源网址',
    'provenance.scraped': '抓取于 {date}',
    'provenance.verified': '核实于 {date}',
    'provenance.missing': '缺失',
    'provenance.state.verified': '已核实',
    'provenance.state.sourceIncomplete': '来源不完整',
    'provenance.state.verificationMissing': '缺少核实日期',
    'provenance.state.staleVerification': '核实日期已过旧',
    'plan.select': '加入简报',
    'plan.remove': '从简报移除',
    'plan.canonicalCarrier': '规范保险公司名称',
    'plan.details': '顾问详情',
    'plan.productPage': '产品页面',
    'plan.brochureLink': '产品册',
    'plan.planPage': '计划页面',
    'plan.coverage': '保障',
    'plan.network': '网络',
    'plan.process': '流程',
    'plan.exclusions': '除外责任',
    'plan.brochure': '产品册',
    'plan.sourceNotes': '来源备注',
    'plan.waitingPeriods': '等待期',
    'plan.claimDeadlines': '索赔期限',
    'plan.claimSla': '索赔时限',
    'plan.tags': '标签',
  },
}

export const supportedLocales = [
  { code: 'en', label: 'EN' },
  { code: 'zh-SG', label: '中文' },
]

const STORAGE_KEY = 'be-sure-ance-locale'
const locale = ref(initialLocale())

export function useI18n() {
  return { locale, supportedLocales, setLocale, t }
}

export function setLocale(nextLocale) {
  if (!messages[nextLocale]) return
  locale.value = nextLocale
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(STORAGE_KEY, nextLocale)
    document.documentElement.lang = nextLocale
  }
}

export function t(key, params = {}) {
  const text = messages[locale.value]?.[key] || messages.en[key] || `[missing:${key}]`
  return Object.entries(params).reduce(
    (result, [paramKey, value]) => result.replaceAll(`{${paramKey}}`, value ?? ''),
    text,
  )
}

function initialLocale() {
  if (typeof window === 'undefined') return 'en'
  const storedLocale = window.localStorage.getItem(STORAGE_KEY)
  const nextLocale = messages[storedLocale] ? storedLocale : 'en'
  document.documentElement.lang = nextLocale
  return nextLocale
}
