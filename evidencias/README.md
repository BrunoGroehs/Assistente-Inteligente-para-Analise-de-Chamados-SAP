# Evidências de validação

Resultados coletados em 18/10/2026. A aplicação não foi publicada externamente.

## Testes locais

As suítes em `tests/` exercitam contratos, gateway, recusa, vencimento, concorrência, rollback, isolamento, recuperação híbrida, falhas do provedor e componentes Streamlit via AppTest. O provedor controlado é exclusivo dos testes.

Resultado: **75 testes aprovados, zero falhas, erros ou testes ignorados**. Relatório gerado pelo pytest: [testes.xml](testes.xml). Ruff não encontrou erros, e `pip check` confirmou compatibilidade das dependências instaladas. Python 3.12.10; dependências diretas fixadas nos arquivos requirements.

## Integração Supabase

- [Isolamento de estruturas](isolamento-supabase.json): comparação do catálogo externo ao schema do projeto antes/depois da inicialização. Nenhum dado de tabela externa foi lido. A igualdade do catálogo comprova preservação dos metadados observados; não é um backup de dados.
- [Gateway no Supabase](integracao-supabase.json): proposta controlada pendente, aprovação simulada pelo teste, bloqueio de repetição e de outra sessão. Não foi um clique de usuário real nem uma resposta de LLM.
- [Interface integrada](interface-integrada.json): AppTest carregou os oito chamados com Supabase e OpenRouter reais, gerou uma proposta para C08 e acionou o botão Não. O chat ficou pausado até a decisão, os botões desapareceram após a recusa e o estado de negócio permaneceu idêntico. Evento automatizado de teste, não decisão de uma pessoa real.

## Integração com IA

O modelo de embeddings 0.6B retornou HTTP 404, sem endpoint disponível. O usuário autorizou a substituição por `qwen/qwen3-embedding-8b`. O chat permanece `qwen/qwen3.6-plus`.

Resultado final: **oito chamados e duas exceções adicionais concluídos com Supabase e OpenRouter reais**. Nenhuma análise alterou o estado de negócio. As propostas de recebimento ficaram pendentes, com quantidade, pedido, item, data e efeito concreto. Os casos adicionais verificam fora do escopo e tentativa de burlar as regras pelo texto do chat.

- [Avaliação integrada](avaliacao-integrada.json): respostas estruturadas, referências, propostas pendentes, uso reportado e latência por caso.
- [Resumo da validação](resumo-validacao.json): verificações por caso, testes automatizados e medidas desta rodada. A mediana observada foi 20,22 segundos, em amostra pequena e fictícia; não é SLA ou benchmark estatístico.
- [Script de avaliação](../scripts/evaluate_live.py): reprodução explícita, com consumo de créditos. Permite `--only E01 --update-report` para repetir somente um caso alterado.

As primeiras rodadas detectaram incompatibilidades reais: ausência de endpoint para embeddings 0.6B; necessidade de explicitar JSON/contrato no prompt; proposta de escalonamento com dados diagnósticos faltantes; referências incompletas; e fatos irrelevantes em resposta fora do escopo. O servidor bloqueou respostas/propostas inválidas. Foram corrigidos contrato, reparo limitado com erros específicos, tratamento de códigos desconhecidos e mensagem determinística de escopo.

O histórico foi preservado em [avaliação inicial](avaliacao-inicial.json) e [rodada anterior ao ajuste de escopo](avaliacao-antes-ajuste-escopo.json). Esses arquivos contêm falhas anteriores e não representam o resultado final. Resposta fora do escopo é uma política de produto aplicada no servidor após classificação do modelo, sem diagnóstico ou ação; não é um fallback de IA mockada.

Os testes AppTest não são screenshots ou inspeção visual em um navegador. A revisão estética final precisa ser feita na interface em execução.
