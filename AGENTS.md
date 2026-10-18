# Instruções globais do projeto

## Objetivo e estado atual

Construir um assistente para análise de chamados SAP MM, no processo de recebimento de mercadorias com referência a pedidos de compra. O ambiente SAP, os chamados e as operações serão simulados.

**Decisão confirmada:** a etapa atual entrega documentação. Não apresentar código, RAG, aprovações, testes funcionais ou publicação como concluídos enquanto não existirem evidências. A implementação do aplicativo é uma etapa posterior.

## Leitura obrigatória

Antes de trabalhar, ler o [índice das instruções](instrucoes/README.md) e os documentos relacionados à tarefa. Referências principais:

- [Requisitos e rastreabilidade](instrucoes/01-desafio.md).
- [Processo SAP e chamados](instrucoes/02-processo-sap.md).
- [Arquitetura e contratos](instrucoes/03-arquitetura.md).
- [RAG e fontes](instrucoes/04-rag-e-fontes.md).
- [Prompts em discussão](instrucoes/05-prompts.md).
- [Interface](instrucoes/06-interface.md).
- [Aprovações humanas](instrucoes/07-aprovacoes-humanas.md).
- [Testes e avaliação](instrucoes/08-testes-e-avaliacao.md).
- [Execução e entrega](instrucoes/09-execucao-e-entrega.md).
- [Decisões e pendências](instrucoes/10-decisoes-e-pendencias.md).

## Manutenção das instruções

1. Incorporar cada nova solicitação relevante ao documento responsável, na mesma entrega da alteração. Atualizar o índice quando necessário.
2. Classificar informações como **requisito do PDF**, **decisão confirmada**, **recomendação** ou **pendência**. Não transformar recomendações ou rascunhos em decisões do usuário.
3. Registrar mudanças de direção no histórico de decisões, com data, motivo e decisão substituída. Corrigir os documentos afetados para evitar regras contraditórias.
4. Respeitar instruções atuais do usuário. Se uma solicitação comprometer um requisito obrigatório do desafio, explicar o conflito e esclarecer a intenção antes de alterar esse requisito.
5. Perguntar quando houver dúvida material sobre comportamento, escopo ou informação indisponível. Resolver detalhes de baixo impacto com base nas decisões registradas.
6. Manter Markdown em português, UTF-8, links relativos para arquivos locais e nomes estáveis. Evitar repetir regras extensas: referenciar seu documento responsável.

## Limites técnicos e de autonomia

- **Decisão confirmada:** Python, Streamlit, Supabase/PostgreSQL com pgvector; OpenRouter com `qwen/qwen3.6-plus` e embeddings inicialmente `qwen/qwen3-embedding-0.6b`.
- Toda alteração de negócio no SAP simulado ou nos chamados exige aprovação humana específica, validada no servidor. O modelo só propõe; nunca aprova nem acessa diretamente o executor.
- Mensagens, consultas e auditoria técnica são automáticas. O critério é o efeito da operação, não seu método HTTP. A política completa está em [aprovações humanas](instrucoes/07-aprovacoes-humanas.md).
- Usar somente dados fictícios. Não expor credenciais em código, interface, prompts ou logs. Isolar dados e aprovações por sessão.
- Apresentar fontes, etapas observáveis e justificativas resumidas. Não usar raciocínio interno bruto do modelo como trilha de auditoria.
- Não indexar instruções de desenvolvimento, gabaritos, prompts ou resultados esperados como conhecimento SAP.
- **Decisão confirmada:** interface organizada, clean, inspirada em iOS, com pouco ruído visual. Seguir [interface](instrucoes/06-interface.md).

## Fontes indisponíveis e colaboração

**Decisão confirmada do usuário:** não abandonar uma informação necessária porque um site falhou. Tentar novamente por meios adequados, conferir URL e buscar páginas oficiais equivalentes ou uma versão pública acessível, sem contornar autenticação ou restrições de acesso.

Se a lacuna continuar e bloquear a qualidade da entrega, pedir ao usuário o conteúdo necessário: texto, arquivo, referência acessível, base de conhecimento ou dados mockados. Explicar exatamente o que falta e em que formato ajudaria. Continuar o trabalho independente dessa informação e registrar a pendência. Nunca inventar conteúdo ausente, fingir consulta bem-sucedida ou trocar a fonte silenciosamente.

## Verificação e comunicação

- Validar links locais, consistência entre documentos e cobertura dos requisitos ao alterar esta documentação.
- Na implementação, executar os testes relevantes e registrar resultado real, versão, limitações e evidências; testes planejados não são testes aprovados.
- Distinguir diagnóstico provável, recomendação, solicitação de autorização e operação efetivamente executada.
- Ao concluir, informar o que mudou, o que foi verificado e as pendências que afetam a próxima etapa.
