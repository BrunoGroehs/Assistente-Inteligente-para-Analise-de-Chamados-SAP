import { useEffect, useRef, useState, type FormEvent } from 'react'
import { ArrowUp, LoaderCircle, MessageSquarePlus, RefreshCw, Ticket, X, FileText } from 'lucide-react'
import { api as defaultApi, ApiError, type Api } from './api'
import { ApprovalCard, CasePicker, Markdown, MessageDetails } from './components'
import { CorrectionCard } from './CorrectionCard'
import type { Snapshot, CorrectionValues } from './types'

const empty: Snapshot = { cases: [], messages: [], proposals: [] }
const chatStorage = 'sap.active-chat'
const attachmentStorage = 'sap.attached-case'

export default function App({ api = defaultApi }: { api?: Api }) {
  const [view, setView] = useState<Snapshot>(empty)
  const [chat, setChat] = useState(() => sessionStorage.getItem(chatStorage) || 'initial')
  const activeChat = useRef(chat)
  const [attached, setAttached] = useState<string | null>(() => sessionStorage.getItem(attachmentStorage))
  const [ready, setReady] = useState(false), [login, setLogin] = useState(false), [code, setCode] = useState('')
  const [error, setError] = useState(''), [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false), [deciding, setDeciding] = useState(false)
  const [progress, setProgress] = useState(''), [picker, setPicker] = useState(false), [pickerDetails, setPickerDetails] = useState(false)
  const [clock, setClock] = useState(Date.now()), [offset, setOffset] = useState(0)
  const end = useRef<HTMLDivElement>(null), input = useRef<HTMLTextAreaElement>(null)
  const attach = (id: string | null) => {
    setAttached(id); setPicker(false)
    if (id) sessionStorage.setItem(attachmentStorage, id); else sessionStorage.removeItem(attachmentStorage)
    input.current?.focus()
  }
  const load = async (target = activeChat.current) => {
    const snapshot = await api.snapshot(target)
    if (activeChat.current === target) {
      setView(snapshot)
      if (snapshot.server_time) setOffset(Date.parse(snapshot.server_time) - Date.now())
    }
    return snapshot
  }
  useEffect(() => {
    let mounted = true
    const bootstrap = async () => {
      const configuration = await api.config()
      try { await api.session() }
      catch (cause) {
        if (!(cause instanceof ApiError) || cause.status !== 401) throw cause
        if (configuration.requires_access_code) { if (mounted) setLogin(true); return }
        await api.login()
        sessionStorage.removeItem(chatStorage); sessionStorage.removeItem(attachmentStorage)
        activeChat.current = 'initial'; if (mounted) { setChat('initial'); setAttached(null) }
      }
      const snapshot = await api.snapshot(activeChat.current)
      if (mounted) {
        setView(snapshot); setReady(true)
        if (snapshot.server_time) setOffset(Date.parse(snapshot.server_time) - Date.now())
      }
    }
    bootstrap().catch(cause => { if (mounted) setError(cause instanceof Error ? cause.message : 'Não foi possível abrir o aplicativo.') })
    return () => { mounted = false }
  }, [api])
  useEffect(() => {
    const waiting = () => view.proposals.some(item => item.state === 'pendente' && Date.parse(item.expires_at) > Date.now() + offset) ||
      view.messages.some(item => item.correction && !item.proposal_id && Date.parse(item.correction.expires_at) > Date.now() + offset)
    if (!waiting()) return
    setClock(Date.now())
    const timer = setInterval(() => { setClock(Date.now()); if (!waiting()) clearInterval(timer) }, 1000)
    return () => clearInterval(timer)
  }, [view.proposals, view.messages, offset])
  useEffect(() => { end.current?.scrollIntoView({ block: 'end', behavior: 'smooth' }) }, [view.messages, progress])
  const current = view.cases.find(item => item.id === attached)
  const pending = view.proposals.some(item => item.ticket === attached && item.state === 'pendente' && Date.parse(item.expires_at) > clock + offset)
  const failure = (cause: unknown) => setError(cause instanceof Error ? cause.message : 'Não foi possível concluir a solicitação.')

  async function loginSubmit(event: FormEvent) {
    event.preventDefault(); setError('')
    try {
      await api.login(code); setCode(''); setLogin(false); activeChat.current = 'initial'; setChat('initial')
      sessionStorage.removeItem(chatStorage); attach(null); await load('initial'); setReady(true)
    } catch (cause) { failure(cause) }
  }
  async function newChat() {
    setError('')
    try {
      const result = await api.newChat()
      activeChat.current = result.chat_id; setChat(result.chat_id); sessionStorage.setItem(chatStorage, result.chat_id)
      setDraft(''); setProgress(''); attach(null)
      setView(previous => ({ ...previous, messages: [], proposals: [] }))
      await load(result.chat_id)
    } catch (cause) { failure(cause) }
  }
  async function send(message = draft) {
    const value = message.trim()
    if (!value || sending || pending) return
    const target = activeChat.current, caseId = current?.id || null
    setDraft(''); setError(''); setSending(true); setProgress('Consultando fontes…')
    const optimistic = { id: crypto.randomUUID(), role: 'user', content: value, attachment: current || null,
      error: false, details: { facts: [], hypotheses: [], missing_information: [], next_steps: [], sources: [],
        consulted_sources: [], policies: [], transactions: [], steps: [] } }
    setView(previous => ({ ...previous, messages: [...previous.messages, optimistic] }))
    try {
      await api.send(target, value, caseId, crypto.randomUUID(), event => {
        if (activeChat.current === target && event.type === 'progress') setProgress(event.label || 'Analisando…')
      })
    } catch (cause) { if (activeChat.current === target) failure(cause) }
    finally {
      try { await load(target) } catch (cause) { if (activeChat.current === target) failure(cause) }
      setSending(false); if (activeChat.current === target) setProgress('')
    }
  }
  async function decide(id: string, approve: boolean) {
    setDeciding(true); setError('')
    const target = activeChat.current
    try { await api.decide(target, id, approve); await load(target) }
    catch (cause) { failure(cause) }
    finally { setDeciding(false) }
  }
  async function prepareCorrection(id: string, values: CorrectionValues) {
    if (deciding || sending || pending) return
    setDeciding(true); setError('')
    const target = activeChat.current
    try { await api.prepareCorrection(target, id, values); await load(target) }
    catch (cause) { if (activeChat.current === target) failure(cause) }
    finally { setDeciding(false) }
  }
  const latestForCase = new Map(view.messages.filter(item => item.role === 'assistant' && item.attachment)
    .map(item => [item.attachment!.id, item.id]))
  const usedProposals = new Set(view.messages.map(message => message.proposal_id))
  const approval = (id: string) => {
    const proposal = view.proposals.find(item => item.id === id)
    return proposal && <ApprovalCard key={id} proposal={proposal} attached={attached} cases={view.cases}
      busy={deciding} now={clock + offset} onAttach={attach} onDecide={decide} />
  }

  if (login) return <main className="access-page"><form className="access-form" onSubmit={loginSubmit}>
    <span className="brand-mark">S</span><h1>Assistente SAP</h1><p className="muted">Entre na demonstração privada.</p>
    <label>Código de acesso<input type="password" value={code} autoComplete="current-password" required
      onChange={event => setCode(event.target.value)} /></label>
    {error && <p className="error" role="alert">{error}</p>}<button className="primary" type="submit">Entrar</button>
  </form></main>

  return <div className="app-shell">
    <header className="app-header"><a className="brand" href="/" aria-label="Assistente SAP"><span className="brand-mark">S</span>
      <span>Assistente SAP<small>MM · Ambiente simulado</small></span></a>
      <button className="secondary new-chat" onClick={newChat} disabled={!ready}><MessageSquarePlus size={17} />Novo chat</button>
    </header>
    <main className="conversation" aria-label="Conversa">
      {!ready && !error && <div className="loading"><LoaderCircle size={21} className="spin" />Preparando a conversa…</div>}
      {ready && !view.messages.length && <div className="welcome"><div className="welcome-mark"><Ticket size={27} strokeWidth={1.5} /></div>
        <h1>Como posso ajudar?</h1><p>Pergunte sobre SAP MM ou anexe um chamado<br className="desktop-break" /> para analisar o caso com contexto.</p></div>}
      {view.messages.map(message => <article key={message.id} className={`message ${message.role}`}>
        {message.role === 'user' && message.attachment && <span className="message-attachment"><Ticket size={13} />{message.attachment.reference}</span>}
        <div className={message.error ? 'error' : 'message-text'}><Markdown message={message.role === 'assistant' ? message : undefined}>{message.content}</Markdown></div>
        {message.role === 'assistant' && <MessageDetails message={message} />}
        {message.proposal_id && approval(message.proposal_id)}
        {message.correction && !message.proposal_id && latestForCase.get(message.correction.ticket) === message.id &&
          <CorrectionCard correction={message.correction} attached={attached} busy={deciding || sending || pending} now={clock + offset}
            onAttach={attach} onPrepare={values => prepareCorrection(message.id, values)} />}
      </article>)}
      {view.proposals.filter(item => !usedProposals.has(item.id)).map(item => approval(item.id))}
      {progress && <div className="progress" role="status"><LoaderCircle size={16} className="spin" />{progress}</div>}
      <div ref={end} />
    </main>
    <div className="composer-wrap">
      {error && <div className="error-banner" role="alert"><span>{error}</span><button className="icon-button" aria-label="Fechar aviso" onClick={() => setError('')}><X size={16} /></button></div>}
      {pending && <p className="pending-hint">Decida a solicitação deste chamado ou remova o anexo para perguntar no modo geral.</p>}
      <form className="composer" onSubmit={event => { event.preventDefault(); void send() }}>
        {current && <div className="attachment-chip"><button type="button" onClick={() => { setPickerDetails(true); setPicker(true) }}>
          <FileText size={19} /><span><strong>{current.reference}</strong><small>{current.title}</small></span></button>
          <button type="button" className="icon-button" aria-label="Remover anexo" onClick={() => attach(null)}><X size={17} /></button></div>}
        <textarea ref={input} aria-label="Mensagem" placeholder={current ? 'Pergunte sobre o chamado…' : 'Faça uma pergunta sobre SAP MM…'}
          value={draft} maxLength={6000} rows={2} disabled={!ready || pending} onChange={event => setDraft(event.target.value)}
          onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); void send() } }} />
        <div className="composer-toolbar"><div>
          <button type="button" className="text-button" disabled={!ready} onClick={() => { setPickerDetails(false); setPicker(true) }}><Ticket size={17} />Chamados</button>
          <button type="button" className="icon-button" aria-label="Atualizar conversa" disabled={!ready || sending}
            onClick={() => { setError(''); load().catch(failure) }}><RefreshCw size={16} /></button>
          {current && !view.messages.some(message => message.attachment?.id === current.id) && <button type="button"
            className="text-button analyze" disabled={sending || pending} onClick={() => void send(current.description)}>Analisar chamado</button>}
        </div><button type="submit" className="send-button" aria-label="Enviar mensagem" disabled={!ready || !draft.trim() || sending || pending}>
          {sending ? <LoaderCircle size={19} className="spin" /> : <ArrowUp size={20} />}</button></div>
      </form>
      <p className="footer-note">Respostas com fontes verificadas. Alterações exigem sua aprovação.</p>
    </div>
    <CasePicker cases={view.cases} attached={attached} open={picker} initiallyDetails={pickerDetails}
      onClose={() => setPicker(false)} onAttach={attach} />
    <span className="sr-only">Conversa {chat === 'initial' ? 'inicial' : 'nova'}</span>
  </div>
}
