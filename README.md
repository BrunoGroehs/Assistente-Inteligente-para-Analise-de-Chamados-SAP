# Assistente SAP MM

Protótipo para análise de chamados de recebimento de mercadorias com referência a pedidos de compra. Python e Streamlit na aplicação; Supabase/PostgreSQL com pgvector na persistência; Qwen3.6 Plus e Qwen3 Embedding 8B pelo OpenRouter.

O SAP é simulado. Nenhuma chamada executa transações SAP reais. Oito chamados fictícios estão disponíveis, com histórico isolado por sessão, fontes consultadas e propostas que precisam de aprovação humana.

## Executar no Windows

Python 3.12 é a versão validada. Na raiz do repositório:

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
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8507
```

Abra `http://127.0.0.1:8507`. O chat inicia sem chamado anexado e permite perguntas gerais sobre o processo pelo RAG. A ingestão gera embeddings com cobrança do OpenRouter; documentos inalterados usam o cache. A aplicação também prepara os guias automaticamente e gera embeddings faltantes na primeira consulta. Reinicie o processo após mudar o `.env`.

Não há painel lateral. Use **Chamados** no compositor para listar/buscar os casos, **Ver detalhes** para consultar e **Anexar ao chat** para incluir o contexto. O chamado aparece como um cartão removível, semelhante a um arquivo anexado. Você pode substituir ou **Remover anexo** e continuar perguntando na mesma conversa. Cada mensagem preserva seu contexto; novas perguntas sem anexo não herdam dados do caso anterior. Para analisar o anexo, escreva ou clique em **Analisar chamado**. Anexar/remover não chama a IA nem decide aprovações.

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

O “passo a passo” mostra operações observáveis, evidências e justificativas resumidas. Raciocínio interno bruto não é exibido ou usado como auditoria.

As respostas indicam as fontes do RAG por números e links que abrem diretamente a documentação oficial. URLs repetidas são agrupadas; fontes citadas, referências apenas consultadas e dados simulados têm áreas próprias. Não há exibição de `content`, trechos ou popup. Textos e metadados permanecem salvos internamente para recuperação e auditoria.

Antes de gerar a análise, uma chamada estruturada verifica se os trechos cobrem a pergunta atual. O servidor valida os IDs de parágrafo selecionados e exige citação do conhecimento aprovado. Sem suporte, retorna **“Não tenho informações suficientes na base de conhecimento...”**, sem diagnóstico, hipóteses ou proposta. Base vazia, código não documentado e prova inválida também bloqueiam a geração. A verificação semântica usa LLM e continua sujeita à avaliação de qualidade.

## Conhecimento, testes e decisões

- [Catálogo do conhecimento](conhecimento/catalogo.json): 12 guias próprios, sendo dez sínteses de nove fontes oficiais e duas políticas simuladas; nenhum gabarito é indexado.
- [Instruções e decisões](instrucoes/README.md): requisitos, arquitetura, diagramas, prompts e limites.
- [Evidências](evidencias/README.md): resultados locais e integrados, com limitações explícitas.
- [Roteiro de demonstração](instrucoes/09-execucao-e-entrega.md): sequência de até 20 minutos.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check sap_assistant app.py tests
```

Os testes padrão usam banco temporário e provedor controlado: não leem a chave nem consomem créditos. Não comprovam sozinhos a qualidade do modelo real. Não existe fallback de produção para respostas mockadas ou para outro modelo.

Para reproduzir a verificação ampliada com os serviços reais configurados no `.env`:

```powershell
.\.venv\Scripts\python.exe scripts/verify_live.py
```

Esse comando **consome créditos** e cria sessões fictícias próprias no schema do projeto. Verifica fontes diretas, novos conteúdos, perguntas sem suporte, regressões dos chamados e cliques Sim/Não, além de concorrência, isolamento, adulteração, expiração e rollback. Não altera tabelas externas nem injeta documentos na base compartilhada. Resultados atuais em [verificação de fontes/RAG](evidencias/verificacao-fontes-rag.json); cobertura e limites em [verificação dos requisitos](evidencias/verificacao-requisitos.md). Propostas pendentes anteriores ao novo envelope de integridade exigem nova análise; não são executadas usando o formato antigo.

Para verificar especificamente o chat único, perguntas gerais e anexos opcionais com os serviços reais: `.\.venv\Scripts\python.exe scripts/verify_chat_attachments_live.py`. Resultado desta rodada em [verificação dos anexos](evidencias/verificacao-anexos-chat.json). Os cliques são automatizados pelo AppTest; não representam revisão visual ou consentimento de uma pessoa.

## Publicar posteriormente

No Streamlit Community Cloud, use `app.py` como entrada e Python 3.12. Defina as configurações do `.env` em **Secrets**, no formato TOML, com `APP_ENV = "cloud"` e `DEMO_ACCESS_CODE` de pelo menos 12 caracteres. PostgreSQL externo é obrigatório. Não publique `.env`, não altere permissões de outros schemas e não use a chave do banco no navegador.

O código de acesso é uma proteção simples para uma demonstração restrita à banca; não substitui autenticação individual de produção. As sessões são isoladas, mas recarregar completamente a página pode iniciar outra sessão. A primeira versão não recupera histórico entre dispositivos.

O Supabase Free suporta o armazenamento/busca vetorial com pgvector dentro das cotas do plano; embeddings e chat são cobrados pelo OpenRouter. Confira as condições ao publicar: [Supabase](https://supabase.com/pricing), [pgvector](https://supabase.com/docs/guides/database/extensions/pgvector). Não há promessa de operação integralmente gratuita.

Limitações: base pequena, versões SAP não identificadas com precisão, confiança qualitativa, ausência de integração SAP real e necessidade de revisão humana para recomendações críticas. Similaridade vetorial e citações existentes não garantem a correção de cada afirmação. Os prompts implementados continuam abertos ao debate.
