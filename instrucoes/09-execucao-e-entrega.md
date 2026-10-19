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

**Decisão confirmada:** preparação Vercel solicitada após a D33; nomes/rotas/bindings seguem registrados em D37. A execução local normal está no [guia passo a passo](../README.md#testar-localmente-no-windows). Os comandos abaixo são alternativas de deploy/desenvolvimento, executados a partir da raiz.


O [vercel.json](../vercel.json) prepara um único projeto Vercel com builds independentes. **Configuração proposta, aguardando confirmação dos nomes e rotas pelo usuário:**

| Serviço | Raiz e framework | Caminhos públicos |
| --- | --- | --- |
| `app` | `.`; FastAPI; entrada `app:app`; Python 3.12 | `/api` e `/api/*`, preservando o prefixo. |
| `frontend` | `frontend`; Vite; Node.js 24; build em `dist` | Todos os demais caminhos, incluindo `/` e `/assets/*`. |

As regras específicas da API vêm antes do catch-all. Um endpoint inexistente em `/api/*` retorna o erro da API, sem cair na interface. O navegador continua usando URLs relativas `/api`, com cookie HttpOnly na mesma origem. O frontend Vite é estático: não há chamadas de uma função de um serviço para outro e, portanto, **nenhum binding interno é necessário**. Supabase e OpenRouter são serviços externos, configurados por segredos; não são bindings Vercel. Se futuramente houver comunicação entre funções de serviços distintos, declarar o binding no chamador e ler a URL injetada somente em runtime, sem defini-la manualmente ou expô-la por `VITE_*`.

No painel Vercel, importe o repositório com **Root Directory na raiz (`.`)**, mantendo os dois serviços do arquivo. Não crie um projeto separado só para `frontend` nem defina build/framework/output globais: essas opções pertencem a cada serviço. O frontend executa `npm ci` e `npm run build`; a API instala as dependências Python. `.python-version` e `pyproject.toml` fixam Python 3.12; `frontend/package.json` especifica Node.js 24. As dependências Python de runtime continuam centralizadas em `requirements.txt`, lidas pelo empacotamento do projeto.

Cadastre as variáveis do `.env.example` no ambiente Vercel correspondente: conexão Supabase com SSL, chave OpenRouter, modelos, `APP_ENV=cloud`, `DEMO_ACCESS_CODE` com pelo menos 12 caracteres e limite por sessão. Não envie `.env` ao Git e não use prefixo `VITE_` para segredos. Use ambientes Supabase separados se os previews não puderem compartilhar as sessões e o corpus do ambiente principal. O cookie é HttpOnly, SameSite estrito e Secure fora de local. O código de acesso não substitui login individual de produção.

Defina `APP_PUBLIC_ORIGIN` como a origem pública exata usada no navegador, por exemplo `https://SEU_PROJETO.vercel.app`, sem caminho. Isso permite validar Origin mesmo quando o proxy de serviços usa um Host interno. Na ausência desse valor, a aplicação usa `VERCEL_URL` quando a plataforma o fornece; aliases/domínios personalizados podem exigir o valor explícito por ambiente. Nenhum cabeçalho `X-Forwarded-Host` enviado pelo cliente concede essa permissão.

O serviço FastAPI tem duração máxima configurada em 300 segundos. O progresso do chat continua em NDJSON; uma aprovação humana pendente é persistida e encerra a requisição, sem aguardar o clique dentro da função. `.vercelignore` exclui segredos, ambiente virtual e artefatos locais do envio; `functions.app.py.excludeFiles` remove frontend e materiais de desenvolvimento do bundle Python, preservando `conhecimento/` e `prompts/`. Na Vercel, a interface é servida pelo serviço Vite; não depende de `frontend/dist` dentro do backend.

Para conferir os serviços juntos localmente, conclua primeiro o [guia local](../README.md#testar-localmente-no-windows). Execute na raiz, com `.env` configurado e `APP_ENV=local`:

```powershell
$env:APP_PUBLIC_ORIGIN='http://127.0.0.1:3000'
npx.cmd --yes vercel@64.5.0 dev -L --listen 127.0.0.1:3000
```

`-L` executa sem vincular ou publicar um projeto e sem buscar segredos da conta Vercel. Sem essa opção, `vercel dev` pode solicitar vínculo ao projeto. As duas formas coordenam os serviços e injetam os bindings que existirem; a configuração atual não declara nenhum. Teste `/`, `/api/health`, sessão e aprovação; encerre com Ctrl+C. Esse comando pode instalar dependências locais e, ao inicializar a API, prepara somente o schema próprio do projeto. Perguntas ao modelo consomem créditos. O proxy localhost em `vite.config.ts` atende somente o desenvolvimento isolado com `npm run dev`, não chamadas internas da Vercel.

O limite de quatro análises simultâneas e uma por sessão é por instância Python, sem coordenação global entre instâncias Vercel. A idempotência de escritas continua transacional no Supabase. O pool de conexões também é por instância; acompanhe os limites do Supabase ao ampliar o tráfego. A validação local não comprova o ambiente hospedado. O usuário relatou falha de conexão no deploy; a recuperação remota ainda precisa ser verificada.

A execução portátil fora da Vercel permanece disponível: compile o React em `frontend/dist` e inicie `python -m uvicorn app:app --host 0.0.0.0 --port PORTA_ESCOLHIDA`. Nesse modo, o FastAPI serve também o build da interface.

Referências oficiais: [Services](https://vercel.com/docs/services), [roteamento](https://vercel.com/docs/services/routing), [bindings](https://vercel.com/docs/services/bindings) e [FastAPI](https://vercel.com/docs/frameworks/backend/fastapi).

## Riscos e evolução

**Diagnóstico de inicialização:** o runtime informa códigos `SAP_STARTUP_*` para configuração, conexão/autenticação/permissão PostgreSQL, vector, identificação do schema, arquivos/conteúdo de conhecimento e cliente HTTP. Mensagens são fixas, sem DSN, senha, SQL ou exceção bruta. Recursos parcialmente criados são fechados; falha continua impedindo inicialização. Procedimento e códigos no [README](../README.md#falha-de-inicialização-da-api).

**Configuração de rede:** conexão direta `db.PROJECT_REF.supabase.co:5432` não é pooler e usa IPv6 por padrão. Na configuração atual Vercel/Supabase, copiar a URL completa do Session pooler (host, porta e usuário `postgres.PROJECT_REF`), com SSL; não construir o host por suposição. Alterar `DATABASE_URL` no ambiente correspondente e fazer novo deploy. [Supabase: IPv4/IPv6](https://supabase.com/docs/guides/troubleshooting/supabase--your-network-ipv4-and-ipv6-compatibility-cHe3BP). Não registrar credenciais em documentos, comandos ou logs.

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
