# RAG, fontes e fundamentação

## Catálogo inicial

**Decisão confirmada:** conhecimento sobre recebimento de pedidos de compra em SAP MM. As fontes abaixo são candidatas à curadoria, não documentos já ingeridos. Consulta de pesquisa: 18/10/2026. As páginas S01 a S03 foram acessadas; nenhuma release numérica foi confirmada nessa leitura.

| ID | Fonte oficial | Uso na base futura | Limites de aplicação |
| --- | --- | --- | --- |
| S01 | SAP Learning: [Posting a Goods Receipt](https://learning.sap.com/courses/business-processes-in-sap-s-4hana-sourcing-procurement/posting-a-goods-receipt) | Conceitos de conferência, vínculo com pedido e atualização do histórico. | SAP S/4HANA; validar edição/release antes de orientações específicas. |
| S02 | SAP Learning: [Posting a Goods Receipt with Reference](https://learning.sap.com/courses/inventory-management-and-physical-inventory-in-sap-s-4hana/posting-a-goods-receipt-with-reference) | Referências de recebimento, dados necessários e diferenças entre MIGO e aplicativos Fiori. | Distinguir as restrições de cada aplicativo; não universalizar limitações. |
| S03 | SAP Learning: [Using the Advanced Transaction for Goods Receipt](https://learning.sap.com/courses/business-processes-in-sap-s-4hana-sourcing-procurement/using-the-advanced-transaction-for-goods-receipt) | Contexto de uso da MIGO e consulta da situação do estoque. | Material didático; não comprova configuração de um cliente real. |

**Recomendação:** complementar com SAP Help Portal para a versão escolhida e documentação de tolerâncias apenas quando necessário ao recorte. SAP Notes e KBAs restritos são referências de descoberta; prévia pública não equivale ao texto completo. Conteúdo comunitário pode ajudar a localizar uma hipótese, mas não substituir uma fonte técnica validada.

Não há corpus de chamados reais fornecido. Os chamados e o estado do simulador serão próprios e fictícios. Uma base pública acessível não é automaticamente licenciada para redistribuição integral: produzir sínteses próprias, manter atribuição e verificar condições de uso antes de copiar documentos.

## Material a preparar

**Recomendação:** produzir cinco guias curtos em português, em diretório de conhecimento separado destas instruções: visão do recebimento; conferência de pedido/item e quantidades; aplicativo e indicador de entrega concluída; esclarecimento e escalonamento; políticas do SAP simulado.

Cada guia deve conter origem e seção de referência, título, idioma, produto/edição, release identificada ou explicitamente desconhecida, data de consulta, tipo de conteúdo, revisão e assuntos cobertos. Usar os tipos `sintese_de_fonte_oficial` e `politica_da_simulacao`; a política simulada não deve parecer um documento publicado pela SAP.

Preservar o vínculo entre guia, trecho e URL. Citar a síntese local com o documento oficial de origem, sem apresentar uma síntese como citação literal. Separar conhecimento procedimental das consultas de dados do simulador.

**Decisão confirmada:** instruções do repositório, prompts, credenciais, gabaritos e resultados esperados dos testes nunca entram no índice SAP. Um teste positivo não pode ser resolvido recuperando seu próprio resultado esperado.

## Ingestão e recuperação

**Decisão confirmada:** embeddings inicialmente `qwen/qwen3-embedding-0.6b` pelo OpenRouter, armazenados em PostgreSQL/pgvector; busca híbrida textual e vetorial.

**Recomendação:** dividir guias por seção coerente, preservar cabeçalhos e termos SAP e gerar IDs estáveis. Deduplicar por hash do conteúdo e registrar modelo e revisão dos embeddings. Reindexar quando modelo, dimensão ou conteúdo mudar; não misturar espaços vetoriais incompatíveis.

Recuperar candidatos por termos/códigos e por significado, combinar as classificações e selecionar trechos úteis sem duplicação. Aplicar filtros de processo, produto e versão quando conhecidos. A versão desconhecida não deve receber uma precisão que não existe. Os valores de tamanho de trecho, quantidade recuperada e corte de relevância são **pendências de calibração**, a registrar após a primeira avaliação; não usar um limiar arbitrário como garantia de verdade.

Documentação de integração: [embeddings no OpenRouter](https://openrouter.ai/docs/api_reference/embeddings), [modelo inicial](https://openrouter.ai/qwen/qwen3-embedding-0.6b) e [pgvector no Supabase](https://supabase.com/docs/guides/database/extensions/pgvector). A identificação do modelo foi pesquisada; acesso autenticado e geração de vetores ainda não foram testados. O acesso à página do modelo apresentou falha intermitente na revisão documental: isso não comprova indisponibilidade da API.

## Evidências e confiança

**Requisito do PDF:** informar fontes e nível de confiança, evitando respostas sem fundamentação.

**Recomendação:** o modelo referencia somente IDs entregues no contexto. O servidor rejeita IDs inexistentes e monta links a partir do catálogo; o modelo não inventa URLs. Verificar separadamente a existência da fonte e se ela sustenta a afirmação, pois um ID válido pode ser citado fora de contexto.

Mostrar quais documentos foram recuperados e quais foram efetivamente citados. Dados transacionais devem aparecer como consulta ao simulador, com ID e versão, sem URL oficial fictícia. Não enviar a base inteira ao modelo.

| Confiança recomendada | Evidência necessária | Comportamento |
| --- | --- | --- |
| Alta | Fonte aplicável e fatos suficientes, sem conflito relevante. | Orientação fundamentada; escrita continua exigindo HITL. |
| Média | Evidência parcial ou contexto ainda incompleto. | Formular hipótese delimitada e pedir esclarecimento. |
| Baixa | Ausência, conflito relevante ou incompatibilidade de evidências. | Explicar a lacuna e pedir validação humana; não propor correção sem suporte. |

A confiança descreve suficiência das evidências, não probabilidade estatística nem autoconfiança numérica do LLM. A falta de suporte para uma correção específica não impede uma pergunta de esclarecimento segura.

## Fontes indisponíveis

**Decisão confirmada:** tentar novamente por meio adequado e procurar fontes oficiais equivalentes. Registrar falha, URL e informação faltante. Se não for possível obter a informação necessária, pedir ao usuário conteúdo, documento, base acessível ou dados mockados, conforme as [regras globais](../AGENTS.md).

Não contornar login, copiar de fontes não verificadas como se fossem oficiais ou completar lacunas por invenção. Se o usuário fornecer mocks, registrar quem os forneceu, seu escopo e que representam a simulação. Prosseguir com tarefas independentes enquanto a lacuna é resolvida.
