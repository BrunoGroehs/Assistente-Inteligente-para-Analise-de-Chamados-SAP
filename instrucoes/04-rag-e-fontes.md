# RAG, fontes e fundamentação

## Catálogo inicial

**Decisão confirmada:** conhecimento sobre recebimento de pedidos de compra em SAP MM. Nove fontes oficiais fundamentam as sínteses próprias catalogadas em [conhecimento](../conhecimento/catalogo.json). Consulta de pesquisa: 18/10/2026. As páginas SAP Learning foram acessadas; nenhuma release numérica específica do ambiente foi confirmada. Os sites integrais não foram copiados nem indexados.

| ID | Fonte oficial | Uso na base futura | Limites de aplicação |
| --- | --- | --- | --- |
| S01 | SAP Learning: [Posting a Goods Receipt](https://learning.sap.com/courses/business-processes-in-sap-s-4hana-sourcing-procurement/posting-a-goods-receipt) | Conceitos de conferência, vínculo com pedido e atualização do histórico. | SAP S/4HANA; validar edição/release antes de orientações específicas. |
| S02 | SAP Learning: [Posting a Goods Receipt with Reference](https://learning.sap.com/courses/inventory-management-and-physical-inventory-in-sap-s-4hana/posting-a-goods-receipt-with-reference) | Referências de recebimento, dados necessários e diferenças entre MIGO e aplicativos Fiori. | Distinguir as restrições de cada aplicativo; não universalizar limitações. |
| S03 | SAP Learning: [Using the Advanced Transaction for Goods Receipt](https://learning.sap.com/courses/business-processes-in-sap-s-4hana-sourcing-procurement/using-the-advanced-transaction-for-goods-receipt) | Contexto de uso da MIGO e consulta da situação do estoque. | Material didático; não comprova configuração de um cliente real. |
| S04 | SAP Learning: [Tolerâncias e entrega concluída](https://learning.sap.com/courses/inventory-management-in-sap-cloud-erp/applying-tolerances-and-the-delivery-complete-indicator-1) | K06: limites e indicador. | Não assumir tolerância ou bloqueio universal. |
| S05 | SAP Learning: [Processamento do recebimento](https://learning.sap.com/courses/executing-basic-erp-processes-with-sap-s-4hana/processing-a-goods-receipt-for-a-purchase-order) | K08: documentos gerados. | Contexto do processo de armazém descrito. |
| S06 | SAP Learning: [Gestão de faturas](https://learning.sap.com/courses/sap-s-4hana-sourcing-procurement-innovations/working-with-invoice-management_b94460d9-dd35-48cc-9c58-8a13ca751cd4) | K09: relação entre recebimento e fatura. | Consulta conceitual; não executar MIRO ou liberar fatura. |
| S07 | SAP Learning: [Números de série](https://learning.sap.com/courses/managing-technical-objects-in-sap-s-4hana-asset-management/working-with-serial-numbers_d13369ff-6846-4d1b-874f-c7eb6f127679) | K10: identificação e perfil. | Não presumir perfil do material do cliente. |
| S08 | SAP Learning: [Verificações de datas](https://learning.sap.com/courses/inventory-management-in-sap-cloud-erp/using-date-checks-in-goods-receipt-processing-1) | K11: validade mínima e entrega. | Resultado depende de dados e configuração. |
| S09 | SAP Learning: [Estornos e devoluções](https://learning.sap.com/courses/inventory-management-and-physical-inventory-in-sap-s-4hana/posting-cancellations-return-deliveries-and-returns) | K12: diferença dos fluxos. | Consulta somente; executor do protótipo não ampliado. |

**Recomendação:** complementar com SAP Help Portal para a versão escolhida e documentação de tolerâncias apenas quando necessário ao recorte. SAP Notes e KBAs restritos são referências de descoberta; prévia pública não equivale ao texto completo. Conteúdo comunitário pode ajudar a localizar uma hipótese, mas não substituir uma fonte técnica validada.

Não há corpus de chamados reais fornecido. Os chamados e o estado do simulador serão próprios e fictícios. Uma base pública acessível não é automaticamente licenciada para redistribuição integral: produzir sínteses próprias, manter atribuição e verificar condições de uso antes de copiar documentos.

## Material a preparar

**Estado implementado após a ampliação solicitada:** 12 guias curtos em português: dez sínteses de fontes oficiais e duas políticas próprias. K01–K05 preservam o corpus inicial. K06–K12 acrescentam tolerâncias, estoques, documentos gerados, relação com fatura, séries, validade/datas e estorno/devolução. K07 também usa S02. Cada guia pequeno corresponde a um trecho recuperável, com parágrafos identificados para a verificação de cobertura.

Cada guia deve conter origem e seção de referência, título, idioma, produto/edição, release identificada ou explicitamente desconhecida, data de consulta, tipo de conteúdo, revisão e assuntos cobertos. Usar os tipos `sintese_de_fonte_oficial` e `politica_da_simulacao`; a política simulada não deve parecer um documento publicado pela SAP.

Preservar o vínculo entre guia, trecho e URL. Citar a síntese local com o documento oficial de origem, sem apresentar uma síntese como citação literal. Separar conhecimento procedimental das consultas de dados do simulador.

**Decisão confirmada:** instruções do repositório, prompts, credenciais, gabaritos e resultados esperados dos testes nunca entram no índice SAP. Um teste positivo não pode ser resolvido recuperando seu próprio resultado esperado.

## Ingestão e recuperação

**Decisão confirmada:** embeddings inicialmente `qwen/qwen3-embedding-8b` pelo OpenRouter, armazenados em PostgreSQL/pgvector; busca híbrida textual e vetorial.

**Atualização confirmada:** a versão 8B substituiu a escolha original 0.6B após o endpoint desta retornar HTTP 404; o usuário aprovou a troca. A integração real retornou dimensão 4.096. O código não troca modelos silenciosamente.

**Estado implementado:** normalização textual em português, contagem de termos, busca vetorial por cosseno no pgvector e fusão RRF com constante 60; até quatro sínteses oficiais por consulta, acrescidas das duas políticas da demonstração como contexto obrigatório. Essa seleção substitui o limite anterior de quatro guias misturados, que podia omitir regras do simulador. A busca usa a mensagem atual, o título e o relato do chamado; a verificação de cobertura prioriza a pergunta atual, com histórico para resolver referências.

**Decisão confirmada para anexo opcional:** sem chamado, a consulta usa somente a pergunta atual e a cobertura recebe apenas o histórico do canal geral. Não inserir título, relato, pedido, evidência `DATA` ou histórico de um chamado removido. Com anexo, o fluxo usa os dados daquele chamado e seu histórico correspondente. A linha do tempo apresentada ao usuário pode conter ambos os contextos, mas não é enviada integralmente ao modelo. A base de conhecimento e a regra de insuficiência são as mesmas nos dois modos.

O corpus pequeno usa varredura exata, sem índice ANN. Conteúdo/metadados recebem hash, e embeddings são reutilizados enquanto hash e modelo não mudarem. A dimensão é verificada antes da busca. Base vazia produz resposta explícita de insuficiência, sem chamada de geração ou proposta.

**Recomendação:** dividir guias por seção coerente, preservar cabeçalhos e termos SAP e gerar IDs estáveis. Deduplicar por hash do conteúdo e registrar modelo e revisão dos embeddings. Reindexar quando modelo, dimensão ou conteúdo mudar; não misturar espaços vetoriais incompatíveis.

Recuperar candidatos por termos/códigos e por significado, combinar as classificações e selecionar trechos úteis sem duplicação. Aplicar filtros de processo, produto e versão quando conhecidos. A versão desconhecida não deve receber uma precisão que não existe. Os valores de tamanho de trecho, quantidade recuperada e corte de relevância são **pendências de calibração**, a registrar após a primeira avaliação; não usar um limiar arbitrário como garantia de verdade.

Documentação de integração: [embeddings no OpenRouter](https://openrouter.ai/docs/api_reference/embeddings), [modelo atual](https://openrouter.ai/qwen/qwen3-embedding-8b) e [pgvector no Supabase](https://supabase.com/docs/guides/database/extensions/pgvector). Acesso autenticado e geração de vetores foram verificados; o histórico de resultados está nas [evidências](../evidencias/README.md).

## Evidências e confiança

**Requisito do PDF:** informar fontes e nível de confiança, evitando respostas sem fundamentação.

**Recomendação:** o modelo referencia somente IDs entregues no contexto. O servidor rejeita IDs inexistentes e monta links a partir do catálogo; o modelo não inventa URLs. Verificar separadamente a existência da fonte e se ela sustenta a afirmação, pois um ID válido pode ser citado fora de contexto.

Mostrar quais documentos foram recuperados e quais foram efetivamente citados. Dados transacionais devem aparecer como consulta ao simulador, com ID e versão, sem URL oficial fictícia. Não enviar a base inteira ao modelo.

**Estado implementado:** `DATA` identifica a consulta simulada; `RELATO` identifica o que foi informado pelo usuário, sem comprová-lo como fato SAP; K01 a K12 identificam conhecimento curado. O servidor verifica IDs e cobertura de referências e aplica abstinência para códigos customizados não documentados.

**Decisão confirmada e implementada, substituindo o popup:** referências numeradas e links de fontes levam diretamente ao site oficial. Agrupar documentos com a mesma URL e distinguir fontes citadas das apenas recuperadas. Não exibir o campo `content`, parágrafos ou popup. Conteúdo, versão e URL do atendimento permanecem salvos internamente; mudanças futuras da base não trocam a URL de uma resposta anterior.

Políticas próprias são identificadas como regras da simulação, sem link oficial inventado. URLs vêm dos metadados catalogados e são validadas como HTTPS em domínios SAP permitidos; URLs/imagens livres geradas pelo modelo são removidas. Não carregar documentos externos automaticamente na interface.

**Decisão confirmada e implementada:** antes da geração, uma chamada estruturada ao Qwen3.6 Plus avalia se os trechos cobrem a solicitação atual. O verificador seleciona IDs de documento/parágrafo; o servidor confere sua existência no texto recuperado. Não aceitar `DATA` ou `RELATO` como prova de conhecimento. A geração recebe somente os documentos aprovados e deve citar pelo menos um deles. Sem cobertura, com prova inválida ou código sem documentação, o servidor devolve “Não tenho informações suficientes na base de conhecimento...” com confiança baixa, sem hipóteses, fatos técnicos ou proposta.

Uma pergunta parcialmente coberta também deve receber abstinência. Instruções em documentos, termos em comum e similaridade não bastam. A suficiência semântica ainda é avaliada por LLM e deve continuar sendo medida; a validação de IDs não prova logicamente a sustentação de toda frase. Erros de rede mantêm o tratamento de falha explícita, nunca resposta técnica inventada.

| Confiança recomendada | Evidência necessária | Comportamento |
| --- | --- | --- |
| Alta | Fonte aplicável e fatos suficientes, sem conflito relevante. | Orientação fundamentada; escrita continua exigindo HITL. |
| Média | Evidência parcial ou contexto ainda incompleto. | Formular hipótese delimitada e pedir esclarecimento. |
| Baixa | Ausência, conflito relevante ou incompatibilidade de evidências. | Explicar a lacuna e pedir validação humana; não propor correção sem suporte. |

A confiança descreve suficiência das evidências, não probabilidade estatística nem autoconfiança numérica do LLM. A falta de suporte para uma correção específica não impede uma pergunta de esclarecimento segura.

## Fontes indisponíveis

**Decisão confirmada:** tentar novamente por meio adequado e procurar fontes oficiais equivalentes. Registrar falha, URL e informação faltante. Se não for possível obter a informação necessária, pedir ao usuário conteúdo, documento, base acessível ou dados mockados, conforme as [regras globais](../AGENTS.md).

Não contornar login, copiar de fontes não verificadas como se fossem oficiais ou completar lacunas por invenção. Se o usuário fornecer mocks, registrar quem os forneceu, seu escopo e que representam a simulação. Prosseguir com tarefas independentes enquanto a lacuna é resolvida.
