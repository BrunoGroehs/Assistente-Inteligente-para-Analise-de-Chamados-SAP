# Interface e direção visual

## Direção confirmada

**Decisão confirmada:** interface organizada, clean e inspirada em iOS, sem excesso de elementos decorativos. A interface usa React/TypeScript com Vite, API Python/FastAPI e componentes HTML sem dependência de Streamlit. Inspiração visual não significa replicar integralmente um aplicativo Apple.

**Recomendação:** fundo neutro claro, superfícies discretas, tipografia consistente, espaçamento confortável, bordas suaves e uma cor de destaque contida. Usar vermelho para erro/recusa e outros estados por necessidade semântica. Não depender apenas da cor para comunicar estado.

Evitar gradientes chamativos, banners grandes, emojis em excesso, sombras fortes, menus duplicados, cartões para todo parágrafo e painéis de métricas sem função no atendimento. Preferir CSS pequeno e estável; não depender de seletores internos frágeis para a experiência principal. Manter componentes pequenos e estado local para navegação; nenhuma consulta por clique de seleção.

## Organização e anexo opcional

**Decisão confirmada, substituindo a navegação lateral e a tela separada de lista:** uma única conversa central, sem painel lateral e sem chamado selecionado automaticamente. O chat inicia livre para perguntas gerais sobre recebimento em SAP MM, com a mesma exigência de evidência no RAG. Não ampliar o escopo para assuntos sem documentação.

O compositor contém o botão **Chamados**, com ícone de identificação. Ele abre um diálogo com todos os chamados, busca por referência/resumo/pedido/material/sistema/componente e filtro de prioridade. A lista mostra referência, resumo, prioridade e situação local; detalhes incluem sistema e componente sugerido. Clicar numa linha escolhe o candidato com botão acessível por teclado. Filtrar troca o conjunto de linhas e não reutiliza um índice de outro conjunto.

**Ver detalhes** abre/recolhe o contexto completo no próprio diálogo: descrição, produto/release, sistema/mandante/ambiente, aplicativo, prioridade/impacto, solicitante/empresa/data, resultado esperado e relatado, erro, reprodução, ações tentadas, pedido/item/quantidades atuais e anexos. Valores ausentes ficam explícitos. **Anexar ao chat** é uma ação separada da consulta. **Cancelar** ou fechar mantém o anexo atual. Não navegar para uma tela de outro chamado.

Depois de anexar, mostrar um cartão compacto junto ao campo de mensagem, com referência/título, acesso aos detalhes e **Remover anexo** com ícone de fechar, como um arquivo anexado à conversa. Um único chamado pode estar anexado por vez; anexar outro substitui o contexto das próximas perguntas. Remover o anexo devolve o compositor ao modo geral. Consultar, anexar e remover não chamam a IA nem alteram negócio.

**Analisar chamado** fica disponível quando há um chamado anexado ainda sem atendimento. Perguntas digitadas com anexo usam esse contexto; sem anexo usam apenas o canal geral e o RAG. A análise começa somente por mensagem ou por esse botão. Não é necessário anexar um chamado para fazer perguntas conceituais documentadas.

A linha do tempo não desaparece ao remover/substituir o anexo. Cada pergunta mostra qual chamado foi anexado naquele momento, ou “Sem chamado anexado”; esse vínculo histórico não muda. O servidor envia ao modelo somente o histórico correspondente ao contexto atual, evitando herdar dados do caso removido. Fontes e etapas ficam junto à resposta que as gerou, sem duplicar o contexto completo no cabeçalho.

**Decisão confirmada — Novo chat:** botão discreto no cabeçalho inicia uma conversa vazia, sem anexo ou rascunho anterior. Preserva os chamados, recebimentos, histórico e propostas já registrados; não é reset do simulador. A conversa nova recebe contexto independente e não reutiliza perguntas, respostas ou propostas de uma conversa anterior, mesmo ao anexar o mesmo chamado. Trocar de chat não aprova, recusa, renova ou transfere pedidos pendentes. O limite de análises continua pertencendo à sessão. Um seletor de conversas anteriores não integra este pedido; seus registros permanecem no banco.

Uma proposta pendente continua junto à resposta original. Com outro anexo ou sem anexo, o cartão oferece reanexar o chamado para revisão, sem botões de consentimento ativos. Reanexar o chamado correto restaura **Sim/Não** e o chat desse contexto permanece pausado até decidir. É possível remover o anexo e perguntar no canal geral. Remoção e troca nunca concedem, cancelam ou transferem aprovação. A validade original continua correndo.

Em telas estreitas, preservar leitura, detalhes e botões, sem depender de uma barra lateral ou de rolagem horizontal para informações essenciais. Usar componentes nativos; a lista é uma visão resumida, com detalhes em texto acessível. Ver [formato inspirado no SAP for Me](02-processo-sap.md) e [aprovações](07-aprovacoes-humanas.md).

**Recomendação técnica implementada para reduzir lag:** manter a projeção pública no estado React da conversa; cliques simples não recarregam o Supabase. **Atualizar**, com ícone discreto junto ao compositor, recarrega a conversa explicitamente. A cópia também é renovada após análise/decisão. Mudanças externas precisam desse botão; cartões antigos nunca dispensam a validação atual do gateway. Durante análise, o status distingue consulta de contexto, busca no RAG, verificação de suporte, preparação da resposta e salvamento. Não apresentar raciocínio interno nem resposta parcial ainda não validada.

## Fontes e etapas observáveis

**Decisão confirmada e implementada, substituindo o popup:** os números nos fatos e os links em **Fontes citadas** abrem diretamente o site oficial. Agrupar a mesma URL em um único item com os números correspondentes. Exibir título e origem de modo compacto; não mostrar o conteúdo dos documentos, parágrafos ou diálogo de fonte. Metadados e textos continuam no histórico interno.

**Decisão confirmada — respostas com menos opções:** apresentar a conclusão em um parágrafo curto, com referências numéricas diretas, uma pergunta focada se faltar contexto ou no máximo um próximo passo em destaque. Evitar menus de alternativas e repetir a mesma conclusão em vários blocos. Alertas relevantes e revisão humana continuam visíveis, assim como o cartão com efeito completo da operação.

Um único expansível **Fontes e detalhes**, fechado por padrão, reúne fatos, hipóteses justificadas, informações faltantes/verificações completas, confiança, fontes, consultas simuladas e etapas reais. **Fontes citadas**, **Referências consultadas**, **Dados consultados** e **Etapas do atendimento** mantêm seções identificadas dentro desse bloco, sem vários expansíveis por resposta. Referências apenas recuperadas são identificadas como não usadas na resposta. Políticas internas não recebem URL SAP inventada. Links externos não geram análise nem decidem propostas. **Sim/Não** continuam exclusivos do cartão de aprovação.

**Decisão confirmada:** sem evidência suficiente, mostrar a mensagem de insuficiência, as informações necessárias e confiança baixa; não exibir diagnóstico ou proposta. Não apresentar fontes recuperadas como se sustentassem essa resposta. Consultas transacionais aparecem como “SAP simulado”, sem fingir conexão real.

Registrar etapas reais: solicitação recebida, dados consultados, busca realizada, evidências selecionadas, esclarecimento necessário, proposta aguardando decisão e resultado da execução. Incluir horário e duração quando medidos. Não gerar uma lista fictícia de atividades a partir de texto livre do LLM.

**Decisão confirmada:** o “passo a passo” é uma trilha verificável de operações, evidências e justificativas resumidas; não é uma transcrição de raciocínio interno bruto. A confiança deve ter justificativa legível, não apenas um selo.

## Cartão de aprovação

**Decisão confirmada:** Sim/Não aparecem somente para uma solicitação de confirmação pendente, registrada pelo servidor a partir da proposta da IA. Perguntas abertas de esclarecimento são respondidas no chat.

**Recomendação:** o cartão deve mostrar a frase da IA, a operação permitida, identificação do pedido/item ou chamado, parâmetros efetivos, efeito antes/depois, indicação de simulação e prazo de validade. Não mostrar credenciais, URL de infraestrutura, token de autorização ou hash técnico ao usuário.

Usar os rótulos **Sim, autorizar** e **Não, recusar**, sem escolha automática. A frase gerada pelo modelo não pode ocultar os dados determinados pelo servidor. Se houver divergência entre frase e operação, invalidar a proposta para correção antes de exibir a confirmação.

Após decisão, desabilitar ambos os botões e mostrar o resultado confirmado pelo gateway. Exibir claramente “aguardando aprovação”, “recusada”, “expirada”, “invalidada”, “executada” ou “falhou”, sem confundir aprovada com executada. Uma mensagem digitada como “sim” não substitui o clique validado.

## Estados e aceite visual

**Recomendação:** definir estados vazios, carregamento, falha do provedor, falta de evidência, sessão perdida e indisponibilidade do banco. Mostrar orientação curta e preservar o histórico possível; não exibir stack traces ou segredos.

Aceite: chat e lista localizáveis imediatamente; conteúdo sem sobreposição ou corte; contraste e foco de teclado legíveis; botões acessíveis por teclado; aprovação não depende apenas de cor; fontes podem ser abertas; troca de chamado não troca sua proposta; reenvio não duplica mensagens nem ações.

**Decisão confirmada:** dúvidas materiais sobre o fluxo devem ser discutidas com o usuário. Detalhes menores de espaçamento e apresentação seguem essa direção e podem ser refinados com uma primeira captura real da interface.
