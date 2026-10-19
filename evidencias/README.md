# Evidências de validação

Resultados coletados em 18/10/2026. A aplicação não foi publicada externamente.

## Testes locais

As suítes em `tests/` exercitam contratos, gateway, recusa, vencimento, concorrência, rollback, isolamento, recuperação híbrida, falhas do provedor e componentes Streamlit via AppTest. O provedor controlado é exclusivo dos testes.

Resultado atual: **133 testes aprovados, zero falhas, erros ou testes ignorados** em [testes-selecao-chamados.xml](testes-selecao-chamados.xml). Ruff não encontrou erros, e `pip check` confirmou compatibilidade das dependências instaladas. Python 3.12.10; dependências diretas fixadas nos arquivos requirements. Os relatórios de [75 testes](testes.xml), [101 testes](testes-ampliados.xml) e [121 testes](testes-fontes-rag.xml) permanecem como histórico.

Os 12 novos testes cobrem perfis fictícios, campos ausentes, busca sem acentos e por documentos, apresentação sem escrita, compatibilidade de sessões antigas, seletor com prévia/cancelamento, lista/filtros/seleção de linha e preservação de histórico/aprovação. A seleção de linha no AppTest usa o estado nativo documentado do componente; não equivale a clicar numa tabela em navegador real.

## Seleção de chamados e formato de suporte

**Oito verificações aprovadas** com Supabase/OpenRouter reais em [verificacao-selecao-chamados.json](verificacao-selecao-chamados.json): busca/prévia/cancelamento, lista com seleção/filtro/detalhes, C07 com os novos perfis e proposta pendente, troca e retorno com a mesma aprovação/histórico, Sim com execução única, Não em C08, campos ausentes em C05 e abstinência em C06. Cliques e decisões foram simulados pelo AppTest; o provedor e a persistência são reais. Navegação não gerou chamadas ao modelo ou escrita de negócio; a aprovação foi a única etapa que registrou recebimento.

Foram quatro requisições de embeddings e cinco de chat nessa rodada. Os hashes do catálogo externo ao schema `sap_chamados_ai` permaneceram iguais; nenhum dado de tabela externa foi lido. Nenhuma migração SQL foi necessária. A [verificação do formato SAP for Me](../instrucoes/02-processo-sap.md) usa documentação oficial, sem afirmar integração SAP ou homologação do formato local.

A [primeira tentativa](verificacao-selecao-chamados-inicial.json) preserva uma falha do harness: exigia citação oficial em uma proposta sustentada pelas regras próprias do simulador. A proposta estava correta e pendente, sem execução. O teste passou a distinguir referências oficiais consultadas e efetivamente citadas, sem obrigar citação irrelevante. A resposta também orientava aguardar uma “frase exata”; o rascunho 2026-10-18.7 esclareceu que a pergunta pertence ao cartão e o consentimento ocorre pelos botões. O gateway já impedia autorização por texto. O reteste completo é o relatório de oito verificações acima.

Reprodução com consumo de créditos: `.\.venv\Scripts\python.exe scripts/verify_case_navigation_live.py`. O teste cria uma sessão fictícia própria; sessões existentes não recebem os novos perfis retroativamente. Inspeção visual e navegação completa por teclado continuam pendentes.

## Ampliação do RAG e fontes diretas

O usuário solicitou ampliar o corpus, retirar o conteúdo/popup da interface, organizar links e impedir respostas sem suporte. O corpus atual tem **12 guias**, com dez sínteses de nove fontes SAP Learning e duas políticas próprias. Os textos continuam internos ao RAG e à auditoria. Novos guias não ampliam as operações executáveis do simulador.

Resultado consolidado: **28 verificações aprovadas após ajustes e retestes**, em [verificacao-fontes-rag.json](verificacao-fontes-rag.json). Foram 44 requisições de chat e 34 de embeddings nas três rodadas consolidadas, incluindo repetições/falhas; esses números excluem a rodada inicial interrompida e uma chamada de diagnóstico, e não representam um custo calculado. As verificações incluem novos conteúdos, BAdI não documentada, SAP Note ausente, pergunta parcialmente coberta, fontes diretas, regressões dos chamados e HITL no PostgreSQL. [test_grounding.py](../tests/test_grounding.py) também cobre base vazia, prova inventada, dado transacional usado como conhecimento, mudança de assunto e verificador inválido.

O [corpus no Supabase](corpus-ampliado-supabase.json) foi conferido por consulta somente leitura: 12 documentos, todos com embeddings de 4.096 dimensões. O [resumo atual](resumo-fontes-rag.json) identifica versões e artefatos. Os hashes do catálogo externo ao schema do projeto permaneceram iguais nas rodadas; nenhum dado de tabela externa foi lido.

A primeira rodada foi interrompida após um falso bloqueio de proposta válida; o [relatório parcial](verificacao-fontes-rag-inicial.json) foi preservado. As regras do simulador passaram a acompanhar os quatro documentos oficiais selecionados. A verificação seleciona IDs de parágrafo, cujo texto é obtido pelo servidor, evitando depender de transcrição literal pelo LLM. A distinção entre assunto sem documentação e fora do escopo foi explicitada; dúvidas conceituais documentadas não são recusadas apenas porque o executor não realiza aquela operação.

O [relatório anterior aos ajustes](verificacao-fontes-rag-antes-ajustes.json) preserva três bloqueios indevidos: BAdI foi classificada fora do escopo, uma explicação de séries foi recusada na geração e a consulta de quantidade não trouxe os trechos necessários. O [reteste focado](verificacao-fontes-rag-reteste.json) aprovou BAdI, séries e UI, mas detectou um ID inválido no caso de quantidade. O [reteste C03](verificacao-fontes-rag-c03.json) aprovou a proposta-base e o diagnóstico de saldo/excedente após restringir os IDs no esquema. O consolidado seleciona o resultado mais recente de cada cenário; não representa uma execução única sem falhas anteriores.

As decisões de cobertura são semânticas e usam LLM. IDs válidos não constituem prova lógica de sustentação de toda frase; ampliar avaliação de falsos bloqueios e respostas indevidas continua necessário. Falhas de rede não são confundidas com ausência de documentação.

## Histórico: verificação ampliada anterior

**20 verificações aprovadas**, com **10 requisições de chat e 13 de embeddings** nesta execução. O usuário autorizou o uso da API. Relatório: [verificacao-ampliada.json](verificacao-ampliada.json); [resumo e versões](resumo-verificacao-ampliada.json); [cobertura do PDF e dos 24 cenários](verificacao-requisitos.md). A rodada anterior com os oito chamados continua registrada abaixo.

- API real: proposta sem execução; texto “sim” sem autorização; código desconhecido sem causa inventada; esclarecimento em duas rodadas; fora do escopo; documento malicioso tratado como dados. A injeção foi somente no contexto de teste, sem modificar o índice compartilhado.
- Recuperação real: três consultas sobre aplicativo, saldo e aprovação; o guia esperado apareceu na primeira posição em todas. Amostra pequena, sem estimativa estatística de qualidade.
- Supabase real: aprovação, recusa, expiração exata, parâmetros/envelope adulterados, dados alterados sem nova versão, saldo desatualizado, sessão/token inválidos, quatro aprovações concorrentes, disputa Sim/Não, reconexão e rollback após flush. Operação fora da lista foi bloqueada no contrato. Decisões simuladas pelo harness, sem solicitar cliques de uma pessoa.
- Interface com Supabase/OpenRouter reais via AppTest: popup com o trecho histórico exato, nenhuma chamada de API ou alteração de negócio ao abrir/fechar; Sim gera uma execução; Não preserva dados; rerun não repete execução nem chamada de IA.
- Catálogo de estruturas fora de `sap_chamados_ai`: hashes antes/depois iguais. Nenhuma leitura de dados de tabelas externas; a igualdade dos metadados observados não representa backup ou auditoria global.

Os testes motivaram o vínculo do envelope completo ao hash da proposta e o uso de fingerprints dos dados, além das versões. Pendências antigas sem envelope exigem nova análise. Nenhuma migração SQL foi necessária. O popup desse relatório corresponde à apresentação anterior, substituída por links diretos a pedido do usuário; os resultados históricos não foram apagados.

Reprodução atual: [scripts/verify_live.py](../scripts/verify_live.py), com serviços configurados e consumo de créditos. O script acompanha o comportamento atual. Permite `--only BAdI K10 C03 UI --report-name verificacao-fontes-rag-reteste.json`; a proposta-base sempre é verificada. Falhas de provedor e conexão são exercitadas com transporte controlado nos testes locais; não se provocou uma interrupção real dos serviços.

## Integração Supabase

- [Isolamento de estruturas](isolamento-supabase.json): comparação do catálogo externo ao schema do projeto antes/depois da inicialização. Nenhum dado de tabela externa foi lido. A igualdade do catálogo comprova preservação dos metadados observados; não é um backup de dados.
- [Gateway no Supabase](integracao-supabase.json): proposta controlada pendente, aprovação simulada pelo teste, bloqueio de repetição e de outra sessão. Não foi um clique de usuário real nem uma resposta de LLM.
- [Interface integrada](interface-integrada.json): AppTest carregou os oito chamados com Supabase e OpenRouter reais, gerou uma proposta para C08 e acionou o botão Não. O chat ficou pausado até a decisão, os botões desapareceram após a recusa e o estado de negócio permaneceu idêntico. Evento automatizado de teste, não decisão de uma pessoa real.

## Integração com IA

O modelo de embeddings 0.6B retornou HTTP 404, sem endpoint disponível. O usuário autorizou a substituição por `qwen/qwen3-embedding-8b`. O chat permanece `qwen/qwen3.6-plus`.

Resultado da primeira rodada: **oito chamados e duas exceções adicionais concluídos com Supabase e OpenRouter reais**. Nenhuma análise alterou o estado de negócio. As propostas de recebimento ficaram pendentes, com quantidade, pedido, item, data e efeito concreto. Os casos adicionais verificam fora do escopo e tentativa de burlar as regras pelo texto do chat.

- [Avaliação integrada](avaliacao-integrada.json): respostas estruturadas, referências, propostas pendentes, uso reportado e latência por caso.
- [Resumo da validação](resumo-validacao.json): verificações por caso, testes automatizados e medidas desta rodada. A mediana observada foi 20,22 segundos, em amostra pequena e fictícia; não é SLA ou benchmark estatístico.
- [Script de avaliação](../scripts/evaluate_live.py): reprodução explícita, com consumo de créditos. Permite `--only E01 --update-report` para repetir somente um caso alterado.

As primeiras rodadas detectaram incompatibilidades reais: ausência de endpoint para embeddings 0.6B; necessidade de explicitar JSON/contrato no prompt; proposta de escalonamento com dados diagnósticos faltantes; referências incompletas; e fatos irrelevantes em resposta fora do escopo. O servidor bloqueou respostas/propostas inválidas. Foram corrigidos contrato, reparo limitado com erros específicos, tratamento de códigos desconhecidos e mensagem determinística de escopo.

O histórico foi preservado em [avaliação inicial](avaliacao-inicial.json) e [rodada anterior ao ajuste de escopo](avaliacao-antes-ajuste-escopo.json). Esses arquivos contêm falhas anteriores e não representam o resultado final. Resposta fora do escopo é uma política de produto aplicada no servidor após classificação do modelo, sem diagnóstico ou ação; não é um fallback de IA mockada.

Os testes AppTest não são screenshots ou inspeção visual em um navegador. A revisão estética final precisa ser feita na interface em execução.
