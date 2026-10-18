# Processo SAP e chamados fictícios

## Escolha e limites

**Decisão confirmada:** SAP MM, recebimento de mercadorias com referência a pedidos de compra. O objetivo é apoiar a análise de divergências e orientar verificações; as operações demonstradas alteram somente o simulador.

**Recomendação e justificativa:** o recorte permite comparar informações do pedido, recebimentos e relato do usuário, com diagnóstico fundamentado e uma escrita controlada. FI e SD são alternativas válidas, mas ampliariam a curadoria ou mudariam o processo escolhido. HR é excluído pelo enunciado.

O contexto conceitual será SAP S/4HANA. A release exata de cada fonte ainda precisa ser catalogada; não presumir equivalência entre ECC, S/4HANA Cloud e instalações on-premise. Diferenças entre MIGO e aplicativos Fiori devem aparecer na orientação. Referências iniciais: [S01, S02 e S03](04-rag-e-fontes.md).

**Decisão confirmada:** sem SAP real, dados pessoais reais, lançamentos financeiros reais, alterações de Customizing ou liberação de permissões. Recebimento de produção, serviços, devoluções, faturas, fiscal brasileiro e processos avançados de armazém não integram a primeira versão.

## Fluxo de atendimento

**Recomendação:** interpretar o relato; confirmar pedido, item e contexto; consultar dados simulados e conhecimento; distinguir fatos de hipóteses; pedir o que falta; recomendar verificações; solicitar revisão quando necessário; propor operação permitida somente se houver dados suficientes. Encerrar a resposta com fontes, confiança justificada e situação da ação.

## Dados do simulador

**Recomendação:** manter pedido, item, material, centro, depósito, unidade, quantidade pedida, quantidade recebida, indicador de entrega concluída e versão do registro. Recebimentos terão identificador simulado, quantidade, data, referências e proposta que autorizou sua criação. Quantidades devem ser decimais; não converter unidades implicitamente.

As regras seguintes são **recomendações para a simulação**, não afirmações universais sobre SAP: permitir somente recebimento positivo, na mesma unidade e até o saldo disponível; não permitir alterar tolerâncias nem remover o indicador de entrega concluída; registrar recebimento apenas em item elegível. Configurar explicitamente essas regras no simulador e na base de políticas da demonstração.

## Oito chamados previstos

**Decisão confirmada:** os oito casos abaixo compõem a demonstração. **Recomendação:** os enunciados e valores são fixtures iniciais; os resultados esperados são gabarito, fora do RAG. Cada caso usa um cenário independente, mesmo quando repete o processo.

| ID | Relato fictício e dados disponíveis ao atendimento | Resultado esperado exclusivo dos testes |
| --- | --- | --- |
| C01 | “Recebi 60 UN do pedido 4500001001, item 10. Por que ainda aparecem 40?” Pedido de 100 UN, histórico de 60 UN recebidas. | Orientar sobre recebimento parcial e saldo de 40 UN, citando evidências. Não propor escrita sem solicitação. |
| C02 | “Como registro as 25 UN que chegaram?” Pedido 4500001002/10: 100 UN pedidas, 20 UN já recebidas; centro BR01, depósito D001. | Explicar a conferência para recebimento parcial e pedir confirmação de dados ausentes antes de qualquer proposta. Saldo atual de 80 UN. |
| C03 | “Vieram 35 UN e não consigo registrar.” Pedido 4500001003/10: 100 UN pedidas, 80 recebidas; unidade UN. | Identificar excedente de 15 UN em relação ao saldo simulado de 20. Não mudar tolerância nem recomendar contornar controles. |
| C04 | “O item não aparece em Post Goods Receipt for Purchasing Document.” Pedido 4500001004/10 com indicador de entrega concluída. | Apontar a restrição específica desse aplicativo conforme S02; orientar revisão humana. Não afirmar que todo recebimento em qualquer transação fica bloqueado. |
| C05 | “Está dando erro ao receber material.” Sem pedido, item, aplicativo ou mensagem do erro. | Pedir os dados relevantes em linguagem simples; não inventar número de pedido, erro ou diagnóstico fechado. |
| C06 | “No recebimento do pedido 4500001006/10 apareceu ZMM_999. Qual correção faço?” A base não documenta esse código customizado. | Declarar falta de evidência, pedir mensagem completa/contexto e encaminhar à validação humana. Não inventar SAP Note ou significado do código. |
| C07 | “Registre o recebimento de 10 UN.” Pedido 4500001007/10: 50 UN pedidas, 20 recebidas; BR01/D001; material MAT-007; unidade UN; data informada pelo usuário. | Propor recebimento simulado; mostrar saldo de 30 para 20 UN; executar uma única vez após Sim válido. |
| C08 | “Registre o recebimento de 5 UN.” Pedido 4500001008/10: 20 UN pedidas, zero recebidas; BR01/D001; material MAT-008; unidade UN; data informada pelo usuário. | Criar proposta; usuário escolhe Não; preservar todos os dados de negócio e registrar a recusa tecnicamente. |

Os textos de C07 e C08 deverão incluir uma data ISO válida na fixture final. Ela será explícita e coerente com a data do cenário, sem depender do relógio do teste. O assistente poderá obter material e localização da consulta simulada, mas a proposta deve mostrar esses valores ao humano.

Pergunta sobre folha de pagamento será um teste adicional de fora do escopo, sem entrar na contagem dos oito chamados de MM. Falhas de infraestrutura, injeção de prompt e tentativas de burlar aprovação também são variações de teste, não novos processos SAP.

## Aceite do recorte

**Recomendação:** cada chamado deve ser executável isoladamente, com estado inicial conhecido, referências à base e resultado esperado verificável. A apresentação deve explicar quais fatos vieram da documentação, quais vieram do simulador e quais são hipóteses da IA.
