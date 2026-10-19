# Execução futura, publicação e entrega

## Estado e preparação

**Decisão confirmada:** implementação autorizada em 18/10/2026. O aplicativo executável, os comandos e as configurações atuais estão no [README principal](../README.md). Este documento preserva o roteiro e os critérios de evolução; os resultados concluídos estão nas [evidências](../evidencias/README.md).

**Estado implementado:** Python 3.12, dependências diretas fixadas após validar compatibilidade e entrada Streamlit na raiz. Domínio, infraestrutura, interface, conhecimento e testes estão separados. O README principal contém os comandos de preparação e execução; manter suas instruções alinhadas ao código e aos resultados verificados.

| Configuração proposta | Finalidade | Tratamento |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | Chat e embeddings | Segredo somente no servidor. |
| `OPENROUTER_CHAT_MODEL` | `qwen/qwen3.6-plus` | Valor configurável e registrado por análise. |
| `OPENROUTER_EMBEDDING_MODEL` | `qwen/qwen3-embedding-8b` | Validar disponibilidade e dimensão antes de criar o índice. |
| `DATABASE_URL` | PostgreSQL no Supabase | Conexão segura com pool adequado ao ambiente e privilégio mínimo. |
| `DEMO_ACCESS_CODE` | Acesso restrito à demonstração | Recomendação de acesso simples para banca, validado no servidor e nunca enviado ao LLM. |

Não solicitar segredos no chat. O usuário configurou `.env` localmente e ativou vector. O aplicativo usa Supabase em desenvolvimento e hospedagem; somente os testes usam SQLite temporário. Todos os objetos próprios ficam em `sap_chamados_ai`, com verificação de identificação; não modificar tabelas dos outros projetos, executar DROP ou reset global. Publicação externa ainda não foi solicitada. Para uso público além da banca, reavaliar autenticação, limites e privacidade.

## Etapas e saídas verificáveis

**Recomendação:**

1. **Núcleo e dados:** materializar oito fixtures, contratos e simulador; garantir consultas e regras de negócio independentes da UI. Saída: testes determinísticos do domínio.
2. **Conhecimento e RAG:** curar guias, registrar metadados, validar embeddings e criar busca híbrida. Saída: evidências relevantes para os casos, sem gabarito no índice.
3. **HITL:** gateway, propostas, validade, transações, idempotência e isolamento. Saída: escrita impossível sem autorização e testes de exceção aprovados.
4. **Interface:** lista, chat, detalhes e cartões, seguindo a [direção visual](06-interface.md). Saída: atendimento integrado e validação manual desktop/tela estreita.
5. **Validação e publicação:** executar matriz relevante, registrar falhas e resultados, preparar secrets e acesso restrito. Publicar somente na etapa correspondente, sem alegar funcionamento antes do teste hospedado.
6. **Entrega:** README, diagrama, base, chamados, decisões, testes, limitações e ensaio da demonstração.

O fluxo HITL pode ser testado antes do LLM real, usando propostas controladas. Isso valida a barreira; não substitui a rodada integrada com o OpenRouter.

## Hospedagem escolhida e alternativas

**Decisão confirmada do plano aprovado:** Streamlit Community Cloud para a aplicação e Supabase/PostgreSQL com pgvector para persistência externa. Configurar dependências, arquivo de entrada e secrets pelo ambiente da hospedagem. A [documentação de publicação](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) descreve o vínculo com GitHub. Revalidar condições e disponibilidade dos serviços na ocasião; não prometer gratuidade permanente.

**Recomendação:** validar primeiro conexão ao banco, esquema, geração de embeddings e chamada de chat. Ingestão deve ser uma operação controlada, sem reconstruir embeddings a cada rerun. Dados locais podem ser cache descartável, nunca prova durável de autorização.

React + FastAPI na Vercel foi considerado e substituído pela simplicidade de Streamlit para o desafio; não é inviável. A [Vercel documenta FastAPI](https://vercel.com/docs/frameworks/backend/fastapi). Rever a decisão se a interface exigir recursos que Streamlit não atender; registrar a mudança e preservar o núcleo Python e o gateway de autorização.

## Riscos e evolução

| Risco ou limitação | Tratamento recomendado |
| --- | --- |
| Diferenças de versão e configuração SAP | Metadados, orientações delimitadas e revisão humana; não alegar validação em SAP real. |
| LLM inventar causa ou citar fonte inadequada | Recuperação, contratos, verificação factual e abstinência quando faltar evidência. |
| Documento ou página inacessível | Retentativa, alternativa oficial e colaboração do usuário conforme [RAG](04-rag-e-fontes.md). |
| Custo ou indisponibilidade do provedor | Acesso restrito, limites por sessão, cache de embeddings e falha explícita. |
| Reinício e rerun | Estado durável, IDs de submissão e execução idempotente. |
| Exposição de credenciais ou sessões | Segredos no servidor, escopo por sessão e logs sem credenciais. |
| Simulação confundida com integração SAP | Aviso discreto, resultados identificados como simulados e limitações na apresentação. |

Para futura integração real, adotar adaptador com APIs autorizadas, identidade com privilégio mínimo, separação de leitura/escrita, auditoria e autorização humana preservada. Avaliar conciliação de operações remotas e regras reais do processo antes de habilitar qualquer escrita. Não usar o modelo como cliente HTTP irrestrito.

## Demonstração de até 20 minutos

**Requisito do PDF:** até 20 minutos. **Recomendação de roteiro de 18 minutos, com dois de reserva:**

| Tempo | Conteúdo |
| --- | --- |
| 0 a 2 min | Trabalho manual transformado, recorte SAP MM e adequação da GenAI. |
| 2 a 5 min | Arquitetura, documentos, RAG, prompts e distinção entre dados simulados e fontes oficiais. |
| 5 a 8 min | C01: orientação fundamentada, fontes e confiança. |
| 8 a 11 min | C05/C06: esclarecimento, falta de evidência e validação humana. |
| 11 a 15 min | C07/C08: proposta, Sim/Não, estado antes/depois e limite de autonomia. |
| 15 a 18 min | Evidências reais, métricas, limitações, acesso futuro ao SAP e próximos passos. |

Se um serviço falhar, identificar a falha e usar evidências previamente coletadas como gravação ou execução anterior, devidamente rotuladas. Não apresentar um mock como demonstração ao vivo bem-sucedida.
