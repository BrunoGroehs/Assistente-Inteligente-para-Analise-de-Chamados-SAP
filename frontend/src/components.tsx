import { useEffect, useRef, useState, type ReactNode } from 'react'
import ReactMarkdown from 'react-markdown'
import { ChevronLeft, Search, Ticket, X, Paperclip, ExternalLink } from 'lucide-react'
import type { Case, Message, Proposal, Source, CorrectionValues } from './types'
import { citationPlugin, citationTarget } from './citations'

export const statuses: Record<string, string> = {
  aberto: 'Aberto', em_validacao_humana: 'Em validação humana', resolvido: 'Resolvido',
  pendente: 'Aguardando aprovação', executada: 'Executada', recusada: 'Recusada',
  expirada: 'Expirada', invalidada: 'Invalidada', falhou: 'Falhou',
}
const missing = 'Não informado'
export const normalized = (value: string) => value.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase()

function SourceLink({ href, children }: { href?: string; children: ReactNode }) {
  const local = href?.startsWith('#source-')
  return <a href={href} target={local ? undefined : '_blank'} rel={local ? undefined : 'noopener noreferrer'}
    onClick={event => {
      if (!local) return
      event.preventDefault()
      const target = document.getElementById(href!.slice(1))
      const details = target?.closest('details')
      if (details) details.open = true
      target?.scrollIntoView({ block: 'nearest' })
    }}>{children}</a>
}

export function Markdown({ children, message }: { children: string; message?: Message }) {
  return <ReactMarkdown skipHtml remarkPlugins={[citationPlugin(message)]} components={{
    a: ({ children, href }) => <SourceLink href={href}>{typeof children === 'string' && /^\d+$/.test(children) ? `[${children}]` : children}</SourceLink>,
    img: ({ alt }) => <span>{alt}</span>,
  }}>{children}</ReactMarkdown>
}

function Field({ label, children }: { label: string; children?: ReactNode }) {
  return <div className="field"><dt>{label}</dt><dd>{children || missing}</dd></div>
}

export function CaseDetails({ item }: { item: Case }) {
  const support = item.support || {}
  const order = item.order
  return <div className="case-details">
    <span className="eyebrow">{item.reference} · Dados fictícios</span>
    <h2>{item.title}</h2><p>{item.description}</p>
    <dl className="field-grid">
      <Field label="Situação local">{statuses[item.status]}</Field>
      <Field label="Prioridade">{item.priority_label}</Field>
      <Field label="Produto">{support.product}</Field><Field label="Versão / release">{support.product_version}</Field>
      <Field label="Sistema">{support.system_id}</Field><Field label="Mandante">{support.client}</Field>
      <Field label="Ambiente">{support.system_role}</Field><Field label="Aplicativo">{support.application}</Field>
      <Field label="Componente sugerido">{support.component}</Field><Field label="Solicitante">{support.reporter}</Field>
      <Field label="Empresa">{support.customer}</Field>
      <Field label="Ocorrência informada">{support.reported_at ? new Date(support.reported_at).toLocaleString('pt-BR') : missing}</Field>
      <Field label="Case SAP">{support.sap_case_number || 'Não enviado ao SAP for Me'}</Field>
    </dl>
    <section><h3>Impacto no negócio</h3><p>{support.business_impact || missing}</p></section>
    <section><h3>Resultado esperado pelo solicitante</h3><p>{support.expected_result || missing}</p></section>
    <section><h3>Resultado relatado na abertura</h3><p>{support.actual_result || missing}</p></section>
    <section><h3>Mensagem de erro</h3><p>{support.error_message || missing}</p></section>
    <section><h3>Passos de reprodução</h3>{support.steps_to_reproduce?.length
      ? <ol>{support.steps_to_reproduce.map((step, i) => <li key={i}>{step}</li>)}</ol> : <p>{missing}</p>}</section>
    <section><h3>Ações já tentadas</h3><p>{support.actions_taken?.join(' · ') || missing}</p></section>
    <section><h3>Pedido e quantidades atuais no simulador</h3>{order ? <>
      <p>Pedido {order.purchase_order} · Item {order.item} · {order.material}</p>
      <p>Centro {order.plant} · Depósito {order.storage_location} · Unidade {order.unit}</p>
      <p>Pedido: {order.ordered} · Recebido: {order.received}</p>
      <p>Entrega concluída: {order.delivery_completed ? 'Sim' : 'Não'}</p>
    </> : <p>{missing}</p>}</section>
    <p className="muted">Anexos: {support.attachments?.join(', ') || 'Nenhum anexo'}</p>
  </div>
}

export function CasePicker({ cases, attached, open, onClose, onAttach, initiallyDetails = false }: {
  cases: Case[]; attached: string | null; open: boolean; initiallyDetails?: boolean;
  onClose: () => void; onAttach: (id: string) => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null)
  const [query, setQuery] = useState(''), [priority, setPriority] = useState('all')
  const [selected, setSelected] = useState<string | null>(null), [details, setDetails] = useState(false)
  useEffect(() => {
    if (open) {
      setQuery(''); setPriority('all'); setSelected(attached || cases[0]?.id || null); setDetails(initiallyDetails)
      if (!dialog.current?.open) dialog.current?.showModal()
    } else dialog.current?.close()
    // Opening is the boundary: filtering does not reset the candidate or current chat attachment.
  }, [open]) // eslint-disable-line react-hooks/exhaustive-deps
  const filtered = cases.filter(item => normalized(JSON.stringify(item)).includes(normalized(query)) &&
    (priority === 'all' || (priority === 'missing' ? !item.support?.priority : item.support?.priority === priority)))
  const candidate = filtered.find(item => item.id === selected) || filtered[0]
  return <dialog ref={dialog} className="case-modal" aria-labelledby="cases-title"
    onCancel={event => { event.preventDefault(); onClose() }}
    onClick={event => { if (event.target === event.currentTarget) onClose() }}>
    <div className="modal-head"><h2 id="cases-title"><Ticket size={20} />Chamados</h2>
      <button className="icon-button" aria-label="Fechar chamados" onClick={onClose}><X size={20} /></button></div>
    <div className="modal-scroll">
      {details && candidate ? <>
        <button className="text-button" onClick={() => setDetails(false)}><ChevronLeft size={16} />Todos os chamados</button>
        <CaseDetails item={candidate} />
      </> : <>
        <div className="case-filters"><label className="search-input"><Search size={17} />
          <input aria-label="Buscar chamado" placeholder="Buscar por chamado, pedido, material…" value={query}
            onChange={event => setQuery(event.target.value)} /></label>
          <select aria-label="Prioridade" value={priority} onChange={event => setPriority(event.target.value)}>
            <option value="all">Todas as prioridades</option><option value="1">1 · Muito alta</option>
            <option value="2">2 · Alta</option><option value="3">3 · Média</option><option value="4">4 · Baixa</option>
            <option value="missing">Não informada</option>
          </select></div>
        <p className="muted small">{filtered.length} de {cases.length} chamados · Ambiente simulado</p>
        <div className="case-list">{filtered.map(item => <button key={item.id}
          className={`case-row ${candidate?.id === item.id ? 'selected' : ''}`}
          aria-pressed={candidate?.id === item.id} onClick={() => setSelected(item.id)}>
          <Ticket size={18} /><span><span className="case-reference">{item.reference}</span>
            <strong>{item.title}</strong><span className="muted small">{statuses[item.status]} · {item.support?.system_id || missing}</span>
          </span><span className="priority">{item.priority_label}</span>
        </button>)}</div>
        {!filtered.length && <p className="empty-search">Nenhum chamado encontrado. Ajuste a busca.</p>}
      </>}
    </div>
    <div className="modal-actions"><button className="secondary" onClick={onClose}>Cancelar</button>
      <div>{!details && <button className="secondary" disabled={!candidate} onClick={() => setDetails(true)}>Ver detalhes</button>}
        <button className="primary" disabled={!candidate} onClick={() => candidate && onAttach(candidate.id)}>
          <Paperclip size={16} />Anexar ao chat</button></div></div>
  </dialog>
}

function Sources({ items }: { items: Source[] }) {
  return <ul className="source-list">{items.map(item => <li key={item.url}>
    <a href={item.url} target="_blank" rel="noopener noreferrer">
      {item.numbers?.length ? `[${item.numbers.join(', ')}] ` : ''}{item.title}<ExternalLink size={13} /></a>
  </li>)}</ul>
}

export function MessageDetails({ message }: { message: Message }) {
  const details = message.details
  const confidence = { alta: 'Alta', media: 'Média', baixa: 'Baixa' }[details.confidence || '']
  return <details className="answer-details"><summary>Fontes e detalhes</summary><div>
    {confidence && <p className="muted">Confiança {confidence.toLowerCase()} · {details.confidence_reason}</p>}
    {!!details.facts.length && <><h4>Fatos consultados</h4><ul>{details.facts.map((fact, i) =>
      <li key={i}>{fact.text} {fact.numbers.map(number => <SourceLink key={number} href={citationTarget(message, number)}>[{number}] </SourceLink>)}</li>)}</ul></>}
    {!!details.hypotheses.length && <><h4>Hipóteses</h4><ul>{details.hypotheses.map((item, i) => <li key={i}>{item}</li>)}</ul></>}
    {!!details.missing_information.length && <><h4>Informações necessárias</h4><ul>{details.missing_information.map((item, i) => <li key={i}>{item}</li>)}</ul></>}
    {!!details.next_steps.length && <><h4>Verificações recomendadas</h4><ul>{details.next_steps.map((item, i) => <li key={i}>{item}</li>)}</ul></>}
    {!!details.sources.length && <><h4>Fontes citadas</h4><Sources items={details.sources} /></>}
    {!!details.policies.length && <><h4>Regras da simulação</h4><ul>{details.policies.map(policy =>
      <li key={policy.number} id={`source-${message.id}-${policy.number}`}>[{policy.number}] {policy.title} · Regra interna do simulador</li>)}</ul></>}
    {!!details.transactions.length && <><h4>Dados consultados</h4>{details.transactions.map((order, i) => <p key={i}>
      Pedido {order.purchase_order} · Item {order.item} · {order.material}<br />
      Pedido: {order.ordered} {order.unit} · Recebido: {order.received} {order.unit} · Saldo: {order.remaining} {order.unit}
    </p>)}</>}
    {!!details.consulted_sources.length && <><h4>Referências consultadas</h4>
      <p className="muted small">Recuperadas na busca; não usadas como fundamento da resposta.</p><Sources items={details.consulted_sources} /></>}
    {!!details.steps.length && <><h4>Etapas do atendimento</h4><ol>{details.steps.map((step, i) => <li key={i}>{step}</li>)}</ol></>}
    {details.latency_ms != null && <p className="muted small">Duração medida: {(details.latency_ms / 1000).toFixed(1)} s</p>}
  </div></details>
}

export function ApprovalCard({ proposal, attached, cases, busy, now, onAttach, onDecide }: {
  proposal: Proposal; attached: string | null; cases: Case[]; busy: boolean; now: number;
  onAttach: (id: string) => void; onDecide: (id: string, approve: boolean) => void;
}) {
  const expired = proposal.state === 'pendente' && Date.parse(proposal.expires_at) <= now
  const pending = proposal.state === 'pendente' && !expired
  const item = cases.find(item => item.id === proposal.ticket)
  const effect = proposal.effect
  return <section className={`approval-card ${pending ? 'pending' : ''}`} aria-label="Solicitação de aprovação">
    <span className="eyebrow">{item?.reference || proposal.ticket} · {statuses[expired ? 'expirada' : proposal.state]}</span>
    {pending ? <>
      <h3>{proposal.phrase}</h3>
      {effect.purchase_order ? <>
        <p>Pedido {effect.purchase_order} · Item {effect.item} · {effect.material}</p>
        <p><strong>Receber {effect.quantity} {effect.unit}</strong> · Saldo: {effect.before} → {effect.after} {effect.unit}</p>
        <p className="muted small">Centro {effect.plant} · Depósito {effect.storage_location} · Data {effect.posting_date}</p>
      </> : <p>{statuses[effect.before] || effect.before} → {statuses[effect.after] || effect.after}</p>}
      <p className="muted small">Somente no simulador · Válida até {new Date(proposal.expires_at).toLocaleTimeString('pt-BR')}</p>
      {attached === proposal.ticket ? <div className="approval-actions">
        <button className="primary" disabled={busy} onClick={() => onDecide(proposal.id, true)}>Sim, autorizar</button>
        <button className="secondary" disabled={busy} onClick={() => onDecide(proposal.id, false)}>Não, recusar</button>
      </div> : <><p className="muted small">Anexe o chamado correspondente para revisar e decidir.</p>
        <button className="secondary" onClick={() => onAttach(proposal.ticket)}><Paperclip size={15} />Anexar {item?.reference || proposal.ticket}</button></>}
    </> : <p>{expired ? 'A solicitação venceu. Peça uma nova análise.' : proposal.result.message || 'Nenhuma autorização ativa.'}
      {proposal.result.receipt_id && <span className="receipt">Documento: {proposal.result.receipt_id}</span>}</p>}
  </section>
}
