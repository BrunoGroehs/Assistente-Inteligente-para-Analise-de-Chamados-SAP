# Requisitos e rastreabilidade

**Classificação:** requisito do PDF, exceto quando identificado de outra forma.

Fonte: [Desafio Técnico - Consultor Pleno AI Advanced Assets](<../Desafio Técnico Consultor Pleno AI Advanced Assets.pdf>), quatro páginas, lidas em 18/10/2026. O PDF original deve ser preservado.

## Objetivo e condições

O assistente deve apoiar consultores que analisam dúvidas e incidentes SAP, reduzindo trabalho repetitivo sem perder confiabilidade. É necessário entregar proposta e protótipo funcional, escolher um módulo diferente de HR e criar entre cinco e dez chamados fictícios de um processo desse módulo (p. 1).

Dados, documentos, APIs e respostas SAP podem ser simulados; integração real não é obrigatória (p. 2). Agentes, ontologias, ferramentas externas e múltiplos modelos são opcionais, mas seu uso deve ser justificado. O tempo sugerido é de duas horas e a sofisticação visual não será avaliada (p. 3). Não se exige solução pronta para produção (p. 4).

**Decisão confirmada:** oito chamados de SAP MM; protótipo desenvolvido em etapas, sem limite rígido de duas horas. A organização documental foi entregue primeiro; a implementação foi autorizada em 18/10/2026.

## Matriz de requisitos

Esta matriz mantém a especificação do enunciado. O estado de verificação de cada comportamento está em [testes e avaliação](08-testes-e-avaliacao.md) e nas [evidências reais](../evidencias/README.md); um teste planejado não equivale a aprovação funcional.

| ID | Exigência e página | Documento responsável | Aceite futuro |
| --- | --- | --- | --- |
| R01 | Módulo permitido e 5 a 10 chamados de um processo (1) | [Processo](02-processo-sap.md) | Oito casos identificados, reproduzíveis e coerentes com MM. |
| R02 | Interpretar solicitação e identificar processo SAP (2) | [Prompts](05-prompts.md) | T01 e T02: resumo fiel e processo correto. |
| R03 | Consultar base fornecida pelo candidato; RAG ou fundamentação equivalente (2) | [RAG](04-rag-e-fontes.md) | T01: evidências recuperadas e identificáveis. |
| R04 | Pedir dados quando o chamado estiver incompleto (2) | [Prompts](05-prompts.md) | T05: pergunta direcionada sem inventar campos. |
| R05 | Apresentar causas possíveis, verificações e próximos passos (2) | [Processo](02-processo-sap.md) | T01 a T04: hipóteses separadas de fatos. |
| R06 | Informar fontes e confiança (2) | [RAG](04-rag-e-fontes.md) | T01, T06 e T18: fontes verificáveis e confiança justificada. |
| R07 | Encaminhar para validação humana por falta de informação ou risco (2) | [HITL](07-aprovacoes-humanas.md) | T06 a T08: revisão solicitada, sem execução autônoma. |
| R08 | Utilizar LLM e demonstrar Prompt Engineering (2) | [Arquitetura](03-arquitetura.md) e [prompts](05-prompts.md) | T01 e T19: chamada real identificada e prompts versionados. |
| R09 | Tratar perguntas fora do escopo (2) | [Prompts](05-prompts.md) | T09: resposta breve de limite e direcionamento. |
| R10 | Prevenir invenções e respostas sem evidências (2) | [RAG](04-rag-e-fontes.md) | T06, T10, T12 e T18. |
| R11 | Registrar solicitação, resposta e fontes (2) | [Arquitetura](03-arquitetura.md) | T01 e T17: registros correlacionados e persistentes. |
| R12 | Um sucesso e dois cenários de exceção, no mínimo (2) | [Testes](08-testes-e-avaliacao.md) | T01, T05 e T06, além de HITL aprovado/recusado. |
| R13 | Separar recomendação de ação dependente de autorização (2) | [Interface](06-interface.md) e [HITL](07-aprovacoes-humanas.md) | T07, T08 e T13 a T16: escrita somente após aprovação válida. |

## Entregáveis finais

**Requisito do PDF, p. 3:** código-fonte ou protótipo executável; README de execução; diagrama simples; base de conhecimento e chamados usados; justificativa das decisões; evidências de testes; riscos, limitações e próximos passos; demonstração de até 20 minutos.

**Recomendação:** controlar a conclusão por evidência: código executado, comandos verificados, artefatos de conhecimento versionados, relatório de testes e roteiro cronometrado. Esta documentação atende à preparação desses entregáveis; não substitui a demonstração funcional.

## Avaliação

| Critério do PDF | Peso |
| --- | ---: |
| Processo e conceitos SAP | 20% |
| Aplicação prática de IA Generativa | 20% |
| RAG, prompts e fundamentação | 20% |
| Erros, riscos, segurança e alucinações | 15% |
| HITL e limites de autonomia | 10% |
| Organização, clareza e qualidade técnica | 10% |
| Comunicação e demonstração | 5% |

Na apresentação, explicar a atividade manual transformada, adequação de GenAI, prevenção de respostas incorretas, critérios de esclarecimento e decisão humana, possível acesso seguro ao SAP real e medição de tempo, qualidade e produtividade (p. 3 e 4). O [roteiro](09-execucao-e-entrega.md) cobre esses pontos.
