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
| D16 | Implementar o protótipo | Usuário autorizou seguir com a implementação após a entrega documental; D01 permanece como histórico da primeira etapa. |
| D17 | Supabase também durante o desenvolvimento | Usuário confirmou preferência por não hospedar banco local; SQLite restrito aos testes temporários. |
| D18 | Preservar tabelas e dados de outros projetos | Schema exclusivo `sap_chamados_ai`, identificação própria e ausência de DROP/reset global. Extensão vector ativada pelo usuário. |
| D19 | Substituir embeddings 0.6B por 8B | API real retornou ausência de endpoint para 0.6B; usuário aprovou `qwen/qwen3-embedding-8b`. Chat permanece Qwen3.6 Plus; atualiza o detalhe de embeddings de D07. |
| D20 | Criar commits locais em português durante o trabalho | Pedido explícito do usuário para manter histórico; separar mudanças coerentes e excluir segredos. Push/publicação requerem solicitação correspondente. |

## Pendências e tratamento

**Estado atualizado:** itens concluídos e pendências remanescentes; consultar as evidências antes de declarar uma nova capacidade validada.

| ID | Informação ou trabalho pendente | Próxima ação |
| --- | --- | --- |
| P01 | Edição/release precisa das fontes SAP | Catalogar antes de produzir instruções dependentes de versão; perguntar ao usuário se for necessário escolher ambiente específico. |
| P02 | Corpus inicial concluído; expansão pendente | Cinco sínteses/políticas próprias catalogadas e indexadas; manter atribuição e pedir conteúdo ao usuário se uma expansão necessária não puder ser acessada. |
| P03 | Prompts finais e apresentação das respostas | Debater rascunhos com o usuário e avaliar versões; [prompts](05-prompts.md). |
| P04 | Configuração autenticada concluída localmente | Usuário configurou `.env`; Supabase e OpenRouter verificados sem versionar credenciais. Configuração de hospedagem ainda pendente. |
| P05 | Modelos atuais verificados | Chat Qwen3.6 Plus e embeddings 8B/4.096 dimensões testados; saídas e referências validadas pelo servidor. Revalidar se o provedor mudar. |
| P06 | Parâmetros iniciais implementados; calibração ampla pendente | Quatro guias por consulta, busca textual/cosseno e RRF 60; avaliar corpus maior com rótulos fora do índice. |
| P07 | Fixtures executáveis concluídas | Oito chamados com datas explícitas em C07/C08 e gabaritos fora da base. |
| P08 | Código e validação funcional concluídos; revisão estética pendente | 75 testes aprovados e dez atendimentos reais verificados. AppTest valida componentes; revisão visual em navegador precisa ocorrer na interface em execução. |
| P09 | Publicação, acesso da banca e limites de consumo | Configurar na etapa de publicação, validar hospedado e ensaiar apresentação. |

## Como incorporar novos pedidos

**Decisão confirmada:** atualizar primeiro o documento responsável. Se o pedido modificar uma escolha, acrescentar decisão com data/motivo, marcar a anterior como substituída e revisar referências afetadas. Se for uma dúvida sem resposta, registrar pendência em vez de criar uma decisão falsa.

Não usar este histórico como substituto para corrigir a especificação principal. Não manter duas stacks ou políticas de aprovação simultaneamente ativas por falta de atualização.

**Próximo passo recomendado:** revisar a interface em execução e discutir os prompts com o usuário; depois preparar a publicação quando solicitada. Expansão da base e calibração de qualidade permanecem evoluções posteriores, sem bloquear o uso do protótipo.
