const EXACT_ZH = new Map([
  ['Endowment', '储蓄保险'],
  ['Legacy Planning', '传承规划'],
  ['Riders', '附加保障'],
  ['Retirement', '退休规划'],
  ['Protection', '保障'],
  ['Accident', '意外'],
  ['Life', '人寿'],
  ['Critical Illness', '严重疾病'],
  ['Provider Directory', '服务机构目录'],
  ['Unknown', '未知'],
  ['Not found', '未找到'],
  ['Not applicable', '不适用'],
  ['Known', '已知'],
])

const ZH_PHRASES = [
  [
    'Comforting news for your family. Thoughtful planning for the unexpected.',
    '让家人安心，为意外周全规划。',
  ],
  ['Choose among our four offerings:', '从以下四个方案中选择：'],
  ['Sum Insured for accidental death or permanent disablement', '意外身故或永久伤残保额'],
  ['Medical expenses for accidents', '意外医疗费用'],
  ['Here is are some key points to take note:', '以下是需要留意的要点：'],
  ['All amounts shown are in Singapore Dollars', '所有金额均以新加坡元列示'],
  [
    'Benefits under this insurance will be payable only upon death, permanent disablement or injury due to an accident.',
    '本保险的利益仅在因意外导致身故、永久伤残或受伤时支付。',
  ],
  [
    'All those who are insured must be a Singapore citizen, Singapore Permanent Resident or foreigner who is holding a valid employment pass, work permit, dependent pass, student pass or social visit pass and residing in Singapore.',
    '所有受保人必须是新加坡公民、新加坡永久居民，或持有有效就业准证、工作准证、家属准证、学生准证或社交访问准证并居住在新加坡的外籍人士。',
  ],
  [
    'You or your spouse must be at least 18 years old and below the age of 70 at the commencement of this insurance.',
    '本保险开始时，您或配偶必须年满 18 岁且未满 70 岁。',
  ],
  [
    'If enrolled under this insurance before 65 years old and there is no lapse in cover, this insurance is renewable until the age of 85.',
    '若在 65 岁前投保且保障未中断，本保险可续保至 85 岁。',
  ],
  [
    'However, once you or your spouse is 75 years old and above, only Plan A, B or C can be selected.',
    '但是，当您或配偶年满 75 岁或以上时，只能选择计划 A、B 或 C。',
  ],
  [
    'Your dependent child(ren) must be at least 1 month old at the commencement of this insurance and you can continue to cover them under this insurance until they are 21 or 25 (if the child is studying full-time in a tertiary institution).',
    '本保险开始时，您的受抚养子女必须至少 1 个月大；您可继续为其提供保障至 21 岁，或在其于高等院校全日制就读时至 25 岁。',
  ],
  [
    'If you or your spouse is a homemaker, full-time student, retiree or unemployed, only Plan A, B or C can be selected',
    '若您或配偶为家庭主妇/主夫、全日制学生、退休人士或失业人士，只能选择计划 A、B 或 C',
  ],
  [
    'If you, your spouse or your dependent child(ren) has/have more than one policy with us covering against Terrorism, the maximum amount payable for Acts of Terrorism for all the policies shall not exceed $500,000 per person.',
    '若您、配偶或受抚养子女持有多份由本公司承保恐怖主义风险的保单，所有保单针对恐怖主义行为的最高应付金额合计不得超过每人 $500,000。',
  ],
  [
    'When more than one person is insured under the policy, the total maximum amount payable under the policy is further subjected to a conveyance/event limit.',
    '当同一保单承保多人时，保单下的最高应付总额还受交通工具/事件限额约束。',
  ],
  [
    'Premium rates are non-guaranteed and may be reviewed from time to time',
    '保费率不保证，并可能不时调整',
  ],
  [
    'You or we may cancel the policy by giving each other prior notice in writing.',
    '您或本公司可通过书面提前通知对方取消保单。',
  ],
  [
    'Please refer to the policy wordings for the cancellation conditions and applicable charges.',
    '取消条件及适用费用请参阅保单条款。',
  ],
  [
    'If you or your spouse wish(es) to nominate a beneficiary, please contact your intermediary for the relevant forms.',
    '如您或配偶希望指定受益人，请联系中介人索取相关表格。',
  ],
  ['How much is my premium?', '我的保费是多少？'],
  ['Your premium may vary, depending on:', '您的保费可能因以下因素而异：'],
  ['The type of plan selected', '所选计划类型'],
  ['Your nature of work', '工作性质'],
  ['Our underwriting requirements', '本公司的核保要求'],
  [
    'Travel how you want - UniTravel will handle the ‘what ifs’',
    '按您想要的方式旅行，UniTravel 为意外情况提供保障',
  ],
  [
    'With UniTravel insurance, enjoy comprehensive coverage for:',
    '通过 UniTravel 保险，可享有以下综合保障：',
  ],
  ['Reimbursement for overseas medical expenses of up to', '海外医疗费用报销最高可达'],
  ['Coverage for loss of frequent flyer miles of up to', '常旅客里程损失保障最高可达'],
  ['Thank you for insuring with', '感谢您向以下机构投保：'],
  ['United Overseas Insurance Limited', '大华保险有限公司'],
  ['Personal Accident Insurance', '个人意外保险'],
  ['Travel Insurance', '旅游保险'],
  ['Home Insurance', '家居保险'],
  ['Car Insurance', '汽车保险'],
  ['Life Insurance', '人寿保险'],
  ['Critical Illness', '严重疾病'],
  ['Medical Insurance', '医疗保险'],
  ['Hospital & Surgical', '住院及手术'],
  ['Legacy Planning', '传承规划'],
  ['Premium Waiver', '保费豁免'],
  ['Payer Benefit', '投保人利益'],
  ['Cashback', '现金回馈'],
  ['View Policy Wording', '查看保单条款'],
  ['Policy Wording', '保单条款'],
  ['Product Summary', '产品摘要'],
  ['Claim Form', '索赔表格'],
  ['Specialist Listing', '专科名单'],
  ['Paediatric Panel', '儿科网络'],
  ['Provider Directory', '服务机构目录'],
  ['Panel hospitals', '合作医院'],
  ['Panel hospital', '合作医院'],
  ['Waiting periods', '等待期'],
  ['Waiting period', '等待期'],
  ['Claim deadlines', '索赔期限'],
  ['Claim deadline', '索赔期限'],
  ['Claim SLA', '索赔时限'],
  ['Source notes', '来源备注'],
  ['Manual review note', '人工复核备注'],
  ['Important Notes', '重要说明'],
  ['Options', '选项'],
  ['Brochure', '产品册'],
  ['Coverage', '保障'],
  ['Network', '网络'],
  ['Exclusions', '除外责任'],
  ['Retirement', '退休'],
  ['Protection', '保障'],
  ['Endowment', '储蓄'],
  ['Insurance', '保险'],
  ['Unknown', '未知'],
  ['Not found', '未找到'],
  ['Not applicable', '不适用'],
  ['Needs review', '需复核'],
  ['Known', '已知'],
].sort((left, right) => right[0].length - left[0].length)

const ZH_PATTERNS = [
  [/\bPlan ([A-Z])\b/g, '计划 $1'],
  [/\b(\d+)\s+working days?\b/gi, '$1 个工作日'],
  [/\b(\d+)\s+days?\b/gi, '$1 天'],
  [/\b(\d+)\s+months?\b/gi, '$1 个月'],
  [/\byears? old\b/gi, '岁'],
  [/\bper person\b/gi, '每人'],
  [/\bsource\b/gi, '来源'],
]

export function translateContent(value, locale) {
  const text = String(value ?? '')
  if (!text || locale !== 'zh-SG') {
    return text
  }
  const normalized = cleanText(text)
  if (!normalized || /[\u3400-\u9fff]/.test(normalized)) {
    return normalized
  }
  const exact = EXACT_ZH.get(normalized)
  if (exact) {
    return exact
  }
  return ZH_PATTERNS.reduce(
    (result, [pattern, replacement]) => result.replace(pattern, replacement),
    ZH_PHRASES.reduce(
      (result, [source, target]) => result.replace(new RegExp(escapeRegExp(source), 'gi'), target),
      normalized,
    ),
  )
}

function cleanText(value) {
  return String(value || '')
    .replace(/\u00a0/g, ' ')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}
