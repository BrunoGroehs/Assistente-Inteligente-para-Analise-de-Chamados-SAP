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

As fixtures implementadas em `sap_assistant/fixtures.py` incluem `2026-10-18` nos relatos C07 e C08, sem depender do relógio do teste. O assistente pode obter material e localização da consulta simulada, mas a proposta mostra esses valores ao humano. Os resultados esperados desta tabela não integram o índice de conhecimento.

Pergunta sobre folha de pagamento será um teste adicional de fora do escopo, sem entrar na contagem dos oito chamados de MM. Falhas de infraestrutura, injeção de prompt e tentativas de burlar aprovação também são variações de teste, não novos processos SAP.

## Aceite do recorte

**Recomendação:** cada chamado deve ser executável isoladamente, com estado inicial conhecido, referências à base e resultado esperado verificável. As respostas devem distinguir fatos da documentação, dados do simulador e hipóteses da IA.

## Aproximação ao formato SAP for Me

**Decisão confirmada:** aproximar os chamados fictícios do atendimento SAP. **Implementação:** o perfil `support` de cada nova sessão guarda resumo/descrição, identificação do sistema, produto, prioridade, impacto, resultados esperado e relatado, mensagem de erro, passos de reprodução, ações tentadas e referências de anexos. A lista e o seletor mostram esse contexto antes de iniciar a análise.

**Verificação em fontes oficiais em 18/10/2026:** o SAP for Me usa **case** para atendimento de suporte. “Chamado” permanece como termo da interface em português e `ticket` como nome interno compatível com a persistência existente. O objeto do aplicativo representa também dúvidas e solicitações internas de operação; não significa que toda solicitação seja elegível para envio ao suporte SAP.

| Referência oficial | Aplicação no protótipo |
| --- | --- |
| [Get Support — criação de case](https://support.sap.com/content/s4m/help/support/cases/create.html) | Descrição curta, contexto do sistema/produto, reprodução, componente e impacto. Seleção do componente é uma sugestão a validar, não roteamento real. |
| [Guia de criação pela API SAP Cloud ALM](https://help.sap.com/docs/cloud-alm/apis/implementation-guidance-for-case-creation?locale=en-US&state=PRODUCTION&version=latest) | Prioridades 1 Muito alta, 2 Alta, 3 Média, 4 Baixa, vinculadas ao impacto. Inspirar os campos não torna o JSON local um payload homologado dessa API. |
| [Metadados públicos da KBA 2913656](https://userapps.support.sap.com/sap/support/knowledge/en/2913656) | Verificação do componente `MM-IM-GR-PO` para recebimento de compras externas. Não houve acesso à solução restrita dessa KBA. |
| [Notificações de cases](https://support.sap.com/content/s4m/help/support/cases/notifications.html) | O fluxo oficial tem estados próprios, como Customer Action. Não mapear automaticamente nossos estados a estados SAP. |

**Limites implementados:** identificação local `SIM-C01` a `SIM-C08`; número do case SAP vazio; sistema fictício QAS/mandante 100; empresa e solicitante de demonstração; produto SAP S/4HANA sem edição/release informada. `MM-IM-GR-PO` aparece como **componente sugerido**, pois a variante exata depende do produto e da edição. “Aberto”, “Em validação humana” e “Resolvido” são situações locais do atendimento. Autorizar o simulador não concede permissão de reprodução ou acesso a sistemas pelo suporte SAP.

Os perfis são entradas fictícias explícitas, sem diagnósticos esperados ou soluções de gabarito. C05 mantém prioridade, impacto, aplicativo, mensagem e reprodução ausentes. Não inventar valores para preencher um formulário. A data da ocorrência é informada na fixture, sem simular uma abertura real no SAP for Me. Não há criação/edição de cases SAP, S-user, instalação, contatos reais ou upload de anexos nesta versão.

Os novos perfis são criados somente em **novas sessões**. Sessões antigas continuam legíveis e exibem ausências; não são alteradas retroativamente. Metadados informados são `RELATO`, separados dos dados atuais consultados e do conhecimento SAP. O resultado relatado na abertura não prova que uma operação foi executada nem substitui evidência no RAG. Estas referências de formato ficam na documentação de desenvolvimento, fora do corpus de recebimento.
