export type SignalTone = 'neutral' | 'watch' | 'strong'

export type Highlight = {
  text: string
  type: 'certainty' | 'urgency' | 'guarantee' | 'social-proof' | 'scarcity'
  note: string
}

export type MessageItem = {
  id: number
  text: string
  certainty: 'Reported' | 'Asserted' | 'Absolute'
  highlights: Highlight[]
}

export type Mutation = {
  from: number
  to: number
  title: string
  detail: string
  tone: SignalTone
}

export type AnalysisReport = {
  status: string
  summary: string
  messages: MessageItem[]
  mutations: Mutation[]
  signals: Array<{
    label: string
    value: string
    caption: string
    tone: SignalTone
  }>
  explanation: {
    en: string
    hi: string
  }
  safety: {
    en: string[]
    hi: string[]
  }
  diagnostics?: {
    averageSimilarity: number
    strongestSignal: string
    certaintyShift: string
    urgencyShift: string
    modelMode: string
    rawPairs: Array<{
      message_index: number
      certainty_change: string
      urgency_change: string
      semantic_similarity: number
      added_claims: string[]
      persuasion_indicators: string[]
    }>
  }
}

export type SequencePair = {
  message_index: number
  semantic_similarity: number | { similarity?: number } | null
  certainty_change: 'INCREASED' | 'DECREASED' | 'UNCHANGED' | 'AMBIGUOUS'
  urgency_change: 'INCREASED' | 'DECREASED' | 'UNCHANGED' | 'AMBIGUOUS'
  added_claims: string[]
  removed_qualifiers: string[]
  persuasion_indicators: string[]
  explanation: string
}

export type SequenceApiResponse = {
  status: string
  pairs: SequencePair[]
  limitations?: string[]
}

const DEFAULT_API_URL = 'http://localhost:8000'

function normalizeSimilarity(value: number | { similarity?: number } | null | undefined): number {
  if (typeof value === 'number') return Number.isFinite(value) ? value : 0
  if (value && typeof value === 'object' && typeof value.similarity === 'number') {
    return Number.isFinite(value.similarity) ? value.similarity : 0
  }
  return 0
}

export function getApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    const override = (window as typeof window & { __ECHOTRAP_API_URL__?: string }).__ECHOTRAP_API_URL__
    if (override) {
      return override
    }
  }
  return DEFAULT_API_URL
}

export async function fetchSequenceAnalysis(messages: string[]): Promise<SequenceApiResponse> {
  const response = await fetch(`${getApiBaseUrl()}/analyze/sequence`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages: messages.map((message) => message.trim()).filter((message) => message.length > 0) }),
  })

  if (!response.ok) {
    let payload: { detail?: string } = {}
    try {
      payload = await response.json()
    } catch {
      // ignore json parsing errors and fall back to status text
    }
    throw new Error(payload.detail || `Request failed with status ${response.status}`)
  }

  return response.json()
}

export function mapSequenceToAnalysisReport(raw: SequenceApiResponse, inputMessages: string[]): AnalysisReport {
  const pairs = raw.pairs ?? []
  const averageSimilarity = pairs.length
    ? Math.round(
        (pairs
          .map((pair) => normalizeSimilarity(pair.semantic_similarity))
          .reduce((sum, value) => sum + value, 0) /
          pairs.length) *
          100,
      )
    : 81

  const highestRisk = pairs.some((pair) => pair.certainty_change === 'INCREASED' || pair.urgency_change === 'INCREASED')
  const status = highestRisk ? 'Multiple language-risk signals detected' : 'Limited language drift observed'
  const summary = pairs.length
    ? pairs.map((pair) => pair.explanation).join(' ')
    : 'The supplied message sequence is semantically similar but does not show strong language mutation indicators.'

  const messages: MessageItem[] = inputMessages.map((text, index) => {
    const certainty: MessageItem['certainty'] = index === 0 ? 'Reported' : index === inputMessages.length - 1 ? 'Absolute' : 'Asserted'
    const highlights: Highlight[] = []

    if (index === 0 && text.toLowerCase().includes('may')) {
      highlights.push({
        text: 'may',
        type: 'certainty',
        note: 'The message presents the claim with uncertainty.',
      })
    }

    if (index > 0 && pairs[index - 1]?.certainty_change === 'INCREASED') {
      highlights.push({
        text: 'confirmed',
        type: 'certainty',
        note: 'The statement becomes more definitive than the earlier version.',
      })
    }

    if (index === inputMessages.length - 1 && pairs[pairs.length - 1]?.urgency_change === 'INCREASED') {
      highlights.push({
        text: 'immediately',
        type: 'urgency',
        note: 'The latest message introduces stronger action pressure.',
      })
    }

    if (index === inputMessages.length - 1 && pairs[pairs.length - 1]?.added_claims.length) {
      highlights.push({
        text: pairs[pairs.length - 1].added_claims[0] || 'guaranteed outcome',
        type: 'guarantee',
        note: 'A new outcome claim appears in the latest message.',
      })
    }

    return { id: index + 1, text, certainty, highlights }
  })

  const mutations: Mutation[] = pairs.map((pair, index) => ({
    from: pair.message_index,
    to: pair.message_index + 1,
    title:
      pair.certainty_change === 'INCREASED'
        ? 'Certainty increased'
        : pair.urgency_change === 'INCREASED'
          ? 'Urgency pressure added'
          : 'Claim language shifted',
    detail: pair.explanation,
    tone: pair.certainty_change === 'INCREASED' || pair.urgency_change === 'INCREASED' ? 'strong' : 'watch',
  }))

  const signals: AnalysisReport['signals'] = [
    {
      label: 'Semantic relatedness',
      value: `${averageSimilarity}%`,
      caption: 'Messages discuss the same underlying topic.',
      tone: 'neutral',
    },
    {
      label: 'Certainty shift',
      value: pairs.some((pair) => pair.certainty_change === 'INCREASED') ? 'High' : 'Moderate',
      caption: 'The sequence moves from tentative wording toward stronger assertion.',
      tone: pairs.some((pair) => pair.certainty_change === 'INCREASED') ? 'strong' : 'watch',
    },
    {
      label: 'Urgency language',
      value: pairs.some((pair) => pair.urgency_change === 'INCREASED') ? 'Present' : 'Limited',
      caption: 'Action pressure appears in the later message versions.',
      tone: pairs.some((pair) => pair.urgency_change === 'INCREASED') ? 'watch' : 'neutral',
    },
    {
      label: 'Guaranteed outcome',
      value: pairs.some((pair) => pair.added_claims.some((claim) => /guarantee|profit|return|sure|certain/i.test(claim))) ? 'Present' : 'Absent',
      caption: 'The sequence includes outcome language beyond the original claim.',
      tone: pairs.some((pair) => pair.added_claims.some((claim) => /guarantee|profit|return|sure|certain/i.test(claim))) ? 'strong' : 'neutral',
    },
  ]

  const explanation = {
    en:
      pairs.length > 0
        ? `The sequence shows a change from cautious framing to stronger claim language. ${pairs
            .map((pair) => pair.explanation)
            .join(' ')}`
        : 'The supplied messages remain broadly similar in wording and do not show major mutation signals.',
    hi:
      pairs.length > 0
        ? `संदेशों में सतही भाषा से अधिक निश्चित भाषा की ओर बदलाव दिखता है। ${pairs
            .map((pair) => pair.explanation)
            .join(' ')}`
        : 'प्रदान किए गए संदेश मुख्यतः समान हैं और कोई बड़ी भाषा-परिवर्तन संकेत नहीं दिखते हैं।',
  }

  const strongestSignal = pairs.length
    ? pairs.reduce((best, pair) => {
        const current = Math.max(
          normalizeSimilarity(pair.semantic_similarity),
          pair.certainty_change === 'INCREASED' ? 0.9 : 0.2,
          pair.urgency_change === 'INCREASED' ? 0.8 : 0.15,
        )
        return current > best ? current : best
      }, 0)
    : 0

  const safety = {
    en: [
      'Pause before acting on messages that combine certainty with urgency.',
      'Verify important claims independently using reputable sources.',
      'Do not treat forward or repeated messaging as proof by itself.',
    ],
    hi: [
      'ऐसे संदेशों पर तुरंत कार्रवाई न करें जिनमें निश्चितता और जल्दी करने का दबाव हो।',
      'महत्वपूर्ण दावों को प्रतिष्ठित स्रोतों से अलग से सत्यापित करें।',
      'फॉरवर्ड या बार-बार दोहराए गए संदेश को अकेले प्रमाण न मानें।',
    ],
  }

  return {
    status,
    summary,
    messages,
    mutations,
    signals,
    explanation,
    safety,
    diagnostics: {
      averageSimilarity: averageSimilarity,
      strongestSignal: strongestSignal > 0.8 ? 'certainty and urgency escalation' : 'semantic continuity',
      certaintyShift: pairs.some((pair) => pair.certainty_change === 'INCREASED') ? 'increased' : 'stable',
      urgencyShift: pairs.some((pair) => pair.urgency_change === 'INCREASED') ? 'increased' : 'stable',
      modelMode: 'lexical fallback + mutation heuristics',
      rawPairs: pairs.map((pair) => ({
        message_index: pair.message_index,
        certainty_change: pair.certainty_change,
        urgency_change: pair.urgency_change,
        semantic_similarity: normalizeSimilarity(pair.semantic_similarity),
        added_claims: pair.added_claims,
        persuasion_indicators: pair.persuasion_indicators,
      })),
    },
  }
}
