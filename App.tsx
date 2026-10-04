import { useMemo, useState, type ReactNode } from 'react'
import { mockAnalysis, sampleMessages, type MessageItem } from './mockAnalysis'

type View = 'home' | 'analyzer' | 'processing' | 'results'
type Lang = 'en' | 'hi'

const Icon = ({ name, size = 18 }: { name: string; size?: number }) => {
  const common = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const }
  const paths: Record<string, ReactNode> = {
    arrow: <><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></>,
    plus: <><path d="M12 5v14"/><path d="M5 12h14"/></>,
    x: <><path d="m6 6 12 12"/><path d="m18 6-12 12"/></>,
    spark: <><path d="m12 3 1.4 4.1L17.5 8.5l-4.1 1.4L12 14l-1.4-4.1-4.1-1.4 4.1-1.4L12 3Z"/><path d="m18.5 14 .7 2.3 2.3.7-2.3.8-.7 2.2-.8-2.2-2.2-.8 2.2-.7.8-2.3Z"/></>,
    shield: <><path d="M12 3 5.5 5.7v5.7c0 4.1 2.7 7.7 6.5 9.1 3.8-1.4 6.5-5 6.5-9.1V5.7L12 3Z"/><path d="m9 12 2 2 4-4"/></>,
    language: <><circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18"/><path d="M12 3a14 14 0 0 0 0 18"/></>,
    info: <><circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
    refresh: <><path d="M20 7v5h-5"/><path d="M4 17v-5h5"/><path d="M6.1 8.2A7 7 0 0 1 18.7 7L20 12"/><path d="M4 12l1.3 5A7 7 0 0 0 17.9 15.8"/></>,
    flag: <><path d="M5 21V4"/><path d="M5 5h10l-1.5 3L15 11H5"/></>,
  }
  return <svg {...common} aria-hidden="true">{paths[name]}</svg>
}

const Logo = () => (
  <div className="brand" aria-label="EchoTrap home">
    <div className="brand-mark"><span></span><span></span><span></span></div>
    <div>
      <strong>EchoTrap</strong>
      <small>Claim mutation intelligence</small>
    </div>
  </div>
)

const Header = ({ onHome, onAnalyze, lang, setLang }: { onHome: () => void; onAnalyze: () => void; lang: Lang; setLang: (l: Lang) => void }) => (
  <header className="topbar">
    <button className="logo-button" onClick={onHome}><Logo /></button>
    <nav>
      <button className="nav-link" onClick={onAnalyze}>Analyze messages</button>
      <button className="lang-toggle" onClick={() => setLang(lang === 'en' ? 'hi' : 'en')} aria-label="Switch explanation language">
        <Icon name="language" size={16}/>{lang === 'en' ? 'EN' : 'हिं'}
      </button>
    </nav>
  </header>
)

function Home({ start }: { start: () => void }) {
  return (
    <main className="home-page">
      <section className="hero-shell">
        <div className="hero-copy">
          <div className="eyebrow"><span className="eyebrow-dot"></span>Investor language intelligence</div>
          <h1>See what changed.<br/><em>Not just what was said.</em></h1>
          <p className="hero-lede">EchoTrap compares related financial messages and reveals how certainty, urgency and outcome claims change from one version to the next.</p>
          <div className="hero-actions">
            <button className="primary-button" onClick={start}>Analyze message sequence <Icon name="arrow"/></button>
            <div className="privacy-note"><Icon name="shield" size={16}/><span>Mock prototype · no message data is uploaded</span></div>
          </div>
        </div>

        <div className="hero-visual" aria-label="Example message mutation">
          <div className="case-header">
            <div><small>EXAMPLE SEQUENCE</small><strong>How one claim changes</strong></div>
            <span className="case-id">ET-024</span>
          </div>
          <div className="mini-thread">
            <div className="mini-message">
              <span className="message-index">01</span>
              <p>ABC Ltd <mark className="mark-soft">may announce</mark> a new project next quarter.</p>
              <span className="certainty-chip neutral">Reported</span>
            </div>
            <div className="thread-link"><span></span><b>certainty ↑</b></div>
            <div className="mini-message">
              <span className="message-index">02</span>
              <p>ABC Ltd <mark className="mark-watch">has confirmed</mark> a major new project.</p>
              <span className="certainty-chip watch">Asserted</span>
            </div>
            <div className="thread-link danger"><span></span><b>outcome + urgency added</b></div>
            <div className="mini-message active">
              <span className="message-index">03</span>
              <p><mark className="mark-danger">Guaranteed profit</mark> — <mark className="mark-danger">invest immediately</mark>.</p>
              <span className="certainty-chip strong">Absolute</span>
            </div>
          </div>
          <div className="hero-visual-footer"><Icon name="info" size={16}/> Linguistic change ≠ proof of fraud or message propagation</div>
        </div>
      </section>

      <section className="principles">
        <div className="section-heading"><span>WHY ECHOTRAP</span><h2>Designed for the moment a claim starts drifting.</h2></div>
        <div className="principle-grid">
          <article><div className="principle-number">01</div><h3>Compare meaning, not keywords</h3><p>Spot when a cautious statement becomes certain, promotional or absolute.</p></article>
          <article><div className="principle-number">02</div><h3>Show the exact language shift</h3><p>Highlight the phrase that introduced urgency, scarcity or guaranteed outcomes.</p></article>
          <article><div className="principle-number">03</div><h3>Explain without overclaiming</h3><p>Surface warning signals while keeping uncertainty and verification boundaries visible.</p></article>
        </div>
      </section>
    </main>
  )
}

function Analyzer({ messages, setMessages, onAnalyze, loadSample }: { messages: string[]; setMessages: (v: string[]) => void; onAnalyze: () => void; loadSample: () => void }) {
  const canAnalyze = messages.length >= 2 && messages.every(m => m.trim().length >= 12)

  const update = (i: number, value: string) => setMessages(messages.map((m, idx) => idx === i ? value : m))
  const add = () => messages.length < 5 && setMessages([...messages, ''])
  const remove = (i: number) => messages.length > 2 && setMessages(messages.filter((_, idx) => idx !== i))

  return (
    <main className="analyzer-page page-wrap">
      <div className="page-kicker">NEW ANALYSIS</div>
      <div className="analyzer-head">
        <div><h1>Compare a message sequence</h1><p>Paste 2–5 related versions in the order you encountered them. EchoTrap will compare how the language changes.</p></div>
        <button className="secondary-button" onClick={loadSample}><Icon name="spark" size={17}/>Load demo sequence</button>
      </div>

      <div className="analyzer-layout">
        <section className="composer-panel">
          <div className="composer-title"><span>MESSAGE SEQUENCE</span><span>{messages.length}/5</span></div>
          <div className="message-stack">
            {messages.map((message, i) => (
              <div className="input-card" key={i}>
                <div className="input-card-top">
                  <div><span className="input-number">{String(i + 1).padStart(2, '0')}</span><strong>{i === 0 ? 'Earliest version' : i === messages.length - 1 ? 'Latest version' : `Version ${i + 1}`}</strong></div>
                  {messages.length > 2 && <button className="icon-button" onClick={() => remove(i)} aria-label={`Remove message ${i+1}`}><Icon name="x" size={16}/></button>}
                </div>
                <textarea value={message} onChange={e => update(i, e.target.value)} placeholder="Paste the financial message exactly as you received it…" maxLength={500}/>
                <div className="input-meta"><span>{message.length}/500</span><span>{message.trim().length > 0 && message.trim().length < 12 ? 'Add a little more context' : 'Text only'}</span></div>
              </div>
            ))}
          </div>
          {messages.length < 5 && <button className="add-message" onClick={add}><Icon name="plus" size={17}/>Add another version</button>}
        </section>

        <aside className="analysis-sidebar">
          <div className="sidebar-card dark-card">
            <span className="sidebar-label">ANALYSIS MODE</span>
            <h3>Claim mutation</h3>
            <p>Compares semantic continuity, certainty shifts and persuasion signals across supplied messages.</p>
            <div className="mode-list">
              <span><Icon name="check" size={15}/>Semantic relatedness</span>
              <span><Icon name="check" size={15}/>Certainty & framing shifts</span>
              <span><Icon name="check" size={15}/>Urgency & scarcity cues</span>
              <span><Icon name="check" size={15}/>Guaranteed-outcome language</span>
            </div>
          </div>
          <div className="sidebar-card privacy-card">
            <Icon name="shield" size={20}/>
            <div><strong>Prototype privacy mode</strong><p>This demo runs on local mock data. Nothing you type is transmitted or stored.</p></div>
          </div>
          <button className="primary-button analyze-button" onClick={onAnalyze} disabled={!canAnalyze}>Run mutation analysis <Icon name="arrow"/></button>
          {!canAnalyze && <p className="helper-text">Add at least two messages with enough context to continue.</p>}
        </aside>
      </div>
    </main>
  )
}

function Processing() {
  const steps = ['Reading supplied versions', 'Comparing semantic continuity', 'Locating certainty shifts', 'Scanning persuasion language', 'Building explanation']
  return (
    <main className="processing-page page-wrap">
      <div className="processing-card">
        <div className="scan-visual"><div className="scan-line"></div><span>ET</span></div>
        <div className="processing-copy">
          <div className="page-kicker">ANALYSIS IN PROGRESS</div>
          <h1>Tracing how the claim changed</h1>
          <p>EchoTrap is comparing the supplied versions, not verifying market outcomes.</p>
          <div className="processing-steps">
            {steps.map((step, i) => <div key={step} className={`processing-step ${i < 3 ? 'done' : i === 3 ? 'active' : ''}`}><span>{i < 3 ? <Icon name="check" size={15}/> : String(i+1).padStart(2,'0')}</span>{step}</div>)}
          </div>
        </div>
      </div>
    </main>
  )
}

function HighlightedText({ item }: { item: MessageItem }) {
  const ordered = [...item.highlights].sort((a,b) => item.text.indexOf(a.text) - item.text.indexOf(b.text))
  let cursor = 0
  const parts: ReactNode[] = []
  ordered.forEach((h, idx) => {
    const start = item.text.indexOf(h.text, cursor)
    if (start < 0) return
    if (start > cursor) parts.push(<span key={`t-${idx}`}>{item.text.slice(cursor, start)}</span>)
    parts.push(<mark key={`h-${idx}`} className={`highlight ${h.type}`} title={h.note}>{item.text.slice(start, start + h.text.length)}</mark>)
    cursor = start + h.text.length
  })
  if (cursor < item.text.length) parts.push(<span key="end">{item.text.slice(cursor)}</span>)
  return <>{parts}</>
}

function Results({ lang, restart }: { lang: Lang; restart: () => void }) {
  const data = mockAnalysis
  return (
    <main className="results-page page-wrap">
      <div className="results-topline">
        <div><div className="page-kicker">ANALYSIS COMPLETE · ET-024</div><h1>Claim evolution report</h1></div>
        <button className="secondary-button" onClick={restart}><Icon name="refresh" size={16}/>New analysis</button>
      </div>

      <section className="status-banner">
        <div className="status-icon"><Icon name="flag"/></div>
        <div><span>LANGUAGE-RISK SUMMARY</span><h2>{data.status}</h2><p>{data.summary}</p></div>
        <div className="status-note">Interpret as warning signals,<br/>not a fraud verdict.</div>
      </section>

      <section className="report-section">
        <div className="section-label-row"><span>01 · CLAIM EVOLUTION</span><small>Hover highlighted phrases for context</small></div>
        <div className="timeline-grid">
          {data.messages.map((msg, i) => (
            <div className="timeline-unit" key={msg.id}>
              <article className={`message-analysis ${i === data.messages.length - 1 ? 'final' : ''}`}>
                <div className="analysis-card-head"><span>MESSAGE {String(msg.id).padStart(2,'0')}</span><span className={`certainty-chip ${msg.certainty === 'Reported' ? 'neutral' : msg.certainty === 'Asserted' ? 'watch' : 'strong'}`}>{msg.certainty}</span></div>
                <p><HighlightedText item={msg}/></p>
                <div className="signal-tags">{msg.highlights.map((h, idx) => <span key={idx}>{h.type.replace('-', ' ')}</span>)}</div>
              </article>
              {i < data.messages.length - 1 && <div className="timeline-arrow"><span></span><Icon name="arrow" size={17}/></div>}
            </div>
          ))}
        </div>

        <div className="mutation-list">
          {data.mutations.map((m, i) => (
            <article className={`mutation-row tone-${m.tone}`} key={i}>
              <div className="mutation-route"><span>{m.from}</span><b>→</b><span>{m.to}</span></div>
              <div><h3>{m.title}</h3><p>{m.detail}</p></div>
              <span className="mutation-status">{m.tone === 'strong' ? 'High-salience shift' : 'Meaning shift'}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="report-section signals-section">
        <div className="section-label-row"><span>02 · LANGUAGE SIGNALS</span><small>Descriptive indicators only</small></div>
        <div className="signal-grid">
          {data.signals.map((signal, i) => (
            <article className={`signal-card tone-${signal.tone}`} key={i}>
              <span>{signal.label}</span><strong>{signal.value}</strong><p>{signal.caption}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="explanation-grid">
        <article className="explanation-card">
          <div className="section-label-row"><span>03 · PLAIN-LANGUAGE EXPLANATION</span><small>{lang === 'en' ? 'English' : 'हिंदी'}</small></div>
          <p className={lang === 'hi' ? 'hindi-copy' : ''}>{data.explanation[lang]}</p>
          <div className="boundary-note"><Icon name="info" size={17}/><span>EchoTrap compares language supplied by the user. It does not establish the truth of the underlying claim or prove that one message caused another.</span></div>
        </article>

        <article className="safety-card">
          <div className="section-label-row"><span>04 · SAFER NEXT STEPS</span><Icon name="shield" size={18}/></div>
          <h2>{lang === 'en' ? 'Before acting on the claim' : 'दावे पर कार्रवाई करने से पहले'}</h2>
          <div className="safety-list">
            {data.safety[lang].map((s, i) => <div key={i}><span>{String(i+1).padStart(2,'0')}</span><p>{s}</p></div>)}
          </div>
        </article>
      </section>

      <div className="report-footer"><span>EchoTrap prototype · mock analysis for SANGYAN demo</span><span>Investor protection, not investment advice</span></div>
    </main>
  )
}

export default function App() {
  const [view, setView] = useState<View>('home')
  const [lang, setLang] = useState<Lang>('en')
  const [messages, setMessages] = useState<string[]>(['', '', ''])

  const headerProps = useMemo(() => ({
    onHome: () => setView('home'),
    onAnalyze: () => setView('analyzer'),
    lang,
    setLang
  }), [lang])

  const loadSample = () => setMessages([...sampleMessages])
  const runAnalysis = () => {
    setView('processing')
    window.setTimeout(() => setView('results'), 1850)
  }

  return (
    <div className="app-shell">
      <Header {...headerProps}/>
      {view === 'home' && <Home start={() => { loadSample(); setView('analyzer') }}/>} 
      {view === 'analyzer' && <Analyzer messages={messages} setMessages={setMessages} onAnalyze={runAnalysis} loadSample={loadSample}/>} 
      {view === 'processing' && <Processing/>}
      {view === 'results' && <Results lang={lang} restart={() => setView('analyzer')}/>} 
    </div>
  )
}
