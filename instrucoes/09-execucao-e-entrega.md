# Execução, publicação e entrega

## Estado e preparação

**Decisão confirmada:** implementação autorizada em 18/10/2026. O aplicativo executável, os comandos e as configurações atuais estão no [README principal](../README.md). Este documento reúne a configuração e os critérios de evolução; os resultados concluídos estão nas [evidências](../evidencias/README.md).

**Estado implementado:** Python 3.12, dependências diretas fixadas após validar compatibilidade e API FastAPI na raiz e frontend React/TypeScript compilado com Vite. Domínio, infraestrutura, interface, conhecimento e testes estão separados. O README principal contém os comandos de preparação e execução; manter suas instruções alinhadas ao código e aos resultados verificados.

| Configuração proposta | Finalidade | Tratamento |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | Chat e embeddings | Segredo somente no servidor. |
| `OPENROUTER_CHAT_MODEL` | `qwen/qwen3.6-plus` | Valor configurável e registrado por análise. |
| `OPENROUTER_EMBEDDING_MODEL` | `qwen/qwen3-embedding-8b` | Validar disponibilidade e dimensão antes de criar o índice. |
| `DATABASE_URL` | PostgreSQL no Supabase | Conexão segura com pool adequado ao ambiente e privilégio mínimo. |
| `DEMO_ACCESS_CODE` | Acesso restrito à demonstração | Recomendação de acesso simples para banca, validado no servidor e nunca enviado ao LLM. |
| `APP_PUBLIC_ORIGIN` | Origem pública exata do navegador | Protocolo e domínio/porta, sem caminho; não é segredo. Fallback para `VERCEL_URL` quando fornecido pela plataforma. |

Não solicitar segredos no chat. O usuário configurou `.env` localmente e ativou vector. O aplicativo usa Supabase em desenvolvimento e hospedagem; somente os testes usam SQLite temporário. Todos os objetos próprios ficam em `sap_chamados_ai`, com verificação de identificação; não modificar tabelas dos outros projetos, executar DROP ou reset global. O usuário solicitou posteriormente preparar a Vercel com múltiplos serviços; publicação ainda não foi autorizada. Para uso público além da banca, reavaliar autenticação, limites e privacidade.

## Etapas e saídas verificáveis

**Recomendação:**

1. **Núcleo e dados:** materializar oito fixtures, contratos e simulador; garantir consultas e regras de negócio independentes da UI. Saída: testes determinísticos do domínio.
2. **Conhecimento e RAG:** curar guias, registrar metadados, validar embeddings e criar busca híbrida. Saída: evidências relevantes para os casos, sem gabarito no índice.
3. **HITL:** gateway, propostas, validade, transações, idempotência e isolamento. Saída: escrita impossível sem autorização e testes de exceção aprovados.
4. **Interface:** chat único, seletor em diálogo, anexo opcional e cartões de aprovação, seguindo a [direção visual](06-interface.md). Saída: atendimento integrado e validação manual desktop/tela estreita.
5. **Validação e publicação:** executar matriz relevante, registrar falhas e resultados, preparar secrets e acesso restrito. Publicar somente na etapa correspondente, sem alegar funcionamento antes do teste hospedado.
6. **Entrega:** README, diagrama, base, chamados, decisões, testes e limitações.

O fluxo HITL pode ser testado antes do LLM real, usando propostas controladas. Isso valida a barreira; não substitui a rodada integrada com o OpenRouter.

## Vercel Services e execução portátil

**Decisão confirmada, substituindo a ausência de plataforma da D33:** preparar um projeto Vercel com múltiplos serviços, sem publicar. **Configuração proposta para confirmação do usuário:** `app`, FastAPI na raiz, recebe `/api` e `/api/*`; `frontend`, Vite em `frontend/`, recebe o restante. Nenhum serviço exclusivamente interno nesta configuração; nenhum binding, porque todas as chamadas à API partem do navegador, não de funções de outro serviço. A solicitação de confirmação dos nomes, exposição e bindings é explícita do usuário. Detalhes e comandos no [README](../README.md#deploy-na-vercel-com-dois-serviços).

Na Vercel, cada serviço é construído independentemente. Instância FastAPI `app:app`, Python 3.12 definido em `.python-version`/`pyproject.toml`, dependências de runtime obtidas de `requirements.txt`, duração de função de 300 s. Frontend com Node.js 24, `npm ci`, `npm run build` e saída `dist`. Rewrites públicos permanecem no topo de `vercel.json`; configurações de build/runtime ficam em cada serviço. Não incluir o frontend no bundle Python; preservar `conhecimento/` e `prompts/`. Arquivos locais e segredos ficam fora do envio via `.vercelignore`.

Configurar os segredos do `.env.example` no ambiente Vercel correspondente, com HTTPS, `APP_ENV=cloud` e código de acesso de pelo menos 12 caracteres. Não colocar chave ou conexão de banco em variáveis Vite. `/api` mantém o prefixo e a origem pública, preservando cookie e validação Origin/Host. Testar os serviços juntos com `vercel dev` ou `vercel dev -L` para modo local sem vínculo. Bindings, se surgirem no futuro, são injetados pela Vercel no chamador, apenas em funções no runtime; não definir manualmente a variável nem utilizá-la no navegador/build/middleware.

**Correção verificada em desenvolvimento:** o proxy de serviços usa um Host interno diferente do Origin do navegador. Aceitar adicionalmente a origem exata configurada no servidor por `APP_PUBLIC_ORIGIN` (ou URL de runtime Vercel) preserva o bloqueio de origens externas; não confiar em `X-Forwarded-Host` da requisição. No teste local, usar a origem e porta indicadas no comando do README. Na publicação, preencher o domínio efetivamente utilizado, sem inventar URL do projeto.

A alternativa portátil permanece: compilar em `frontend/dist` e iniciar um processo Uvicorn que também serve a interface, sem Vite ativo. Não deixar servidores locais de teste rodando ao encerrar o trabalho. Não há publicação automática, Docker obrigatório ou mudança do Supabase nesta etapa.

Inicializar/verificar somente o schema do projeto e ingerir documentos alterados sem reconstruir embeddings desnecessariamente. Limite de tarefas e pool de conexões são por instância; Vercel pode criar várias instâncias. Avaliar coordenação distribuída para limite global e capacidade do Supabase antes de ampliar tráfego. Testes locais não equivalem à validação do ambiente hospedado.

## Riscos e evolução

| Risco ou limitação | Tratamento recomendado |
| --- | --- |
| Diferenças de versão e configuração SAP | Metadados, orientações delimitadas e revisão humana; não alegar validação em SAP real. |
| LLM inventar causa ou citar fonte inadequada | Recuperação, contratos, verificação factual e abstinência quando faltar evidência. |
| Documento ou página inacessível | Retentativa, alternativa oficial e colaboração do usuário conforme [RAG](04-rag-e-fontes.md). |
| Custo ou indisponibilidade do provedor | Acesso restrito, limites por sessão, cache de embeddings e falha explícita. |
| Reinício e reenvio HTTP | Estado durável, IDs de submissão e execução idempotente. |
| Exposição de credenciais ou sessões | Segredos no servidor, escopo por sessão e logs sem credenciais. |
| Simulação confundida com integração SAP | Aviso discreto, resultados identificados como simulados e limites documentados. |

Para futura integração real, adotar adaptador com APIs autorizadas, identidade com privilégio mínimo, separação de leitura/escrita, auditoria e autorização humana preservada. Avaliar conciliação de operações remotas e regras reais do processo antes de habilitar qualquer escrita. Não usar o modelo como cliente HTTP irrestrito.
