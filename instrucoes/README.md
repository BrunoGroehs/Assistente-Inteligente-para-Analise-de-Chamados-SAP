# Instruções do desafio SAP

**Atualizado em:** 18/10/2026. **Estado:** implementação autorizada e em validação. Consulte o [README de execução](../README.md) e as [evidências](../evidencias/README.md) para o estado efetivamente verificado.

Este diretório organiza os requisitos, as escolhas e os pontos a discutir do Assistente Inteligente para Análise de Chamados SAP. As regras globais estão no [AGENTS.md](../AGENTS.md).

## Como ler

Ler primeiro o desafio e o processo SAP; depois arquitetura, RAG, prompts, interface e aprovações. Consultar testes e entrega antes de implementar. O histórico registra por que as escolhas foram feitas.

| Documento | Responsabilidade |
| --- | --- |
| [01 - Desafio](01-desafio.md) | Requisitos do PDF, pesos, entregáveis e rastreabilidade. |
| [02 - Processo SAP](02-processo-sap.md) | Recorte de MM, dados simulados e oito chamados. |
| [03 - Arquitetura](03-arquitetura.md) | Componentes, fluxo, persistência e contratos. |
| [04 - RAG e fontes](04-rag-e-fontes.md) | Catálogo, curadoria, recuperação e fundamentação. |
| [05 - Prompts](05-prompts.md) | Estratégia e rascunhos abertos à discussão. |
| [06 - Interface](06-interface.md) | Chat, lista, detalhes, aprovações e direção visual. |
| [07 - Aprovações humanas](07-aprovacoes-humanas.md) | Barreira determinística, estados e execução segura. |
| [08 - Testes e avaliação](08-testes-e-avaliacao.md) | Casos de aceite, métricas e evidências futuras. |
| [09 - Execução e entrega](09-execucao-e-entrega.md) | Etapas, configuração, publicação e demonstração. |
| [10 - Decisões e pendências](10-decisoes-e-pendencias.md) | Histórico, alternativas, perguntas e próximos passos. |

## Legenda de estado

- **Requisito do PDF:** obrigação ou condição expressa no enunciado, com página indicada.
- **Decisão confirmada:** escolha do usuário ou do plano aprovado; novas preferências confirmadas também entram aqui.
- **Recomendação:** proposta técnica para a implementação; não é requisito do enunciado nem funcionalidade já entregue.
- **Pendência:** informação ou decisão ainda necessária. Uma pendência não bloqueia tarefas independentes dela.

O rótulo de uma seção vale para seus itens, salvo indicação diferente. Links externos são referências, não bases já ingeridas nem comprovação de comportamento do aplicativo.

## Direção atual

**Decisões confirmadas:** SAP MM, recebimento com referência a pedido de compra; Python + Streamlit; PostgreSQL/pgvector no Supabase em desenvolvimento e hospedagem; Qwen3.6 Plus e embeddings Qwen3 Embedding 8B pelo OpenRouter; HITL em módulo do servidor; oito chamados fictícios; lista lateral e chat; estilo clean inspirado em iOS; protótipo mais completo, desenvolvido por etapas. Todas as tabelas próprias ficam em `sap_chamados_ai`, preservando os demais projetos.

**Pendências principais:** concluir a avaliação integrada dos casos, discutir os prompts e preparar a publicação quando solicitada. Configuração real e resultados de testes devem ser consultados nas evidências, sem confundir histórico documental com estado atual.

Novas solicitações devem atualizar seu documento responsável e, se alterarem uma escolha, o [histórico](10-decisoes-e-pendencias.md).
