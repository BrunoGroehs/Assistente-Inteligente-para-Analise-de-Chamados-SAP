# Interface e direção visual

## Direção confirmada

**Decisão confirmada:** interface organizada, clean e inspirada em iOS, sem excesso de elementos decorativos. A implementação será em Streamlit, preservando os componentes nativos e sua acessibilidade. Inspiração visual não significa replicar integralmente um aplicativo Apple.

**Recomendação:** fundo neutro claro, superfícies discretas, tipografia consistente, espaçamento confortável, bordas suaves e uma cor de destaque contida. Usar vermelho para erro/recusa e outros estados por necessidade semântica. Não depender apenas da cor para comunicar estado.

Evitar gradientes chamativos, banners grandes, emojis em excesso, sombras fortes, menus duplicados, cartões para todo parágrafo e painéis de métricas sem função no atendimento. Preferir CSS pequeno e estável; não depender de seletores internos frágeis para a experiência principal. Não adicionar componentes React personalizados nesta versão.

## Organização

**Decisão confirmada:** lista lateral de chamados e chat do chamado selecionado; fontes e etapas em detalhes expansíveis.

**Recomendação de composição:**

1. Lateral com título curto, lista dos oito chamados e indicação textual de situação. Trocar de chamado preserva o histórico correto.
2. Área principal com título do chamado, breve contexto e aviso discreto de ambiente simulado.
3. Conversa com mensagens do usuário e do assistente, campo de entrada e indicador de processamento.
4. Em cada resposta, resumo útil primeiro; detalhes de fontes, confiança e etapas disponíveis sem dominar a tela.
5. Cartão de aprovação próximo da mensagem que o originou. Não criar um centro de aprovações separado nesta versão.

Em telas estreitas, usar a lateral recolhível do Streamlit e manter texto, detalhes e botões utilizáveis. Não exigir rolagem horizontal para ler o conteúdo essencial.

## Fontes e etapas observáveis

**Decisão confirmada e implementada, substituindo o popup:** os números nos fatos e os links em **Fontes citadas** abrem diretamente o site oficial. Agrupar a mesma URL em um único item com os números correspondentes. Exibir título e origem de modo compacto; não mostrar o conteúdo dos documentos, parágrafos ou diálogo de fonte. Metadados e textos continuam no histórico interno.

**Fontes citadas**, **Referências consultadas**, **Dados consultados** e **Etapas do atendimento** têm funções separadas. Referências apenas recuperadas ficam recolhidas e identificadas como não usadas na resposta. Dados do simulador têm resumo próprio. Políticas internas aparecem em uma linha, sem URL SAP inventada. Links externos não geram nova análise nem decidem propostas. **Sim/Não** continuam exclusivos do cartão de aprovação.

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

Aceite: chat e lista localizáveis imediatamente; conteúdo sem sobreposição ou corte; contraste e foco de teclado legíveis; botões acessíveis por teclado; aprovação não depende apenas de cor; fontes podem ser abertas; troca de chamado não troca sua proposta; rerun não duplica mensagens nem ações.

**Decisão confirmada:** dúvidas materiais sobre o fluxo devem ser discutidas com o usuário. Detalhes menores de espaçamento e apresentação seguem essa direção e podem ser refinados com uma primeira captura real da interface.
