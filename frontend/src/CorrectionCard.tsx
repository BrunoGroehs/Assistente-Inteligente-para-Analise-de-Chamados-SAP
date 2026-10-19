import { useState } from 'react'
import { Wrench, Paperclip } from 'lucide-react'
import type { Correction, CorrectionValues } from './types'

export function CorrectionCard({ correction, attached, busy, now, onAttach, onPrepare }: {
  correction: Correction; attached: string | null; busy: boolean; now: number;
  onAttach: (id: string) => void; onPrepare: (values: CorrectionValues) => Promise<void>;
}) {
  const [open, setOpen] = useState(false)
  const [quantity, setQuantity] = useState(''), [date, setDate] = useState(''), [status, setStatus] = useState('')
  const expired = Date.parse(correction.expires_at) <= now
  const receipt = correction.operation === 'registrar_recebimento_simulado'
  const valid = receipt ? quantity !== '' && Number(quantity) > 0 && Number(quantity) <= Number(correction.max_quantity) && !!date : !!status
  return <section className="approval-card correction-card" aria-label="Correção disponível">
    <span className="eyebrow">SIM-{correction.ticket} · Correção no simulador</span>
    <h3>Quer preparar esta correção para aprovação?</h3>
    <p>{receipt ? `Recebimento no pedido ${correction.purchase_order}, item ${correction.item}. Informe a quantidade correta e a data de lançamento.`
      : 'Selecione a situação desejada para o chamado.'}</p>
    {expired ? <p className="muted small">Esta sugestão venceu. Peça uma nova análise.</p>
      : attached !== correction.ticket ? <button className="secondary" onClick={() => onAttach(correction.ticket)}>
        <Paperclip size={15} />Anexar SIM-{correction.ticket}</button>
      : !open ? <button className="secondary" disabled={busy} onClick={() => setOpen(true)}><Wrench size={15} />Preparar correção</button>
      : <form className="correction-form" onSubmit={event => { event.preventDefault(); if (valid && !busy) void onPrepare(
        receipt ? { quantity, posting_date: date } : { status }) }}>
        {receipt ? <><label>Quantidade correta ({correction.unit}, máximo {correction.max_quantity})
          <input type="number" min="0.001" max={correction.max_quantity} step="0.001" required value={quantity}
            onChange={event => setQuantity(event.target.value)} /></label>
          <label>Data de lançamento<input type="date" required value={date} onChange={event => setDate(event.target.value)} /></label></>
          : <label>Situação desejada<select required value={status} onChange={event => setStatus(event.target.value)}>
            <option value="">Selecione</option><option value="em_validacao_humana">Em validação humana</option><option value="resolvido">Resolvido</option>
          </select></label>}
        <p className="muted small">Preparar não executa a ação. Você revisará os dados e decidirá pelos botões Sim/Não.</p>
        <button className="primary" type="submit" disabled={busy || !valid}>{busy ? 'Preparando…' : 'Revisar ação'}</button>
      </form>}
  </section>
}
