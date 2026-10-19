import { afterEach, expect, it, vi } from 'vitest'
import { api, ApiError } from './api'

afterEach(() => vi.unstubAllGlobals())

it('consome eventos repartidos sem tratar progresso como resposta validada', async () => {
  const bytes = new TextEncoder().encode('{"type":"progress","label":"Verificação"}\n{"type":"completed","state":"completed"}\n')
  const stream = new ReadableStream({ start(controller) {
    controller.enqueue(bytes.slice(0, 47)); controller.enqueue(bytes.slice(47)); controller.close()
  } })
  const fetch = vi.fn().mockResolvedValue(new Response(stream, { status: 200 }))
  vi.stubGlobal('fetch', fetch)
  const events: unknown[] = []
  await api.send('initial', 'Pergunta', null, 'submission', event => events.push(event))
  expect(events).toEqual([{ type: 'progress', label: 'Verificação' }, { type: 'completed', state: 'completed' }])
  expect(fetch).toHaveBeenCalledTimes(1)
})

it('conexão interrompida não repete o envio automaticamente', async () => {
  const fetch = vi.fn().mockResolvedValue(new Response('{"type":"progress","label":"Buscando"}\n'))
  vi.stubGlobal('fetch', fetch)
  await expect(api.send('initial', 'Pergunta', null, 'submission', () => {})).rejects.toThrow('interrompida')
  expect(fetch).toHaveBeenCalledTimes(1)
})

it('erro HTTP não é aceito como sucesso', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"detail":"Sem acesso"}', { status: 401 })))
  await expect(api.snapshot('initial')).rejects.toBeInstanceOf(ApiError)
})
