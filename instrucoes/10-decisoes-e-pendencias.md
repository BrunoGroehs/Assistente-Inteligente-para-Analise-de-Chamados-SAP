# Decisões e pendências

## Histórico

**Classificação:** decisões confirmadas pelo usuário ou pelo plano aprovado. Data de registro: 18/10/2026. Recomendações adicionais estão identificadas nos documentos responsáveis.

| ID | Decisão | Motivo e referência |
| --- | --- | --- |
| D01 | Primeira entrega somente documental, com `AGENTS.md` e `instrucoes/` | Organizar requisitos antes da implementação; [índice](README.md). |
| D02 | SAP MM, recebimento com referência a pedido de compra | Recorte coerente para diagnóstico, RAG e HITL; [processo](02-processo-sap.md). |
| D03 | Oito chamados fictícios | Atende ao intervalo de 5 a 10 do PDF; [casos](02-processo-sap.md). |
| D04 | Python + Streamlit | Direção do plano aprovado para concentrar esforço em SAP, IA e segurança; [arquitetura](03-arquitetura.md). |
| D05 | Substituir a escolha inicial React + FastAPI | Alternativa discutida, inclusive Vercel; Streamlit foi escolhido no plano final aprovado; [entrega](09-execucao-e-entrega.md). |
| D06 | Supabase/PostgreSQL com pgvector | Persistência externa e recuperação vetorial; [RAG](04-rag-e-fontes.md). |
| D07 | Qwen3.6 Plus via OpenRouter | Modelo indicado pelo usuário; embeddings inicialmente Qwen3 Embedding 0.6B pela mesma plataforma; [arquitetura](03-arquitetura.md). |
| D08 | Lista lateral de chamados com chat e detalhes expansíveis | Preferência confirmada na conversa; [interface](06-interface.md). |
| D09 | HITL em módulo determinístico no servidor | Não exigir microsserviço; modelo só propõe; [aprovações](07-aprovacoes-humanas.md). |
| D10 | Aprovação para alterações de negócio, não para todo POST técnico | Interpretação confirmada de “não GET”; chat, buscas e logs automáticos; [política](07-aprovacoes-humanas.md). |
| D11 | Proposta específica, vinculada aos dados e válida por 15 minutos | Regra do plano aprovado contra reutilização de autorização; [HITL](07-aprovacoes-humanas.md). |
| D12 | Protótipo mais completo, desenvolvido em etapas | Sem limite rígido de duas horas; prompts continuam em discussão; [execução](09-execucao-e-entrega.md). |
| D13 | Interface clean, organizada, inspirada em iOS e sem excesso visual | Nova preferência explícita do usuário durante esta entrega; [interface](06-interface.md). |
| D14 | Perguntar diante de dúvida material | Nova orientação explícita do usuário; detalhes menores seguem a direção registrada; [AGENTS.md](../AGENTS.md). |
| D15 | Persistir na obtenção de fontes e pedir ajuda quando necessário | Usuário pode fornecer conteúdo, base de conhecimento ou dados mockados; não inventar dados indisponíveis; [RAG](04-rag-e-fontes.md). |

## Pendências e tratamento

**Pendências:** itens ainda não executados ou que exigirão validação. Não bloqueiam a conclusão desta organização documental.

| ID | Informação ou trabalho pendente | Próxima ação |
| --- | --- | --- |
| P01 | Edição/release precisa das fontes SAP | Catalogar antes de produzir instruções dependentes de versão; perguntar ao usuário se for necessário escolher ambiente específico. |
| P02 | Corpus próprio e condições de redistribuição | Curar sínteses, atribuição e metadados; pedir conteúdo ao usuário se as fontes necessárias não forem acessíveis. |
| P03 | Prompts finais e apresentação das respostas | Debater rascunhos com o usuário e avaliar versões; [prompts](05-prompts.md). |
| P04 | Configuração autenticada de OpenRouter e Supabase | Verificar ambiente na implementação; configurar segredos por canal apropriado, sem publicá-los no chat ou repositório. |
| P05 | Disponibilidade e contratos reais dos modelos | Fazer chamada de chat/embeddings e validar ferramentas, esquema e dimensão. Falha intermitente de página não equivale a falha da API. |
| P06 | Parâmetros da recuperação híbrida | Calibrar trechos, quantidade e relevância com consultas rotuladas, fora do índice. |
| P07 | Fixtures executáveis, datas e estado inicial dos oito chamados | Materializar os cenários descritos e seus gabaritos separados. |
| P08 | Código, testes, evidências e revisão visual | Implementar por etapas e registrar resultados reais; [testes](08-testes-e-avaliacao.md). |
| P09 | Publicação, acesso da banca e limites de consumo | Configurar na etapa de publicação, validar hospedado e ensaiar apresentação. |

## Como incorporar novos pedidos

**Decisão confirmada:** atualizar primeiro o documento responsável. Se o pedido modificar uma escolha, acrescentar decisão com data/motivo, marcar a anterior como substituída e revisar referências afetadas. Se for uma dúvida sem resposta, registrar pendência em vez de criar uma decisão falsa.

Não usar este histórico como substituto para corrigir a especificação principal. Não manter duas stacks ou políticas de aprovação simultaneamente ativas por falta de atualização.

**Próximo passo recomendado:** discutir os prompts e revisar os guias que formarão a base antes de implementar o atendimento integrado. Tarefas técnicas independentes, como simulador e gateway, podem avançar quando a implementação for solicitada.
