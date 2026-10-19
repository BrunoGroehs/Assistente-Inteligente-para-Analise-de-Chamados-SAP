# Assistente SAP MM

Protótipo para análise de chamados de recebimento de mercadorias com referência a pedidos de compra. React + TypeScript na interface e Python/FastAPI na API; Supabase/PostgreSQL com pgvector na persistência; Qwen3.6 Plus e Qwen3 Embedding 8B pelo OpenRouter.

O SAP é simulado. Nenhuma chamada executa transações SAP reais. Oito chamados fictícios estão disponíveis, com histórico isolado por sessão, fontes consultadas e propostas que precisam de aprovação humana.

## Executar no Windows

Python 3.12 e Node.js 24.14 são as versões validadas. Não é necessário instalar banco local. Na raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Preencha `.env` localmente com a chave OpenRouter e a conexão Supabase. O arquivo é ignorado pelo Git. Não cole segredos em prompts, issues ou capturas de tela.

### Conexão PostgreSQL no Supabase

1. Abra o projeto correto no painel Supabase e clique em **Connect**.
2. Selecione **Session pooler** e copie a conexão PostgreSQL.
3. Substitua `[YOUR-PASSWORD]` pela senha do banco, codificando caracteres reservados para URL. Não use a chave anon/publishable como senha.
4. Preencha `DATABASE_URL` no `.env`. O aplicativo aceita `postgresql://`, `postgres://` ou `postgresql+psycopg://`, normalizando o driver internamente. Preserve o usuário, host e porta copiados do painel e use `sslmode=require`.
5. Em **Database → Extensions**, ative `vector` se ainda não estiver ativa. O aplicativo não instala nem altera extensões.

Exemplo com valores fictícios:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres.PROJECT_REF:SENHA_CODIFICADA@HOST_DO_POOLER:5432/postgres?sslmode=require
OPENROUTER_API_KEY=CHAVE_LOCAL
OPENROUTER_CHAT_MODEL=qwen/qwen3.6-plus
OPENROUTER_EMBEDDING_MODEL=qwen/qwen3-embedding-8b
APP_ENV=local
```

Se precisar codificar uma senha, use uma ferramenta local, não um site externo. [Conexões Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres).

### Preparar e iniciar

```powershell
.\.venv\Scripts\python.exe -m sap_assistant.cli init-db
.\.venv\Scripts\python.exe -m sap_assistant.cli ingest
cd frontend
npm.cmd ci
npm.cmd run build
cd ..
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000`. A API serve a interface compilada e os endpoints na mesma origem. Encerre com Ctrl+C. O chat inicia sem chamado anexado e permite perguntas gerais sobre o processo pelo RAG. A ingestão gera embeddings com cobrança do OpenRouter; documentos inalterados usam o cache. A aplicação também prepara os guias automaticamente e gera embeddings faltantes na primeira consulta. Reinicie o processo após mudar o `.env`.

Não há painel lateral. Use **Chamados** no compositor para listar/buscar os casos, **Ver detalhes** para consultar e **Anexar ao chat** para incluir o contexto. O chamado aparece como um cartão removível, semelhante a um arquivo anexado. Você pode substituir ou **Remover anexo** e continuar perguntando na mesma conversa. Cada mensagem preserva seu contexto; novas perguntas sem anexo não herdam dados do caso anterior. Para analisar o anexo, escreva ou clique em **Analisar chamado**. Anexar/remover não chama a IA nem decide aprovações.

**Novo chat**, no cabeçalho, inicia uma conversa vazia e sem anexo, mantendo os dados dos chamados e os registros anteriores no banco. Perguntas e propostas de outra conversa não são reutilizadas. As respostas mostram o resumo e, quando útil, um próximo passo; fontes e verificações completas ficam em um único **Fontes e detalhes**, fechado por padrão. Alertas e cartões de aprovação permanecem visíveis.

Os registros das novas sessões seguem um formato inspirado no SAP for Me: ambiente, componente sugerido, prioridade, impacto e reprodução. IDs `SIM-Cxx` e situações são locais; nenhum case é enviado à SAP. Sessões já abertas mantêm seus dados anteriores; abra uma nova sessão para receber os novos perfis. [Fontes e limites](instrucoes/02-processo-sap.md).

Para conferir os modelos com uma chamada real de cada tipo:

```powershell
.\.venv\Scripts\python.exe -m sap_assistant.cli check-provider
```

## Dados e aprovação humana

Somente o schema **`sap_chamados_ai`** é criado/utilizado pela aplicação. Ele possui uma identificação de projeto; um schema existente sem identificação compatível causa recusa de inicialização. Não há comando DROP, reset global ou alteração de tabelas externas. Não exponha esse schema pela Data API; o acesso ocorre somente pelo servidor Python.

As tabelas próprias são `sap_project_identity`, `sap_workspaces`, `sap_messages`, `sap_knowledge`, `sap_proposals` e `sap_audit`. A extensão vector é uma configuração do banco existente, ativada pelo usuário. Não se instala outro banco local: SQLite é usado apenas nos testes temporários.

O LLM devolve uma proposta tipada, sem URL/SQL arbitrário. O gateway valida operação, frase, parâmetros, sessão e versões; a interface mostra o efeito concreto e solicita **Sim, autorizar / Não, recusar**. A proposta vale 15 minutos. Recusa, silêncio, mudança de dados ou clique repetido não criam autorização nova. Uma mensagem “sim” no chat não executa nada. Cada alteração de situação do chamado exige decisão separada.

Sem chamado anexado, não há proposta de alteração nem consulta aos pedidos simulados. Remover o anexo preserva a proposta anterior e permite perguntas gerais; para decidir, reanexe o chamado original pelo cartão. A decisão continua vinculada à proposta exata, com a mesma validade.

A navegação reutiliza uma cópia visual exclusiva da sessão no navegador para evitar consultas ao banco em cada clique. Ela é recarregada após análise/decisão ou pelo botão **Atualizar**, usado também para mudanças externas. Essa cópia nunca autoriza operações: o gateway sempre verifica o Supabase atual antes de executar. Durante a análise, o status informa a etapa em andamento. [Medições de desempenho](evidencias/README.md).

O “passo a passo” mostra operações observáveis, evidências e justificativas resumidas. Raciocínio interno bruto não é exibido ou usado como auditoria.

As respostas indicam as fontes do RAG por números e links que abrem diretamente a documentação oficial. URLs repetidas são agrupadas; fontes citadas, referências apenas consultadas e dados simulados têm áreas próprias. Não há exibição de `content`, trechos ou popup. Textos e metadados permanecem salvos internamente para recuperação e auditoria.

Antes de gerar a análise, uma chamada estruturada verifica se os trechos cobrem a pergunta atual. O servidor valida os IDs de parágrafo selecionados e exige citação do conhecimento aprovado. Sem suporte, retorna **“Não tenho informações suficientes na base de conhecimento...”**, sem diagnóstico, hipóteses ou proposta. Base vazia, código não documentado e prova inválida também bloqueiam a geração. A verificação semântica usa LLM e continua sujeita à avaliação de qualidade.

## Conhecimento, testes e decisões

- [Catálogo do conhecimento](conhecimento/catalogo.json): 12 guias próprios, sendo dez sínteses de nove fontes oficiais e duas políticas simuladas; nenhum gabarito é indexado.
- [Instruções e decisões](instrucoes/README.md): requisitos, arquitetura, diagramas, prompts e limites.
- [Evidências](evidencias/README.md): resultados locais e integrados, com limitações explícitas.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check sap_assistant app.py tests scripts
cd frontend
npm.cmd test
npm.cmd run build
cd ..
```

Os testes padrão usam banco temporário e provedor controlado: não leem a chave nem consomem créditos. Não comprovam sozinhos a qualidade do modelo real. Não existe fallback de produção para respostas mockadas ou para outro modelo.

Para reproduzir a verificação ampliada com os serviços reais configurados no `.env`:

```powershell
.\.venv\Scripts\python.exe scripts/verify_live.py
```

Esse comando **consome créditos** e cria sessões fictícias próprias no schema do projeto. Verifica fontes diretas, novos conteúdos, perguntas sem suporte, regressões dos chamados e cliques Sim/Não, além de concorrência, isolamento, adulteração, expiração e rollback. Não altera tabelas externas nem injeta documentos na base compartilhada. O histórico do núcleo está em [verificação de fontes/RAG](evidencias/verificacao-fontes-rag.json); cobertura e limites em [verificação dos requisitos](evidencias/verificacao-requisitos.md). A execução atual desse script gera `evidencias/verificacao-ampliada-web.json`, preservando o relatório anterior. Propostas pendentes anteriores ao novo envelope de integridade exigem nova análise; não são executadas usando o formato antigo.

Para verificar a API atual com Supabase/OpenRouter reais:

```powershell
.\.venv\Scripts\python.exe scripts/verify_web_live.py
```

Consome créditos; testa RAG geral, fontes diretas, abstinência, Sim/Não, duplicação e Novo chat em sessões fictícias próprias. O relatório é [verificacao-web-api.json](evidencias/verificacao-web-api.json). As decisões desse teste são simuladas, não cliques de uma pessoa. Os testes React exercitam busca, detalhes, anexo, resposta compacta e cartões. Relatórios antigos de Streamlit são históricos; não comprovam a interface atual.

## Arquitetura atual

```mermaid
flowchart LR
    UI[React e TypeScript] -->|HTTP e cookie HttpOnly| API[FastAPI /api]
    API --> CORE[Atendimento Python]
    CORE --> RAG[Busca híbrida e verificação de cobertura]
    RAG <--> DB[(Supabase e pgvector)]
    RAG <--> OR[OpenRouter: embeddings e Qwen]
    CORE --> PROPOSTA[Proposta validada]
    UI -->|Sim ou Não para proposta exata| HITL[Gateway determinístico]
    PROPOSTA --> HITL
    HITL -->|Aprovação válida| SAP[SAP simulado no Supabase]
```

Busca, filtros, detalhes e anexos são estado React local; não chamam Python nem o banco. A análise envia etapas observáveis por NDJSON enquanto o núcleo consulta o Supabase e o OpenRouter em uma tarefa separada. A resposta técnica aparece depois de validada. O RAG e o gateway permanecem no núcleo Python, sem ferramentas de execução ou aprovação para o modelo. [Arquitetura e contratos](instrucoes/03-arquitetura.md).

Para desenvolver a interface com atualização automática, mantenha a API na porta 8000 e execute `npm.cmd run dev` em `frontend/` em outro terminal. Abra a URL indicada pelo Vite (normalmente porta 5173); o proxy encaminha `/api` sem expor segredos. Para executar normalmente, basta o build e um processo Uvicorn, sem servidor Vite. No Linux/macOS, use `npm` em lugar de `npm.cmd` e o Python do ambiente correspondente.

## Deploy na Vercel com dois serviços

O [vercel.json](vercel.json) prepara um único projeto Vercel com builds independentes. **Configuração proposta, aguardando confirmação dos nomes e rotas pelo usuário:**

| Serviço | Raiz e framework | Caminhos públicos |
| --- | --- | --- |
| `app` | `.`; FastAPI; entrada `app:app`; Python 3.12 | `/api` e `/api/*`, preservando o prefixo. |
| `frontend` | `frontend`; Vite; Node.js 24; build em `dist` | Todos os demais caminhos, incluindo `/` e `/assets/*`. |

As regras específicas da API vêm antes do catch-all. Um endpoint inexistente em `/api/*` retorna o erro da API, sem cair na interface. O navegador continua usando URLs relativas `/api`, com cookie HttpOnly na mesma origem. O frontend Vite é estático: não há chamadas de uma função de um serviço para outro e, portanto, **nenhum binding interno é necessário**. Supabase e OpenRouter são serviços externos, configurados por segredos; não são bindings Vercel. Se futuramente houver comunicação entre funções de serviços distintos, declarar o binding no chamador e ler a URL injetada somente em runtime, sem defini-la manualmente ou expô-la por `VITE_*`.

No painel Vercel, importe o repositório com **Root Directory na raiz (`.`)**, mantendo os dois serviços do arquivo. Não crie um projeto separado só para `frontend` nem defina build/framework/output globais: essas opções pertencem a cada serviço. O frontend executa `npm ci` e `npm run build`; a API instala as dependências Python. `.python-version` e `pyproject.toml` fixam Python 3.12; `frontend/package.json` especifica Node.js 24. As dependências Python de runtime continuam centralizadas em `requirements.txt`, lidas pelo empacotamento do projeto.

Cadastre as variáveis do `.env.example` no ambiente Vercel correspondente: conexão Supabase com SSL, chave OpenRouter, modelos, `APP_ENV=cloud`, `DEMO_ACCESS_CODE` com pelo menos 12 caracteres e limite por sessão. Não envie `.env` ao Git e não use prefixo `VITE_` para segredos. Use ambientes Supabase separados se os previews não puderem compartilhar as sessões e o corpus do ambiente principal. O cookie é HttpOnly, SameSite estrito e Secure fora de local. O código de acesso não substitui login individual de produção.

Defina `APP_PUBLIC_ORIGIN` como a origem pública exata usada no navegador, por exemplo `https://SEU_PROJETO.vercel.app`, sem caminho. Isso permite validar Origin mesmo quando o proxy de serviços usa um Host interno. Na ausência desse valor, a aplicação usa `VERCEL_URL` quando a plataforma o fornece; aliases/domínios personalizados podem exigir o valor explícito por ambiente. Nenhum cabeçalho `X-Forwarded-Host` enviado pelo cliente concede essa permissão.

O serviço FastAPI tem duração máxima configurada em 300 segundos. O progresso do chat continua em NDJSON; uma aprovação humana pendente é persistida e encerra a requisição, sem aguardar o clique dentro da função. `.vercelignore` exclui segredos, ambiente virtual e artefatos locais do envio; `functions.app.py.excludeFiles` remove frontend e materiais de desenvolvimento do bundle Python, preservando `conhecimento/` e `prompts/`. Na Vercel, a interface é servida pelo serviço Vite; não depende de `frontend/dist` dentro do backend.

Para conferir os serviços juntos localmente, na raiz, com `.env` configurado e `APP_ENV=local`:

```powershell
$env:APP_PUBLIC_ORIGIN='http://127.0.0.1:3000'
npx.cmd --yes vercel@64.5.0 dev -L --listen 127.0.0.1:3000
```

`-L` executa sem vincular ou publicar um projeto e sem buscar segredos da conta Vercel. Sem essa opção, `vercel dev` pode solicitar vínculo ao projeto. As duas formas coordenam os serviços e injetam os bindings que existirem; a configuração atual não declara nenhum. Teste `/`, `/api/health`, sessão e aprovação; encerre com Ctrl+C. Esse comando pode instalar dependências locais e, ao inicializar a API, prepara somente o schema próprio do projeto. Perguntas ao modelo consomem créditos. O proxy localhost em `vite.config.ts` atende somente o desenvolvimento isolado com `npm run dev`, não chamadas internas da Vercel.

O limite de quatro análises simultâneas e uma por sessão é por instância Python, sem coordenação global entre instâncias Vercel. A idempotência de escritas continua transacional no Supabase. O pool de conexões também é por instância; acompanhe os limites do Supabase ao ampliar o tráfego. Não houve nova migração, deploy ou push nesta configuração. Publicação e validação hospedada são etapas separadas.

A execução portátil fora da Vercel permanece disponível: compile o React em `frontend/dist` e inicie `python -m uvicorn app:app --host 0.0.0.0 --port PORTA_ESCOLHIDA`. Nesse modo, o FastAPI serve também o build da interface.

Referências oficiais: [Services](https://vercel.com/docs/services), [roteamento](https://vercel.com/docs/services/routing), [bindings](https://vercel.com/docs/services/bindings) e [FastAPI](https://vercel.com/docs/frameworks/backend/fastapi).

## Correções e citações

Ao identificar correção executável, o chat oferece a proposta **Sim/Não** ou **Preparar correção**, quando faltarem quantidade/data ou situação desejada. Preencha o formulário e clique em **Revisar ação**; isso somente prepara a proposta. A execução exige **Sim, autorizar** separado. Nada escolhe automaticamente a quantidade pelo saldo ou inventa data. “Altere para mim” mantém a correção discutida, sem virar mudança de status.

Os números das fontes são clicáveis, inclusive em respostas antigas. Fonte SAP abre o site oficial; regra interna abre a identificação em **Fontes e detalhes**, sem conteúdo bruto ou popup. Para reproduzir C03 com Supabase/OpenRouter reais: `python scripts/verify_corrections_live.py` (requer dependências de desenvolvimento, consome créditos e simula as decisões humanas em workspace próprio).

## Testes de navegador com serviços reais

Os testes de navegador usam Microsoft Edge instalado, Supabase/OpenRouter reais e sessões fictícias novas. **Consomem créditos**, por isso são separados dos testes padrão e exigem confirmação explícita por variável de ambiente:

```powershell
cd frontend
npm.cmd ci
npm.cmd run build
$env:RUN_REAL_USER_TESTS='1'
$env:USER_TEST_RUN='minha-rodada'
npm.cmd run test:usuario:real
```

A configuração inicia um Uvicorn temporário na porta local 8011 e o encerra ao terminar. O nome da rodada evita sobrescrever evidências anteriores; use um nome novo para cada execução. Não executa deploy, reset ou limpeza de tabelas. `.env` e credenciais ficam no Python. Não são gravados vídeos ou traces com cookies; os relatórios públicos contêm somente perguntas, respostas e metadados de apresentação. Os resultados e capturas ficam em `evidencias/jornadas-usuario/`. A verificação de links também confere os destinos contra o catálogo; um teste abre uma página oficial em nova aba.
