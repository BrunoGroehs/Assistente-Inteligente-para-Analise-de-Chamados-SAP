import { act, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import type { Api } from './api'
import type { Case, Message, Proposal, Snapshot } from './types'

const cases: Case[] = Array.from({ length: 8 }, (_, index) => ({
  id: `C0${index + 1}`, reference: `SIM-C0${index + 1}`, title: `Caso ${index + 1}`,
  description: `Relato do pedido 450000100${index + 1}`, status: 'aberto', priority_label: index === 4 ? 'Não informado' : '4 · Baixa',
  support: { system_id: 'QAS', component: 'MM-IM-GR-PO', priority: index === 4 ? undefined : '4',
    business_impact: 'Impacto informado pelo solicitante.' },
}))
const details = { confidence: 'alta', confidence_reason: 'Fonte aplicável.', facts: [{ text: 'Fato fundamentado.', numbers: [1] }],
  hypotheses: [], missing_information: [], next_steps: [], policies: [], transactions: [], steps: ['Busca realizada'],
  sources: [{ url: 'https://learning.sap.com/', title: 'Fonte oficial SAP', numbers: [1] }], consulted_sources: [] }
const answer: Message = { id: 'answer', role: 'assistant', content: 'Resposta fundamentada. [1](https://learning.sap.com/)', error: false, details }
const proposal: Proposal = { id: 'proposal-1', ticket: 'C07', state: 'pendente',
  expires_at: new Date(Date.now() + 900000).toISOString(), phrase: 'Posso registrar o recebimento simulado de 10 UN?',
  effect: { operation: 'Recebimento simulado', purchase_order: '4500001007', item: '10', material: 'MAT-007',
    quantity: '10', unit: 'UN', plant: 'BR01', storage_location: 'D001', posting_date: '2026-10-18', before: '30', after: '20' }, result: {} }

function setup(initial: Partial<Snapshot> = {}) {
  const box = { current: { cases, messages: [], proposals: [], ...initial } as Snapshot }
  const api: Api = {
    config: vi.fn().mockResolvedValue({ requires_access_code: false }),
    session: vi.fn().mockResolvedValue({ authenticated: true }), login: vi.fn().mockResolvedValue({ authenticated: true }),
    newChat: vi.fn().mockImplementation(async () => { box.current = { cases, messages: [], proposals: [] }; return { chat_id: 'new-chat' } }),
    snapshot: vi.fn().mockImplementation(async () => structuredClone(box.current)),
    send: vi.fn().mockImplementation(async (_chat, message, _ticket, _submission, event) => {
      event({ type: 'progress', label: 'Verificando fontes…' })
      box.current.messages = [{ id: 'user', role: 'user', content: message, error: false, details }, answer]
      event({ type: 'completed', state: 'completed' })
    }),
    decide: vi.fn().mockImplementation(async (_chat, _id, approve) => {
      box.current.proposals = [{ ...proposal, state: approve ? 'executada' : 'recusada', result: { message: approve ? 'Recebimento registrado.' : 'Solicitação recusada.' } }]
      return { state: approve ? 'executada' : 'recusada', message: 'Atualizada' }
    }),
  }
  render(<App api={api} />)
  return { api, box, user: userEvent.setup() }
}

beforeEach(() => { sessionStorage.clear() })

describe('chat React', () => {
  it('inicia sem anexo e não faz novas consultas para navegar, ver detalhes e anexar', async () => {
    const { api, user } = setup()
    await screen.findByRole('heading', { name: 'Como posso ajudar?' })
    expect(screen.queryByRole('complementary')).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Chamados' }))
    const dialog = screen.getByRole('dialog', { name: 'Chamados' })
    expect(within(dialog).getAllByRole('button', { pressed: false }).length).toBe(7)
    await user.type(within(dialog).getByRole('textbox', { name: 'Buscar chamado' }), '4500001007')
    await user.click(within(dialog).getByRole('button', { name: 'Ver detalhes' }))
    expect(within(dialog).getByText('Impacto informado pelo solicitante.')).toBeVisible()
    expect(within(dialog).getByText('MM-IM-GR-PO')).toBeVisible()
    await user.click(within(dialog).getByRole('button', { name: 'Anexar ao chat' }))
    expect(screen.getByRole('button', { name: 'Remover anexo' })).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'Remover anexo' }))
    expect(screen.queryByRole('button', { name: 'Remover anexo' })).not.toBeInTheDocument()
    expect(api.snapshot).toHaveBeenCalledTimes(1)
    expect(api.send).not.toHaveBeenCalled()
    expect(api.decide).not.toHaveBeenCalled()
  })

  it('filtro vazio e cancelamento mantêm o chat sem anexo', async () => {
    const { api, user } = setup()
    await screen.findByRole('heading', { name: 'Como posso ajudar?' })
    await user.click(screen.getByRole('button', { name: 'Chamados' }))
    await user.selectOptions(screen.getByRole('combobox', { name: 'Prioridade' }), 'missing')
    expect(screen.getByRole('button', { pressed: true }).textContent).toContain('SIM-C05')
    await user.type(screen.getByRole('textbox', { name: 'Buscar chamado' }), 'inexistente')
    expect(screen.getByText('Nenhum chamado encontrado. Ajuste a busca.')).toBeVisible()
    expect(screen.getByRole('button', { name: 'Anexar ao chat' })).toBeDisabled()
    await user.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(api.snapshot).toHaveBeenCalledTimes(1)
  })

  it('pergunta geral envia uma vez e mantém fontes em um único detalhe fechado', async () => {
    const { api, user } = setup()
    await screen.findByRole('heading', { name: 'Como posso ajudar?' })
    await user.type(screen.getByRole('textbox', { name: 'Mensagem' }), 'Como funciona o recebimento?')
    await user.click(screen.getByRole('button', { name: 'Enviar mensagem' }))
    await screen.findByText('Resposta fundamentada.', { exact: false })
    expect(api.send).toHaveBeenCalledTimes(1)
    expect(vi.mocked(api.send).mock.calls[0][2]).toBeNull()
    const summary = screen.getByText('Fontes e detalhes')
    expect(summary.closest('details')).not.toHaveAttribute('open')
    expect(screen.getByText('Fato fundamentado.', { exact: false })).not.toBeVisible()
    await user.click(summary)
    expect(screen.getByRole('link', { name: /Fonte oficial SAP/ })).toHaveAttribute('href', 'https://learning.sap.com/')
    expect(screen.getByText('Busca realizada')).toBeVisible()
  })

  it('novo chat limpa rascunho e anexo sem enviar ou decidir nada', async () => {
    const { api, user } = setup({ messages: [answer] })
    await screen.findByText('Resposta fundamentada.', { exact: false })
    await user.click(screen.getByRole('button', { name: 'Chamados' }))
    await user.click(screen.getByRole('button', { name: 'Anexar ao chat' }))
    await user.type(screen.getByRole('textbox', { name: 'Mensagem' }), 'Rascunho antigo')
    await user.click(screen.getByRole('button', { name: 'Novo chat' }))
    await screen.findByRole('heading', { name: 'Como posso ajudar?' })
    expect(screen.getByRole('textbox', { name: 'Mensagem' })).toHaveValue('')
    expect(screen.queryByRole('button', { name: 'Remover anexo' })).not.toBeInTheDocument()
    expect(api.newChat).toHaveBeenCalledTimes(1)
    expect(api.send).not.toHaveBeenCalled(); expect(api.decide).not.toHaveBeenCalled()
  })

  it.each([true, false])('decisão %s só aparece após reanexar o chamado da proposta', async approve => {
    const { api, user } = setup({ proposals: [proposal] })
    await screen.findByRole('button', { name: 'Anexar SIM-C07' })
    expect(screen.queryByRole('button', { name: 'Sim, autorizar' })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Anexar SIM-C07' }))
    expect(screen.getByRole('textbox', { name: 'Mensagem' })).toBeDisabled()
    expect(screen.getByText('Receber 10 UN')).toBeVisible()
    await user.click(screen.getByRole('button', { name: approve ? 'Sim, autorizar' : 'Não, recusar' }))
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Sim, autorizar' })).not.toBeInTheDocument())
    expect(api.decide).toHaveBeenCalledExactlyOnceWith('initial', 'proposal-1', approve)
  })

  it('remover anexo com proposta pendente libera pergunta geral e não concede autorização', async () => {
    const { api, user } = setup({ proposals: [proposal] })
    await user.click(await screen.findByRole('button', { name: 'Anexar SIM-C07' }))
    await user.click(screen.getByRole('button', { name: 'Remover anexo' }))
    expect(screen.getByRole('textbox', { name: 'Mensagem' })).not.toBeDisabled()
    expect(screen.getByRole('button', { name: 'Anexar SIM-C07' })).toBeVisible()
    expect(api.decide).not.toHaveBeenCalled()
    expect(api.snapshot).toHaveBeenCalledTimes(1)
  })

  it('proposta vencida não oferece Sim/Não e não impede pergunta geral', async () => {
    const { api } = setup({ proposals: [{ ...proposal, expires_at: new Date(Date.now() - 1000).toISOString() }] })
    await screen.findByText('A solicitação venceu. Peça uma nova análise.')
    expect(screen.queryByRole('button', { name: 'Sim, autorizar' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Não, recusar' })).not.toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Mensagem' })).not.toBeDisabled()
    expect(api.decide).not.toHaveBeenCalled()
  })

  it('resposta antiga em andamento não invade a conversa criada por Novo chat', async () => {
    const { api, box, user } = setup()
    let complete!: () => void
    const waiting = new Promise<void>(resolve => { complete = resolve })
    vi.mocked(api.send).mockImplementation(async () => { await waiting })
    await screen.findByRole('heading', { name: 'Como posso ajudar?' })
    await user.type(screen.getByRole('textbox', { name: 'Mensagem' }), 'Pergunta da conversa antiga')
    await user.click(screen.getByRole('button', { name: 'Enviar mensagem' }))
    await user.click(screen.getByRole('button', { name: 'Novo chat' }))
    await screen.findByRole('heading', { name: 'Como posso ajudar?' })
    box.current = { cases, messages: [answer], proposals: [] }
    await act(async () => { complete(); await waiting })
    expect(api.snapshot).toHaveBeenLastCalledWith('initial')
    expect(screen.queryByText('Resposta fundamentada.', { exact: false })).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Como posso ajudar?' })).toBeVisible()
  })
})
