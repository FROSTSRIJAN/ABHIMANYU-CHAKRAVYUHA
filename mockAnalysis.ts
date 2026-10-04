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

export const sampleMessages = [
  'ABC Ltd may announce a new manufacturing project next quarter, according to early market chatter.',
  'ABC Ltd has confirmed a major manufacturing project and investors are expecting a strong reaction.',
  'Confirmed! ABC Ltd is set to explode after the project news. Guaranteed profit — invest immediately before everyone finds out.'
]

export const mockAnalysis = {
  status: 'Multiple language-risk signals detected',
  summary: 'The sequence shifts from an uncertain report to a confident assertion, then adds an unsupported guaranteed-outcome claim and pressure to act immediately.',
  messages: [
    {
      id: 1,
      text: sampleMessages[0],
      certainty: 'Reported',
      highlights: [
        { text: 'may announce', type: 'certainty', note: 'The claim is explicitly uncertain.' }
      ]
    },
    {
      id: 2,
      text: sampleMessages[1],
      certainty: 'Asserted',
      highlights: [
        { text: 'has confirmed', type: 'certainty', note: 'Uncertainty has been converted into a definite assertion.' },
        { text: 'strong reaction', type: 'social-proof', note: 'A market-outcome expectation is introduced without evidence in the supplied messages.' }
      ]
    },
    {
      id: 3,
      text: sampleMessages[2],
      certainty: 'Absolute',
      highlights: [
        { text: 'Confirmed!', type: 'certainty', note: 'The message opens with absolute certainty.' },
        { text: 'Guaranteed profit', type: 'guarantee', note: 'A guaranteed financial outcome has been added.' },
        { text: 'invest immediately', type: 'urgency', note: 'The user is pressured to act without time for verification.' },
        { text: 'before everyone finds out', type: 'scarcity', note: 'Scarcity/exclusivity language is used to increase pressure.' }
      ]
    }
  ] as MessageItem[],
  mutations: [
    {
      from: 1,
      to: 2,
      title: 'Certainty increased',
      detail: '“May announce” becomes “has confirmed”, changing a possibility into a stated fact.',
      tone: 'watch'
    },
    {
      from: 2,
      to: 3,
      title: 'Outcome claim introduced',
      detail: 'The final version adds “Guaranteed profit”, which did not exist in earlier messages.',
      tone: 'strong'
    },
    {
      from: 2,
      to: 3,
      title: 'Urgency & scarcity added',
      detail: '“Invest immediately” and “before everyone finds out” push the reader toward fast action.',
      tone: 'strong'
    }
  ] as Mutation[],
  signals: [
    { label: 'Semantic relatedness', value: '81%', caption: 'Messages discuss the same underlying topic', tone: 'neutral' as SignalTone },
    { label: 'Certainty shift', value: 'High', caption: 'Reported → asserted → absolute', tone: 'strong' as SignalTone },
    { label: 'Urgency language', value: 'Present', caption: 'Action pressure appears in the final version', tone: 'watch' as SignalTone },
    { label: 'Guaranteed outcome', value: 'Present', caption: 'A guaranteed-profit phrase is introduced', tone: 'strong' as SignalTone }
  ],
  explanation: {
    en: 'The first message is cautious and frames the information as a possibility. The second version removes that uncertainty and presents the project as confirmed. The third version goes further by introducing a guaranteed financial outcome, urgency, and exclusivity. EchoTrap is identifying changes in language and framing; it is not proving whether the underlying claim is true or false.',
    hi: 'पहले संदेश में जानकारी को संभावना के रूप में रखा गया है। दूसरे संदेश में वही बात अधिक निश्चित तरीके से “कन्फर्म” बताई गई है। तीसरे संदेश में गारंटीड लाभ, तुरंत कार्रवाई और सीमित अवसर जैसी भाषा जोड़ दी गई है। EchoTrap केवल भाषा और दावे में आए बदलाव दिखाता है; यह अपने-आप यह साबित नहीं करता कि मूल दावा सही है या गलत।'
  },
  safety: {
    en: [
      'Pause before acting on messages that combine certainty with urgency.',
      'Verify important claims independently using appropriate official sources.',
      'Do not treat a forwarded message or repeated claim as evidence by itself.'
    ],
    hi: [
      'ऐसे संदेशों पर तुरंत कार्रवाई न करें जिनमें बहुत ज़्यादा निश्चितता और जल्दी करने का दबाव हो।',
      'महत्वपूर्ण दावों को उपयुक्त आधिकारिक स्रोतों से स्वतंत्र रूप से सत्यापित करें।',
      'सिर्फ़ फ़ॉरवर्ड किए गए या बार-बार दोहराए गए संदेश को प्रमाण न मानें।'
    ]
  },
  diagnostics: {
    averageSimilarity: 81,
    strongestSignal: 'certainty and urgency escalation',
    certaintyShift: 'increased',
    urgencyShift: 'increased',
    modelMode: 'lexical fallback + mutation heuristics',
    rawPairs: [
      {
        message_index: 1,
        certainty_change: 'INCREASED',
        urgency_change: 'UNCHANGED',
        semantic_similarity: 0.81,
        added_claims: [],
        persuasion_indicators: ['has confirmed']
      },
      {
        message_index: 2,
        certainty_change: 'INCREASED',
        urgency_change: 'INCREASED',
        semantic_similarity: 0.79,
        added_claims: ['Guaranteed profit'],
        persuasion_indicators: ['Guaranteed profit', 'invest immediately']
      }
    ]
  }
}
