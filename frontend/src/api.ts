import type { ProgressEvent, Snapshot, CorrectionValues } from './types'

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message) }
}

async function checked(response: Response): Promise<Response> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(typeof body.detail === 'string' ? body.detail : 'Não foi possível concluir a solicitação.', response.status)
  }
  return response
}

async function request<T>(path: string, body?: unknown): Promise<T> {
  // Mesmo domínio em execução local e na Vercel: /api é roteado ao FastAPI.
  // Bindings internos são exclusivos de funções no servidor, nunca do navegador.
  const response = await checked(await fetch('/api' + path, {
    credentials: 'same-origin', method: body === undefined ? 'GET' : 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'sap-assistant' },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  }))
  return response.json() as Promise<T>
}

export const api = {
  config: () => request<{ requires_access_code: boolean }>('/config'),
  session: () => request<{ authenticated: boolean }>('/session'),
  login: (access_code = '') => request<{ authenticated: boolean }>('/session', { access_code }),
  newChat: () => request<{ chat_id: string }>('/chats', {}),
  snapshot: (chat: string) => request<Snapshot>(`/chats/${encodeURIComponent(chat)}`),
  prepareCorrection: (chat: string, message: string, values: CorrectionValues) => request<{ proposal_id: string }>(
    `/chats/${encodeURIComponent(chat)}/messages/${encodeURIComponent(message)}/correction`, values),
  decide: (chat: string, proposal: string, approve: boolean) => request<{ state: string; message: string }>(
    `/chats/${encodeURIComponent(chat)}/proposals/${encodeURIComponent(proposal)}/decision`, { approve }),
  async send(chat: string, message: string, ticket_id: string | null, submission_id: string,
             onEvent: (event: ProgressEvent) => void) {
    const response = await checked(await fetch(`/api/chats/${encodeURIComponent(chat)}/messages`, {
      method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'sap-assistant' },
      body: JSON.stringify({ message, ticket_id, submission_id }),
    }))
    if (!response.body) throw new Error('A conexão não retornou o andamento da análise. Atualize a conversa.')
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = '', completed = false
    const consume = (line: string) => {
      if (!line.trim()) return
      const event = JSON.parse(line) as ProgressEvent
      if (event.type === 'error') throw new Error(event.message || 'Não foi possível concluir a análise.')
      if (event.type === 'completed') completed = true
      onEvent(event)
    }
    try {
      while (true) {
        const { done, value } = await reader.read()
        buffer += decoder.decode(value, { stream: !done })
        let index: number
        while ((index = buffer.indexOf('\n')) >= 0) {
          consume(buffer.slice(0, index)); buffer = buffer.slice(index + 1)
        }
        if (done) break
      }
      consume(buffer)
      if (!completed) throw new Error('A conexão foi interrompida. Atualize a conversa antes de enviar novamente.')
    } finally { reader.releaseLock() }
  },
}
export type Api = typeof api
