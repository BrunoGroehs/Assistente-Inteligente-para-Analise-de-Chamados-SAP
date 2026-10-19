# Instruções do desafio SAP

**Atualizado em:** 18/10/2026. **Estado:** protótipo implementado e validado funcionalmente; revisão estética e publicação posteriores. Consulte o [README de execução](../README.md) e as [evidências](../evidencias/README.md) para os resultados efetivamente verificados.

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
| [08 - Testes e avaliação](08-testes-e-avaliacao.md) | Casos de aceite, métricas, evidências executadas e limites. |
| [09 - Execução e entrega](09-execucao-e-entrega.md) | Etapas, configuração, publicação e demonstração. |
| [10 - Decisões e pendências](10-decisoes-e-pendencias.md) | Histórico, alternativas, perguntas e próximos passos. |

## Legenda de estado

- **Requisito do PDF:** obrigação ou condição expressa no enunciado, com página indicada.
- **Decisão confirmada:** escolha do usuário ou do plano aprovado; novas preferências confirmadas também entram aqui.
- **Recomendação:** proposta técnica para a implementação; não é requisito do enunciado nem funcionalidade já entregue.
- **Pendência:** informação ou decisão ainda necessária. Uma pendência não bloqueia tarefas independentes dela.

O rótulo de uma seção vale para seus itens, salvo indicação diferente. Links externos são referências, não bases já ingeridas nem comprovação de comportamento do aplicativo.

## Direção atual

**Decisões confirmadas:** SAP MM, recebimento com referência a pedido de compra; Python/FastAPI + React/TypeScript/Vite; PostgreSQL/pgvector no Supabase em desenvolvimento e hospedagem; Qwen3.6 Plus e embeddings Qwen3 Embedding 8B pelo OpenRouter; HITL em módulo do servidor; oito chamados fictícios; chat único com anexo opcional e sem painel lateral; estilo clean inspirado em iOS; protótipo mais completo, desenvolvido por etapas. Todas as tabelas próprias ficam em `sap_chamados_ai`, preservando os demais projetos.

**Atualização confirmada:** corpus ampliado para 12 guias; fontes agrupadas com links diretos, sem conteúdo/popup na interface; verificação de cobertura antes da geração e mensagem explícita de insuficiência quando o RAG não sustentar a pergunta atual. Essas decisões substituem a apresentação anterior por popup.

**Atualização confirmada:** botão Chamados no compositor lista os casos, permite ver detalhes e anexar ao chat. O cartão do chamado pode ser removido ou substituído; perguntas sem anexo usam o RAG geral, sem dados/histórico do caso anterior nem propostas de alteração. Uma única linha do tempo preserva o contexto de cada mensagem. Isso substitui a lista lateral e a tela separada de listagem. Perfis de suporte seguem inspirados no SAP for Me; [processo](02-processo-sap.md) e [interface](06-interface.md).

**Otimização implementada:** navegação reutiliza a cópia visual exclusiva da sessão; análise/decisão/Atualizar recarregam o estado. Não autorizar operações pelo cache. Medições, validação de HITL com cartão antigo e limites da amostra estão nas [evidências](../evidencias/README.md).

**Atualização confirmada:** Novo chat limpa conversa e anexo sem reiniciar o simulador; histórico, cache e propostas são vinculados à conversa atual. Respostas mais curtas, com um próximo passo quando útil e um único Fontes e detalhes recolhido. Ver [interface](06-interface.md) e [prompts](05-prompts.md).

**Pendências principais:** revisão visual em navegador e teclado, calibração com corpus maior, discussão dos prompts e publicação quando solicitada. A avaliação funcional integrada está registrada nas [evidências](../evidencias/README.md), com [cobertura dos requisitos](../evidencias/verificacao-requisitos.md). Configuração real e resultados de testes devem ser consultados nesses relatórios, sem confundir histórico documental com estado atual.

Novas solicitações devem atualizar seu documento responsável e, se alterarem uma escolha, o [histórico](10-decisoes-e-pendencias.md).

**Atualização confirmada:** Streamlit removido. Aplicação portátil com frontend compilado servido pela API, navegação local no navegador e sem plataforma de hospedagem definida. Deploy manual posterior pelo usuário. [Arquitetura](03-arquitetura.md), [execução](09-execucao-e-entrega.md) e decisão D33.
