# Evidências de validação

## Migração atual: React + FastAPI

**Executado em 18/10/2026 (horário de São Paulo).** Streamlit removido do código, das dependências e do ambiente virtual deste projeto. Nenhum deploy realizado; nenhum servidor local de teste ficou em execução.

| Verificação | Resultado |
| --- | --- |
| Python: domínio, RAG, HITL e API HTTP | **152 aprovados**, zero falhas/ignorados; [XML](testes-api-react.xml). Os antigos testes Streamlit foram substituídos por testes HTTP; contagens históricas não são cumulativas. |
| React: diálogo, filtros, anexo, Novo chat, fontes e aprovações | **12 aprovados**; [relatório](testes-react.json), testes em [App](../frontend/src/App.test.tsx) e [cliente HTTP](../frontend/src/api.test.ts). |
| TypeScript e build Vite | `npm.cmd run build` aprovado; bundle JS 363,59 kB / 112,54 kB gzip e CSS 10,05 kB / 3,10 kB gzip nesta rodada. |
| Análise estática e dependências | Ruff aprovado em aplicação, testes e scripts; `pip check` sem conflitos; `npm audit` sem vulnerabilidades reportadas nesta execução. |
| Supabase + OpenRouter reais via HTTP | **Cinco verificações aprovadas** em [verificacao-web-api.json](verificacao-web-api.json). Quatro chamadas de embeddings, seis de chat. |
| Medição de API com Supabase real | [desempenho-api-web.json](desempenho-api-web.json); não mede cliques ou renderização do navegador. |

A rodada integrada verificou pergunta geral com URL SAP oficial sem conteúdo bruto, pergunta sem suporte com abstinência e sem proposta, proposta real de recebimento sem escrita prévia, bloqueio da conversa errada, Sim idempotente, Não preservando negócio mesmo após tentativa de Sim e Novo chat preservando histórico/dados. Os dois consentimentos foram simulados pelo harness em seu workspace fictício, não feitos por uma pessoa. O hash do catálogo de objetos externos ficou idêntico; isso verifica estruturas externas, não é uma comparação de conteúdo de todas as tabelas de outros projetos. Nenhum comando do aplicativo escreve nesses schemas.

Os testes HTTP também cobrem cookie/sessão, origem indevida, parâmetros inválidos, outra sessão, replay, isolamento de conversa, proposta vencida, dados alterados após apresentação, build estático e erro seguro. Um provedor bloqueado por evento comprova que a API continua respondendo e rejeita uma segunda análise da mesma sessão. Os testes React comprovam navegação sem novas chamadas, fontes recolhidas e ausência de botões de consentimento antes de reanexar ou após vencimento. Resposta de uma análise antiga não invade o Novo chat.

Nesta amostra, inicializar os recursos levou 9,609 s; carregar/atualizar o snapshot autenticado, 2,131/2,312 s com quatro SELECTs; Novo chat no servidor, 0,783 s. Essas operações são explícitas: buscar, consultar detalhes e anexar/remover não enviam requisições. O atendimento geral mediu 23,347 s no serviço, incluindo RAG, cobertura e geração, sem contar todo o fluxo HTTP do teste. React elimina reruns da apresentação; não elimina a espera do Supabase ou OpenRouter. Amostra única, sem promessa de SLA.

Não houve revisão estética em navegador real, teste de hospedagem, comparação estatística ou integração SAP real. Layout responsivo e foco foram implementados, mas a revisão visual/teclado continua pendente. Scripts antigos de verificação de interface agora encaminham para o harness HTTP atual; não reproduzem mais o Streamlit. Seus relatórios antigos permanecem abaixo como histórico.

Na revisão documental, 202 links locais foram conferidos: 201 destinos existem; a referência ao PDF original está pendente porque o arquivo já estava removido no diretório de trabalho. A remoção não integra os commits desta migração. Blocos Markdown e `git diff --check` passaram.

## Histórico das versões anteriores com Streamlit

As seções seguintes e seus resultados são históricos. Comandos e scripts citados nelas devem ser consultados na versão Git correspondente; para a versão atual use `scripts/verify_web_live.py`, `scripts/benchmark_ui.py` e os comandos do README principal.


Resultados coletados em 18/10/2026. A aplicação não foi publicada externamente.

## Testes locais

As suítes em `tests/` exercitam contratos, gateway, recusa, vencimento, concorrência, rollback, isolamento, recuperação híbrida, falhas do provedor e componentes Streamlit via AppTest. O provedor controlado é exclusivo dos testes.

Resultado da versão anterior: **158 testes aprovados, zero falhas, erros ou testes ignorados** em [testes-novo-chat.xml](testes-novo-chat.xml). Ruff não encontrou erros, e `pip check` confirmou compatibilidade das dependências instaladas. Python 3.12.10; dependências diretas fixadas nos arquivos requirements. Os relatórios de [75 testes](testes.xml), [101 testes](testes-ampliados.xml), [121 testes](testes-fontes-rag.xml), [133 testes](testes-selecao-chamados.xml), [140 testes](testes-anexos-chat.xml) e [147 testes](testes-desempenho.xml) permanecem como histórico.

Os testes de interface foram adaptados ao chat único com anexo opcional; sete cenários adicionais do serviço cobrem RAG geral sem `DATA`, separação de histórico, propostas forjadas de recebimento/status sem anexo, idempotência/vínculo da submissão, isolamento e base vazia. A seleção de linha no AppTest usa o estado nativo documentado do componente; não equivale a clicar numa tabela em navegador real.

## Novo chat e respostas compactas

**Quatro verificações aprovadas** com Supabase/OpenRouter reais em [verificacao-novo-chat.json](verificacao-novo-chat.json): resposta curta com fontes, Novo chat sem anexo/histórico anterior e sem mudar negócio, nova resposta com histórico filtrado no PostgreSQL e bloqueio de decisão da proposta de outra conversa. Uma proposta controlada na conversa nova executou uma única vez após o clique do harness; a proposta anterior permaneceu pendente, sem transferência ou renovação.

Foram duas chamadas de embeddings e quatro de chat com o rascunho 2026-10-18.9. A primeira resposta ficou abaixo de 100 palavras no resumo e com no máximo um próximo passo; a orientação do prompt prefere até 80 palavras sem corte automático. A UI manteve um único Fontes e detalhes fechado por resposta, com fontes oficiais acessíveis. As decisões foram simuladas pelo AppTest e as propostas de aprovação foram entradas controladas; não são consentimento humano nem proposta gerada pelo modelo nessa rodada.

Os 11 novos testes cobrem histórico/submissão isolados por conversa, IDs inválidos, proposta não reutilizada, decisão na conversa correta, manutenção dos dados de negócio, Novo chat com pendência anterior, fontes numeradas e apresentação compacta sem esconder pedidos de contexto/revisão. Não houve migração SQL: mensagens e propostas usam seus campos JSON existentes, com leitura compatível de registros antigos sem `chat_id`. [Script de reprodução](../scripts/verify_new_chat_live.py), com consumo de créditos. AppTest não equivale a inspeção visual ou teclado em navegador.

## Desempenho da navegação

A reclamação de lag motivou medição com Supabase real. O [antes](desempenho-interface-antes.json) registrou cinco SELECTs por rerun de apresentação; o [depois](desempenho-interface-depois.json) registra zero nessas interações após o primeiro carregamento. Mesma máquina e sequência de AppTest, com uma sessão fictícia nova em cada rodada. Os tempos abaixo são observações isoladas, sem benchmark estatístico, navegador real ou garantia de SLA.

| Interação | Antes | Depois |
| --- | --- | --- |
| Abrir chamados | 3,122 s | 0,392 s |
| Anexar | 2,714 s | 0,029 s |
| Remover anexo | 2,717 s | 0,031 s |
| Rerun sem mudanças | 2,720 s | 0,024 s |
| Primeiro carregamento da sessão, com recursos já preparados | 4,007 s | 2,764 s |

Atualizar explicitamente fez três SELECTs e levou 1,195 s. A preparação fria dos recursos, medida separadamente, levou 9,917 s antes e 8,153 s depois; variabilidade de rede impede atribuir toda diferença à leitura em lote do catálogo. O preparo frio e a primeira leitura continuam tendo custo, e não estão incluídos nos tempos dos cliques já carregados.

A pergunta geral com OpenRouter real levou 25,040 s no AppTest. O serviço registrou 21,435 s após a pré-validação, com busca concluída aos 7,613 s, cobertura aos 12,808 s e resposta validada aos 20,852 s. Houve uma chamada de embeddings e duas de chat; são intervalos de etapas, não medições isoladas de cada requisição HTTP. A melhoria da navegação não elimina a espera por RAG, cobertura e geração. O status agora informa as etapas efetivamente executadas sem exibir conteúdo ainda não validado.

Sete testes adicionais cobrem navegação sem SQL, atualização explícita, isolamento/troca de sessão, snapshot sem mutação de negócio, vencimento visual, aprovação que revalida dados alterados após a exibição e progresso de análise. Reproduzir o benchmark atual: `.\.venv\Scripts\python.exe scripts/benchmark_ui.py`; acrescentar `--with-analysis` consome OpenRouter. A medição anterior foi feita antes da correção, sem consumir LLM; o script atual não reintroduz a implementação lenta para repetir esse baseline.

As [três verificações de aprovação com cache](aprovacoes-com-cache-supabase.json) também passaram no Supabase real: Sim executou uma vez, Não preservou dados e uma alteração de saldo após exibir o cartão invalidou o consentimento. Em todos os cenários a UI recarregou o estado confirmado e rerun não repetiu execução. Propostas controladas e cliques simulados pelo AppTest, sem consumir LLM. Reprodução: `.\.venv\Scripts\python.exe scripts/verify_snapshot_approvals_live.py`.

## Chat único com anexo opcional — estado atual

**Seis verificações aprovadas** com Supabase/OpenRouter reais em [verificacao-anexos-chat.json](verificacao-anexos-chat.json): pergunta geral fundamentada sem chamado/painel; lista, detalhes, cancelamento e anexo sem análise automática; proposta C07 ligada ao anexo; remoção/substituição do anexo com nova pergunta geral sem dados do chamado anterior; reanexar para decidir a proposta original e executar uma vez; código não documentado sem diagnóstico. A linha do tempo única preservou as perguntas gerais e as mensagens do caso com seus vínculos originais.

Foram quatro requisições de embeddings e seis de chat, com o rascunho 2026-10-18.8. Os hashes do catálogo externo ao schema do projeto permaneceram iguais; não foram lidos dados de tabelas externas nem feita migração SQL. O teste automatizou os cliques e o Sim; não foi consentimento de uma pessoa ou revisão visual. Não e demais invariantes de HITL permanecem nos testes locais e nos relatórios reais anteriores.

Reproduzir: `.\.venv\Scripts\python.exe scripts/verify_chat_attachments_live.py`, com consumo de créditos e criação de uma sessão fictícia própria. A tentativa de inspeção visual não encontrou navegadores disponíveis na ferramenta desta sessão; revisão visual/teclado continua pendente. [Interface atual](../instrucoes/06-interface.md).

## Histórico: seleção anterior e formato de suporte

**Oito verificações aprovadas** com Supabase/OpenRouter reais em [verificacao-selecao-chamados.json](verificacao-selecao-chamados.json): busca/prévia/cancelamento, lista com seleção/filtro/detalhes, C07 com os novos perfis e proposta pendente, troca e retorno com a mesma aprovação/histórico, Sim com execução única, Não em C08, campos ausentes em C05 e abstinência em C06. Cliques e decisões foram simulados pelo AppTest; o provedor e a persistência são reais. Navegação não gerou chamadas ao modelo ou escrita de negócio; a aprovação foi a única etapa que registrou recebimento.

Foram quatro requisições de embeddings e cinco de chat nessa rodada. Os hashes do catálogo externo ao schema `sap_chamados_ai` permaneceram iguais; nenhum dado de tabela externa foi lido. Nenhuma migração SQL foi necessária. A [verificação do formato SAP for Me](../instrucoes/02-processo-sap.md) usa documentação oficial, sem afirmar integração SAP ou homologação do formato local.

A [primeira tentativa](verificacao-selecao-chamados-inicial.json) preserva uma falha do harness: exigia citação oficial em uma proposta sustentada pelas regras próprias do simulador. A proposta estava correta e pendente, sem execução. O teste passou a distinguir referências oficiais consultadas e efetivamente citadas, sem obrigar citação irrelevante. A resposta também orientava aguardar uma “frase exata”; o rascunho 2026-10-18.7 esclareceu que a pergunta pertence ao cartão e o consentimento ocorre pelos botões. O gateway já impedia autorização por texto. O reteste completo é o relatório de oito verificações acima.

Essa rodada descreve a seleção que abria a conversa do caso e mantinha a lateral, posteriormente substituída pelo anexo opcional. O script `verify_case_navigation_live.py` redireciona agora à verificação atual de anexos, sem sobrescrever o relatório histórico. Sessões existentes não recebem os novos perfis retroativamente. Inspeção visual e navegação completa por teclado continuam pendentes.

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
