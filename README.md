# Assistente SAP MM

**[Acessar o aplicativo](https://assistente-inteligente-para-analise.vercel.app/)**

Assistente para análise de chamados de recebimento de mercadorias com referência a pedidos de compra. Interface React/TypeScript, API Python/FastAPI, Supabase/PostgreSQL com pgvector e modelos Qwen pelo OpenRouter.

O SAP e os oito chamados são simulados. **Testar localmente significa executar o aplicativo no computador; o banco continua no Supabase e a IA usa o OpenRouter.** Apenas os testes automatizados padrão usam banco temporário e provedor controlado.

- [Preparar e executar localmente](#testar-localmente-no-windows)
- [Conferir o funcionamento no navegador](#conferir-o-funcionamento-no-navegador)
- [Executar os testes automatizados](#testes-automatizados-sem-consumo-de-api)
- [Resolver erros de inicialização](#falha-de-inicialização-da-api)
- [Desenvolver com atualização automática](#desenvolvimento-com-atualização-automática)
- [Testar com serviços reais](#testes-com-supabase-e-openrouter-reais)
- [Deploy na Vercel](#deploy-na-vercel-com-dois-serviços)

## Testar localmente no Windows

Use PowerShell e abra o terminal na **raiz deste repositório**, onde estão `app.py`, `requirements.txt` e `frontend/`. Não é necessário Streamlit, Vercel CLI ou PostgreSQL instalado no computador para este caminho.

### 1. Conferir os pré-requisitos

Tenha Python **3.12**, Node.js **24.x**, acesso ao projeto Supabase e uma chave OpenRouter com créditos. Versões verificadas no projeto: Python 3.12.10 e Node.js 24.14.0.

```powershell
python --version
node --version
npm.cmd --version
```

Se `python` apontar para outra versão, instale/selecione Python 3.12 antes de criar o ambiente virtual.

### 2. Instalar as dependências

Execute na raiz. Não é necessário ativar o ambiente virtual: os comandos usam seu executável diretamente.

```powershell
if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm.cmd --prefix frontend ci
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

O ambiente `.venv` também deve usar Python 3.12. A cópia acima preserva um `.env` já existente.

### 3. Configurar o `.env` local

Edite `.env` no computador, sem enviar seu conteúdo ao Git ou ao chat. Substitua os marcadores fictícios abaixo pelos seus valores:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres.PROJECT_REF:SENHA_CODIFICADA@HOST_DO_SESSION_POOLER:5432/postgres?sslmode=require
OPENROUTER_API_KEY=SUA_CHAVE_OPENROUTER
OPENROUTER_CHAT_MODEL=qwen/qwen3.6-plus
OPENROUTER_EMBEDDING_MODEL=qwen/qwen3-embedding-8b
APP_ENV=local
APP_PUBLIC_ORIGIN=http://127.0.0.1:8000
DEMO_ACCESS_CODE=
MAX_ANALYSES_PER_SESSION=30
```

`DEMO_ACCESS_CODE` pode ficar vazio em modo local; se preenchido, a interface pedirá esse código. As variáveis cadastradas na Vercel não configuram automaticamente seu `.env` local. Variáveis já definidas no terminal têm prioridade sobre o arquivo; confira-as se o app continuar usando uma configuração antiga.

Para obter `DATABASE_URL`:

1. No projeto Supabase correto, abra **Connect → Session pooler**.
2. Copie a **URL completa**. O usuário deve seguir `postgres.PROJECT_REF`, e o host deve terminar em `.pooler.supabase.com`; preserve a porta indicada no painel para Session mode.
3. Preencha a senha atual do banco, codificando caracteres reservados para URL. A senha do banco não é a chave anon/publishable.
4. Use `sslmode=require`: acrescente `?sslmode=require` se não houver parâmetros, ou `&sslmode=require` se já houver outros.
5. Em **Database → Extensions**, confirme que `vector` está ativa.

Não coloque crases ou espaços extras no valor. O aplicativo aceita `postgresql://`, `postgres://` e `postgresql+psycopg://`. O endereço `db.PROJECT_REF.supabase.co` é uma conexão direta, não um pooler, e depende da compatibilidade IPv6/IPv4 do ambiente. Não deduza o host do pooler pela região; copie do painel. [Conexões Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres).

### 4. Conferir o banco e preparar o RAG

Primeiro, prepare o schema e os guias. Esse comando não chama o OpenRouter:

```powershell
.\.venv\Scripts\python.exe -m sap_assistant.cli init-db
```

Resultado esperado: `Base pronta: 12 guias; 0 embeddings gerados nesta execução.` Se falhar, resolva a conexão, as permissões ou a extensão vector antes de continuar.

Depois, gere os embeddings que faltarem:

```powershell
.\.venv\Scripts\python.exe -m sap_assistant.cli ingest
```

**A ingestão consome créditos do OpenRouter quando cria embeddings.** Guias inalterados com embeddings já existentes usam o cache. Se o comando informar zero embeddings novos, isso pode estar correto. Os guias também são sincronizados ao iniciar a API; a ingestão antecipada evita deixar essa preparação para a primeira pergunta.

A aplicação manipula somente o schema próprio `sap_chamados_ai`. Não é preciso apagar tabelas nem reiniciar os dados de outros projetos.

### 5. Compilar a interface e iniciar o app

Ainda na raiz:

```powershell
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Mantenha esse terminal aberto. Após `Application startup complete`, acesse **http://127.0.0.1:8000**. Um único processo serve a interface compilada e a API; não é necessário iniciar Vite em outro terminal para esse teste.

Em um segundo PowerShell, confira a API:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/config
```

O primeiro deve informar `status: ok`; o segundo informa se o código de acesso está habilitado. Eles verificam a API, sem fazer uma pergunta ao modelo.

### 6. Encerrar e iniciar novamente

Use **Ctrl+C** no terminal da API. Nas próximas execuções, basta iniciar Uvicorn pelo comando da etapa 5. Compile novamente se mudar o frontend; execute `ingest` se mudar o conhecimento e quiser preparar os embeddings antes do uso. Reinicie a API após alterar `.env` ou prompts.

## Conferir o funcionamento no navegador

As perguntas abaixo usam os serviços reais e podem consumir créditos. Para começar com dados fictícios novos, use uma nova sessão do navegador; **Novo chat não reinicia os dados de negócio**.

| Verificação | Como testar | Resultado esperado |
| --- | --- | --- |
| Seleção de chamado | **Chamados → Ver detalhes → Anexar ao chat**. | Anexo aparece no compositor; anexar não chama a IA nem executa ação. |
| Orientação com fontes | Anexe C01 e pergunte por que restam 40 UN após receber 60 de 100. | Resposta fundamentada; números das fontes são clicáveis. |
| Falta de contexto | Anexe C05 e peça ajuda para o erro no recebimento. | Perguntas de esclarecimento, sem inventar os dados ausentes. |
| Falta de evidência | Anexe C06 e pergunte sobre `ZMM_999`. | Informa insuficiência de conhecimento; não inventa causa nem correção. |
| Preparação e recusa | Anexe C03, peça a correção, complete os dados solicitados e revise. Clique **Não, recusar**. | Preparar/revisar não altera o negócio; a recusa não registra recebimento. |
| Aprovação | Em sessão nova, anexe C07 e solicite receber 10 UN com data explícita válida. Revise e clique **Sim, autorizar**. | Recebimento simulado ocorre somente após o clique; saldo atualizado e resultado visível. |
| Pergunta geral | Remova o anexo e pergunte sobre o processo de recebimento. | Usa o RAG geral, sem consultar o pedido anterior ou propor alteração sem chamado. |
| Novo chat | Clique **Novo chat**. | Conversa e anexo limpos; alterações de negócio anteriores permanecem. |

Use **Fontes e detalhes** para conferir referências, evidências identificadas e etapas observáveis. Fontes oficiais abrem seus sites; regras internas abrem a identificação no próprio bloco. Não há popup ou conteúdo bruto do documento. O passo a passo não expõe raciocínio interno do modelo.

## Testes automatizados sem consumo de API

Execute na raiz; o app pode estar desligado. Esses testes usam banco temporário e provedor controlado, sem precisar de OpenRouter/Supabase acessíveis. Eles validam o código e as barreiras de aprovação, mas não comprovam a qualidade do modelo real.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check sap_assistant app.py tests scripts
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run build
```

## Falha de inicialização da API


Se a API falhar em `lifespan`, o aplicativo ainda não conseguiu preparar seus serviços. Os logs usam códigos de diagnóstico com orientações fixas, sem imprimir conexão, senha, SQL ou resposta bruta de provedor:

| Código | O que conferir |
| --- | --- |
| `SAP_STARTUP_CONFIG` | No `.env` local: `APP_ENV=local`, URL do banco e origem pública. Na hospedagem: `APP_ENV=cloud` e código de acesso. |
| `SAP_STARTUP_DB_CONNECTION` | URL completa do pooler, SSL e rede. Uma URL direta pode depender de IPv6. |
| `SAP_STARTUP_DB_AUTH` | Usuário completo do pooler e senha atual do banco, com caracteres reservados codificados. |
| `SAP_STARTUP_DB_PERMISSION` | Permissões necessárias somente ao schema do projeto. |
| `SAP_STARTUP_DB_VECTOR` | Extensão vector no projeto Supabase correto. |
| `SAP_STARTUP_DB_IDENTITY` | Identificação do schema próprio; não apagar ou sobrescrever schema incompatível. |
| `SAP_STARTUP_KNOWLEDGE_FILES` | `conhecimento/catalogo.json` e os arquivos referenciados no pacote. |

Outros códigos distinguem preparação do banco, sincronização do conhecimento e criação do cliente HTTP. O processo continua recusando inicialização incompleta; nenhuma alternativa local ou resposta mockada é ativada. Uma falha de `vc_handler` após a falha do lifespan pode ser secundária: corrigir primeiro o diagnóstico de inicialização e verificar novamente. Não foi comprovada a recuperação hospedada apenas pelos testes locais.

Se a página disser **Interface ainda não compilada**, execute `npm.cmd --prefix frontend run build` e reinicie a API. Se a porta 8000 estiver ocupada, encerre a instância anterior ou escolha outra porta e ajuste a origem/URL do navegador. **Não há fallback do aplicativo para banco local ou respostas mockadas.**

## Desenvolvimento com atualização automática

Opcional, para editar código. Esta alternativa usa dois terminais e substitui o modo compilado da etapa 5.

**Terminal 1, na raiz — API:**

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2, na raiz — interface:**

```powershell
npm.cmd --prefix frontend run dev
```

Abra **http://127.0.0.1:5173** (ou a URL indicada pelo Vite). O proxy encaminha `/api` à porta 8000 mantendo a origem. Se configurar uma origem explícita para esse modo, use `APP_PUBLIC_ORIGIN=http://127.0.0.1:5173` e reinicie a API. Encerre os dois terminais com Ctrl+C ao terminar.

## Testes com Supabase e OpenRouter reais

O `.env` precisa estar configurado. Os comandos abaixo são opcionais, **consomem créditos** e criam sessões fictícias próprias no schema do projeto. Escolha a verificação necessária; não é preciso executar todas para iniciar o app.

| Comando, a partir da raiz | Finalidade |
| --- | --- |
| `.\.venv\Scripts\python.exe -m sap_assistant.cli check-provider` | Conferir chat e embeddings com chamadas reais. |
| `.\.venv\Scripts\python.exe scripts/verify_web_live.py` | API, fontes, falta de evidência, Novo chat e decisões Sim/Não simuladas pelo teste. |
| `.\.venv\Scripts\python.exe scripts/verify_corrections_live.py` | Correção guiada de C03 e confirmação separada. |
| `.\.venv\Scripts\python.exe scripts/verify_live.py` | Verificação ampliada, incluindo isolamento e integridade das aprovações. |

### Testes de navegador com serviços reais

Requer Microsoft Edge instalado. Na raiz, após instalar dependências de desenvolvimento e preparar o RAG:

```powershell
npm.cmd --prefix frontend run build
$env:RUN_REAL_USER_TESTS='1'
$env:USER_TEST_RUN='minha-rodada'
npm.cmd --prefix frontend run test:usuario:real
```

Use um nome novo para cada rodada. O runner inicia sua própria API na porta 8011 e a encerra ao terminar; não precisa do app da porta 8000. Não executa deploy ou limpeza de tabelas externas. As decisões são automatizadas, não cliques de uma pessoa. Transcrições e capturas ficam em `evidencias/jornadas-usuario/`; não são gravados vídeos/traces com cookies. [Resultados e limites](evidencias/README.md).

## Dados e aprovação humana

Somente o schema **`sap_chamados_ai`** é criado/utilizado pela aplicação, com identificação própria. As tabelas são `sap_project_identity`, `sap_workspaces`, `sap_messages`, `sap_knowledge`, `sap_proposals` e `sap_audit`. Um schema sem identificação compatível impede a inicialização; não há DROP/reset global. O acesso é pelo servidor Python, sem expor o schema pela Data API. SQLite é exclusivo dos testes.

Toda alteração de negócio exige proposta exata e aprovação no servidor, válida por 15 minutos. **Preparar correção → Revisar ação** cria somente a proposta; **Sim, autorizar** executa. Recusa, silêncio, parâmetros/dados alterados ou clique repetido não geram autorização nova. Digitar “sim” no chat não executa nada. Sem anexo, não há proposta de negócio; para decidir uma proposta anterior, reanexe seu chamado original. [Política completa](instrucoes/07-aprovacoes-humanas.md).

Antes de responder sobre SAP, o sistema verifica se a base sustenta a pergunta atual e valida as citações. Sem evidência suficiente, informa a limitação, sem diagnóstico ou proposta. A confiança é qualitativa; a avaliação semântica usa LLM e continua sujeita à revisão.

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

## Deploy na Vercel com dois serviços

O teste local acima funciona sem deploy. Para publicar, a configuração em [vercel.json](vercel.json) separa `app` (FastAPI em `/api` e `/api/*`) e `frontend` (Vite nos demais caminhos), no mesmo domínio. As chamadas partem do navegador; não há bindings internos entre funções desses serviços.

As variáveis locais não são enviadas à Vercel. Cadastre as variáveis no ambiente correspondente, usando `APP_ENV=cloud`, código de acesso com pelo menos 12 caracteres, origem pública HTTPS e URL completa do pooler. Salvar uma variável exige novo deploy para aplicá-la. Validação local não comprova funcionamento hospedado.

Consulte [configuração Vercel, limites e teste com vercel dev](instrucoes/09-execucao-e-entrega.md#vercel-services-e-execução-portátil) para os comandos e detalhes. No Linux/macOS, adapte os executáveis: `npm` em vez de `npm.cmd`, e `.venv/bin/python` em vez de `.venv\Scripts\python.exe`.

## Conhecimento, testes e decisões

- [Catálogo do conhecimento](conhecimento/catalogo.json): 12 guias; dez sínteses de nove fontes oficiais e duas políticas simuladas. Nenhum gabarito é indexado.
- [Instruções e decisões](instrucoes/README.md): requisitos, processo SAP, prompts, arquitetura, interface e segurança.
- [Evidências](evidencias/README.md): resultados observados, versões e limitações. Relatórios antigos de Streamlit são históricos.
