# Decisões e pendências

## Histórico

**Classificação:** decisões confirmadas pelo usuário ou pelo plano aprovado. Data de registro: 18/10/2026. Recomendações adicionais estão identificadas nos documentos responsáveis.

| ID | Decisão | Motivo e referência |
| --- | --- | --- |
| D01 | Primeira entrega somente documental, com `AGENTS.md` e `instrucoes/` | Organizar requisitos antes da implementação; [índice](README.md). |
| D02 | SAP MM, recebimento com referência a pedido de compra | Recorte coerente para diagnóstico, RAG e HITL; [processo](02-processo-sap.md). |
| D03 | Oito chamados fictícios | Atende ao intervalo de 5 a 10 do PDF; [casos](02-processo-sap.md). |
| D04 | Python + Streamlit — substituída por D33 | Direção do plano aprovado para concentrar esforço em SAP, IA e segurança; [arquitetura](03-arquitetura.md). |
| D05 | Substituir a escolha inicial React + FastAPI — substituída por D33 | Alternativa discutida, inclusive Vercel; Streamlit foi escolhido no plano final aprovado; [entrega](09-execucao-e-entrega.md). |
| D06 | Supabase/PostgreSQL com pgvector | Persistência externa e recuperação vetorial; [RAG](04-rag-e-fontes.md). |
| D07 | Qwen3.6 Plus via OpenRouter | Modelo indicado pelo usuário; embeddings inicialmente Qwen3 Embedding 0.6B pela mesma plataforma; [arquitetura](03-arquitetura.md). |
| D08 | Lista lateral de chamados — substituída por D29 | Histórico da navegação anterior; chat atual usa anexo opcional sem painel lateral. |
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
| D21 | Citações do RAG com popup do trecho utilizado — substituída por D23 | Histórico do primeiro pedido; snapshots permanecem internos para auditoria. |
| D22 | Ampliar testes e utilizar a API real | Pedido explícito para verificar HITL e demais critérios; autorização para consumo da API nos testes, com evidências e decisões humanas simuladas identificadas. |
| D23 | Substituir popup e conteúdo exibido por links diretos organizados | Novo pedido: agrupar URLs, separar fontes citadas/consultadas e abrir documentação oficial; manter textos apenas internamente. |
| D24 | Ampliar o corpus de conhecimento | Novo pedido: 12 guias, com sete novos conteúdos oficiais relacionados ao recebimento; sem ampliar operações executáveis. |
| D25 | Exigir suporte no RAG antes de responder | Novo pedido: mensagem explícita de insuficiência sem diagnóstico/proposta; verificação de cobertura e de IDs antes da geração. |
| D26 | Quatro sínteses oficiais mais as duas políticas como contexto obrigatório | Detalhe técnico da recuperação após a expansão: a primeira rodada omitiu as regras do simulador e bloqueou uma proposta válida; substitui o limite anterior de quatro guias misturados. |
| D27 | Selecionar chamados junto ao chat e pela lista completa — refinada por D29 | Histórico: a seleção abria a conversa do caso e mantinha a lateral. Usuário esclareceu que deseja anexar/remover o chamado na mesma conversa. |
| D28 | Aproximar o formato dos chamados do SAP for Me | Pedido do usuário: conferir uso SAP de “ticket”. Fontes oficiais usam case; perfis fictícios incluem contexto, componente sugerido, prioridade, impacto e reprodução. IDs/situações permanecem locais, sem envio à SAP nem migração de sessões antigas; [processo](02-processo-sap.md). |
| D29 | Chat único, sem painel lateral, com chamado como anexo opcional | Esclarecimento explícito do usuário: botão lista chamados, detalhes e Anexar ao chat; cartão removível como arquivo do GPT; perguntas gerais sem anexo. Histórico preservado com contexto por mensagem; sem anexo não há consulta transacional ou proposta de negócio. Substitui D08 e o fluxo de navegação de D27; [interface](06-interface.md). |
| D30 | Reduzir consultas repetidas nos cliques — recomendação técnica implementada | Usuário relatou lag e apontou Streamlit. Medição: cinco SELECTs e cerca de 2,7 s por interação simples. Snapshot exclusivo da sessão, leitura em lote e invalidação após análise/decisão/Atualizar; autorização sempre revalidada no banco. A manutenção de Streamlit nesta correção foi substituída por D33 após o novo pedido do usuário. [Arquitetura](03-arquitetura.md). |
| D31 | Novo chat com contexto independente | Pedido explícito: limpar conversa, anexo e rascunho sem apagar histórico nem resetar dados de negócio. Histórico, cache e propostas vinculados à conversa; nenhuma autorização é transferida. [Arquitetura](03-arquitetura.md). |
| D32 | Respostas com menos opções e blocos | Pedido explícito: resumo direto, um próximo passo quando útil e um único Fontes e detalhes fechado por padrão. Não remover alertas, fundamentação ou o cartão de aprovação. [Interface](06-interface.md) e [prompts](05-prompts.md). |

**Decisão confirmada — D33, 18/10/2026:** remover Streamlit por travadas percebidas pelo usuário. A stack atual é React + TypeScript/Vite na interface e Python/FastAPI na API, preservando Supabase, OpenRouter, RAG e HITL. Substitui escolhas anteriores de Streamlit e Community Cloud; essas linhas permanecem como histórico. Entregar sem plataforma de deploy definida; o usuário adicionará hospedagem manualmente. Navegação local no navegador, etapas por NDJSON, cookie HttpOnly e build servido na mesma origem. Não publicar nem deixar processo local de teste ativo. Ver [arquitetura](03-arquitetura.md) e [execução](09-execucao-e-entrega.md).

**Decisão confirmada — D34, 18/10/2026:** toda correção executável identificada oferece caminho visual para aprovação: proposta completa com Sim/Não, ou preparação guiada quando faltarem parâmetros. “Altere para mim” preserva o recebimento discutido, sem pressupor mudança de status. Formulário não executa; gateway confirma a proposta exata. Citações numéricas conhecidas abrem fonte oficial ou identificação da regra interna, inclusive nas respostas antigas; sem popup de conteúdo. [Interface](06-interface.md), [aprovações](07-aprovacoes-humanas.md) e [prompts](05-prompts.md).

**Decisão confirmada — D35, 19/10/2026:** executar conversas como usuário com perguntas variadas, múltiplos chats e verificação de respostas/links. Edge headless e serviços reais para testes; cliques automatizados são identificados como tal. A inspeção encontrou necessidade de responder diretamente sobre o estado do anexo e evitar garantia de lançamento por MIGO sem evidência aplicável; correções e retestes têm [evidências separadas](../evidencias/jornadas-usuario/README.md).

**Decisão confirmada — D36, 19/10/2026:** manter no repositório os arquivos do aplicativo, conhecimento, instruções técnicas e evidências de validação. Remover materiais pessoais de apoio e suas referências; excluir relatórios temporários do navegador pelo `.gitignore`.

## Pendências e tratamento

**Estado atualizado:** itens concluídos e pendências remanescentes; consultar as evidências antes de declarar uma nova capacidade validada.

| ID | Informação ou trabalho pendente | Próxima ação |
| --- | --- | --- |
| P01 | Edição/release precisa das fontes SAP | Catalogar antes de produzir instruções dependentes de versão; perguntar ao usuário se for necessário escolher ambiente específico. |
| P02 | Corpus ampliado para 12 guias | Dez sínteses de nove fontes oficiais e duas políticas próprias; manter atribuição e pedir conteúdo ao usuário se uma expansão necessária não puder ser acessada. |
| P03 | Prompts finais e apresentação das respostas | Debater rascunhos com o usuário e avaliar versões; [prompts](05-prompts.md). |
| P04 | Configuração autenticada concluída localmente | Usuário configurou `.env`; Supabase e OpenRouter verificados sem versionar credenciais. Configuração de hospedagem ainda pendente. |
| P05 | Modelos atuais verificados | Chat Qwen3.6 Plus e embeddings 8B/4.096 dimensões testados; saídas e referências validadas pelo servidor. Revalidar se o provedor mudar. |
| P06 | Parâmetros iniciais implementados; calibração ampla pendente | Quatro sínteses mais duas políticas, busca textual/cosseno, RRF 60 e checagem de cobertura; avaliar relevância, falsos bloqueios e sustentação com rótulos fora do índice. |
| P07 | Fixtures executáveis concluídas | Oito chamados com datas explícitas em C07/C08, perfis de suporte fictícios para novas sessões e gabaritos fora da base; C05 preserva lacunas. |
| P08 | Jornadas e revisão funcional realizadas; validação ampla pendente | 187 Python, 14 React e 15 cenários de navegador com evidência final aprovada; 38 perguntas e capturas desktop/estreitas inspecionadas. Acessibilidade completa, outros navegadores e dispositivos reais continuam pendentes. |
| P09 | Publicação, acesso da banca e limites de consumo | Configurar na etapa de publicação, validar o ambiente hospedado. |
| P10 | PDF original ausente no diretório de trabalho | Remoção já existente fora desta migração; mantida fora dos commits. O link em `01-desafio.md` depende de disponibilizar novamente o arquivo. Requisitos transcritos foram preservados. |

## Como incorporar novos pedidos

**Decisão confirmada:** atualizar primeiro o documento responsável. Se o pedido modificar uma escolha, acrescentar decisão com data/motivo, marcar a anterior como substituída e revisar referências afetadas. Se for uma dúvida sem resposta, registrar pendência em vez de criar uma decisão falsa.

Não usar este histórico como substituto para corrigir a especificação principal. Não manter duas stacks ou políticas de aprovação simultaneamente ativas por falta de atualização.

**Próximo passo recomendado:** revisar a interface em execução e discutir os prompts com o usuário; depois preparar a publicação quando solicitada. Expansão da base e calibração de qualidade permanecem evoluções posteriores, sem bloquear o uso do protótipo.
