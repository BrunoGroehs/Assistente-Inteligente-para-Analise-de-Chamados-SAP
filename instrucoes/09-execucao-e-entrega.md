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

Não solicitar segredos no chat. O usuário configurou `.env` localmente e ativou vector. O aplicativo usa Supabase em desenvolvimento e hospedagem; somente os testes usam SQLite temporário. Todos os objetos próprios ficam em `sap_chamados_ai`, com verificação de identificação; não modificar tabelas dos outros projetos, executar DROP ou reset global. O usuário fará o deploy manual posteriormente; não publicar nem escolher plataforma nesta etapa. Para uso público além da banca, reavaliar autenticação, limites e privacidade.

## Etapas e saídas verificáveis

**Recomendação:**

1. **Núcleo e dados:** materializar oito fixtures, contratos e simulador; garantir consultas e regras de negócio independentes da UI. Saída: testes determinísticos do domínio.
2. **Conhecimento e RAG:** curar guias, registrar metadados, validar embeddings e criar busca híbrida. Saída: evidências relevantes para os casos, sem gabarito no índice.
3. **HITL:** gateway, propostas, validade, transações, idempotência e isolamento. Saída: escrita impossível sem autorização e testes de exceção aprovados.
4. **Interface:** chat único, seletor em diálogo, anexo opcional e cartões de aprovação, seguindo a [direção visual](06-interface.md). Saída: atendimento integrado e validação manual desktop/tela estreita.
5. **Validação e publicação:** executar matriz relevante, registrar falhas e resultados, preparar secrets e acesso restrito. Publicar somente na etapa correspondente, sem alegar funcionamento antes do teste hospedado.
6. **Entrega:** README, diagrama, base, chamados, decisões, testes e limitações.

O fluxo HITL pode ser testado antes do LLM real, usando propostas controladas. Isso valida a barreira; não substitui a rodada integrada com o OpenRouter.

## Aplicação portátil e publicação manual

**Decisão confirmada, substituindo Streamlit/Community Cloud:** entregar aplicativo normal sem plataforma definida. React é compilado em `frontend/dist`; FastAPI serve a interface e `/api` na mesma origem. Comandos completos no [README](../README.md). Python 3.12 e Node.js 24.14 foram usados na validação. O usuário escolherá e configurará a hospedagem pelo site do serviço posteriormente.

**Recomendação:** executar build antes de iniciar Uvicorn; manter o diretório compilado no artefato; instalar dependências Python no servidor; configurar somente os segredos do `.env.example` no ambiente. Usar HTTPS, `APP_ENV=cloud` e código de demonstração de pelo menos 12 caracteres. Proxy deve preservar origem/host e streaming NDJSON, sem buffering e com timeout adequado. Não colocar chave ou conexão de banco em variáveis Vite do navegador.

Para execução normal há um único processo Uvicorn, sem Vite ativo. O servidor de desenvolvimento do Vite é opcional. Não deixar servidores locais de teste rodando ao encerrar o trabalho. Não há publicação automática, Docker obrigatório, configuração de plataforma ou mudança do Supabase nesta etapa.

Inicializar/verificar somente o schema do projeto e ingerir documentos alterados sem reconstruir embeddings desnecessariamente. A fila limitada é por processo; usar um processo inicialmente e avaliar coordenação distribuída antes de escalar. Testes React/HTTP não equivalem a revisão estética em navegador ou validação do ambiente hospedado.

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
