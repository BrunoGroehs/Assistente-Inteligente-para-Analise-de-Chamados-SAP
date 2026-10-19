# Roteiro de gravação para a entrevista

**Duração planejada:** 18 minutos, com dois minutos de reserva até o limite de 20. **Classificação:** recomendação de apresentação baseada no enunciado conferido no PDF versionado, nos requisitos de [01-desafio.md](01-desafio.md) e no comportamento implementado. Os resultados efetivamente observados ficam nas [evidências](../evidencias/README.md).

Use as falas como apoio e apresente com suas palavras. A parte central é a demonstração do processo SAP, da fundamentação e dos limites de autonomia. Não é necessário percorrer cada arquivo ou cada um dos oito chamados ao vivo.

## Preparação antes de gravar

1. Execute o aplicativo conforme o [README](../README.md). Confira OpenRouter e Supabase, sem abrir `.env` na gravação.
2. Use uma janela privada nova para obter uma sessão fictícia limpa. **Novo chat preserva os recebimentos da sessão**; ele não reinicia os dados. Em uma nova tomada, use outra sessão privada se precisar repetir os valores iniciais.
3. Deixe abertas apenas a aplicação, o [diagrama](03-arquitetura.md) em um visualizador com suporte a Mermaid, o [catálogo](../conhecimento/catalogo.json), os [prompts](05-prompts.md) e o relatório de testes. Evite mostrar configuração de infraestrutura ou credenciais.
4. Prepare os textos da [cola de gravação](12-cola-gravacao.md). As datas são explícitas e pertencem aos exemplos fictícios; não são inferidas como a data de hoje.
5. Faça um ensaio com cronômetro. A análise real depende da rede e do provedor; aproveite a espera para explicar a etapa exibida. Se cortar uma espera no vídeo, indique o corte.
6. Verifique áudio, legibilidade do texto e zoom. Mantenha visíveis os parâmetros e o efeito do cartão ao confirmar ou recusar.

## Sequência de 18 minutos

| Tempo | Mostrar | Mensagem principal |
| --- | --- | --- |
| 00:00–01:15 | Tela inicial | Problema manual, objetivo e limite da prova de conceito. |
| 01:15–02:15 | Chamados e detalhes de C01 | Recorte SAP MM, oito casos e diferença entre relato e dado consultado. |
| 02:15–03:45 | Diagrama e catálogo | Por que GenAI, arquitetura e percurso do RAG. |
| 03:45–06:00 | C01, fontes e remoção do anexo | Sucesso consultivo: saldo correto, referência e confiança. |
| 06:00–07:15 | Novo chat com C05 | Exceção 1: faltam dados, então o assistente pergunta. |
| 07:15–08:15 | Novo chat com C06 | Exceção 2: falta documentação, então o assistente se abstém. |
| 08:15–11:15 | Novo chat com C03 | Correção guiada, limite de quantidade e recusa humana. |
| 11:15–13:00 | Novo chat com C07 | Aprovação específica e resultado do recebimento simulado. |
| 13:00–13:45 | Chat geral, pergunta de HR | Limite de escopo. |
| 13:45–15:00 | Prompts e uma trilha de atendimento | Contratos, cobertura, instruções não confiáveis e auditoria. |
| 15:00–16:00 | Evidências de testes | O que foi testado e como medir qualidade e produtividade. |
| 16:00–17:30 | Diagrama ou tela do app | Riscos, evolução e acesso seguro a SAP real. |
| 17:30–18:00 | Tela inicial ou resultado confirmado | Valor entregue e limites atuais. |

## Falas e ações sugeridas

### 1. Abertura: o problema que você escolheu resolver

**Fala sugerida:**

> “Este é um assistente para apoiar a análise de chamados SAP. A atividade que quero reduzir é o trabalho repetitivo de entender o relato, procurar documentação, conferir os dados e preparar uma orientação consistente.
>
> Escolhi SAP MM, no recebimento de mercadorias com referência a pedidos de compra. A demonstração usa oito chamados e dados fictícios. Não há conexão com um SAP real. A IA interpreta e recomenda; qualquer alteração de negócio depende de uma decisão humana validada pelo servidor.”

Evite dizer que o assistente resolve qualquer incidente SAP ou que já reduziu o tempo em um percentual medido. Essa comprovação exigiria uma comparação controlada.

### 2. Processo SAP e contexto do chamado

**Na tela:** clique em **Chamados**, busque `SIM-C01` e abra **Ver detalhes**. Mostre descrição, ambiente, componente sugerido, impacto e pedido. Anexe o chamado.

**Fala sugerida:**

> “O processo começa com um pedido de compra, passa pela conferência do material recebido e registra o recebimento com referência ao pedido. O histórico permite acompanhar o que já foi recebido e o que ainda está pendente.
>
> Os casos incluem recebimento parcial, quantidade excedente, item ausente no aplicativo e relato incompleto. O formato é inspirado no suporte SAP for Me, mas os identificadores SIM e as situações são locais. Também separo o que o usuário relatou dos dados efetivamente consultados no simulador.”

Se a banca perguntar sobre C04, explique que o comportamento do aplicativo **Post Goods Receipt for Purchasing Document** não deve ser generalizado como bloqueio universal na MIGO. A aplicabilidade depende de aplicativo, configuração e versão; [fontes e processo](02-processo-sap.md).

### 3. Arquitetura e justificativa da IA

**Na tela:** mostre o Mermaid em [03-arquitetura.md](03-arquitetura.md) e o catálogo com 12 guias.

**Fala sugerida:**

> “A interface usa React e TypeScript, e a API usa Python com FastAPI. Conversas, evidências, propostas e auditoria ficam no Supabase. A busca semântica usa PostgreSQL com pgvector. Chat e embeddings vêm do OpenRouter: Qwen3.6 Plus e Qwen3 Embedding 8B.
>
> GenAI ajuda a interpretar relatos escritos de formas diferentes e explicar uma orientação com contexto. Regras como quantidade permitida, validade da proposta e autorização continuam em código determinístico.
>
> A base tem dez sínteses próprias em português, referenciadas em nove páginas oficiais, e duas políticas do simulador. Não é uma cópia de toda a documentação SAP nem um acesso a SAP Notes restritas.
>
> A busca combina similaridade semântica com termos e números. Seleciona até quatro guias oficiais, acrescenta as políticas e verifica se os parágrafos recuperados cobrem a pergunta atual. Só então gera a análise. O servidor valida o esquema e as referências antes de exibir a resposta.”

Precisão técnica: cada guia é uma unidade de recuperação nesta base pequena. A busca textual atual usa correspondência de termos; não apresente como um mecanismo completo de pesquisa corporativa ou um índice vetorial distribuído.

### 4. Sucesso consultivo: C01

**Pergunta para colar:**

```text
Recebi 60 UN de 100. Por que ainda aparecem 40? Explique sem solicitar alteração.
```

**Mostrar:** saldo de 40, fonte numérica clicável, **Fontes e detalhes**, confiança justificada, dados consultados e etapas. Abra uma fonte oficial e volte para o chat. Remova o anexo para mostrar que ele é opcional; a conversa permanece.

**Fala sugerida:**

> “Aqui a resposta explica o saldo com base nos dados consultados e no conhecimento recuperado. Uma entrega parcial, por si só, não significa erro. Nenhuma escrita é necessária para responder a essa dúvida.
>
> Os números levam à fonte oficial ou à identificação de uma regra interna. As referências recuperadas e não usadas ficam separadas. A confiança é qualitativa e acompanhada de justificativa; não é uma probabilidade calibrada de acerto.
>
> As etapas mostram o que o sistema fez, como consultar e recuperar evidências. Não são uma exposição do raciocínio interno do modelo.”

Opcional, se houver tempo: sem anexo, pergunte “O que é recebimento com referência ao pedido?”. O modo geral mantém o RAG e não consulta o pedido anterior.

### 5. Exceção 1: informações insuficientes no relato — C05

**Ações:** Novo chat → Chamados → `SIM-C05` → Anexar.

```text
Está dando erro ao receber material. Como resolvo?
```

**Fala sugerida:**

> “Este relato não identifica suficientemente o incidente. O assistente pede os dados necessários e não inventa pedido, mensagem de erro ou causa. Essa pergunta de esclarecimento faz parte do atendimento, em vez de produzir uma correção com base em suposição.”

Mostre uma ou duas informações solicitadas. Não é necessário preencher o complemento neste vídeo; ele pode ser usado como demonstração adicional.

### 6. Exceção 2: falta de evidência na base — C06

**Ações:** Novo chat → anexar `SIM-C06`.

```text
Qual a causa e a correção da mensagem ZMM_999? Pode corrigir?
```

**Fala sugerida:**

> “Agora o contexto do pedido existe, mas o significado desta mensagem customizada não está documentado na base. O assistente informa que não tem conhecimento suficiente, sinaliza revisão humana e não inventa uma causa ou proposta de correção.
>
> Ter dados transacionais não substitui ter documentação aplicável. Também não basta encontrar uma página sobre um assunto parecido.”

Não prometa que esse mecanismo elimina toda alucinação: a avaliação de cobertura também usa LLM e continua sujeita a erro. O contrato e a revisão humana são camadas complementares.

### 7. Correção guiada e recusa — C03

**Ações:** Novo chat → anexar `SIM-C03`.

```text
como resolvo isso?
```

**Mostrar:** pedido de 100 UN, 80 recebidas e saldo de 20; relato de entrega de 35. Clique em **Preparar correção**. Digite 35 e a data explícita `2026-10-18`: **Revisar ação** deve ficar indisponível. Troque para 20 e prepare a proposta. Mostre quantidade, pedido/item, localização, data, saldo antes/depois e prazo. Clique em **Não, recusar**.

**Fala sugerida:**

> “A tentativa excede o saldo em 15 UN. No simulador, não é permitido ultrapassar o saldo ou alterar tolerâncias. Essa regra local não significa que todo SAP real tenha a mesma configuração de sobre-entrega.
>
> A IA oferece uma correção, mas não decide a quantidade correta nem inventa uma data. Eu complemento esses dados. Para demonstrar o cartão, estou selecionando 20 UN explicitamente; isso não resolve o tratamento físico das outras 15 UN entregues.
>
> Preparar não executa. O servidor apresenta o efeito concreto para uma decisão separada. Vou recusar: nenhum recebimento é registrado e o saldo permanece igual.”

Se mostrar o link de uma política interna, explique que ele abre a identificação em **Fontes e detalhes**, sem fabricar uma URL SAP. O comportamento de “altere para mim” mantendo a operação de recebimento também foi incluído nos testes; não precisa repetir essa rodada ao vivo se o tempo estiver curto.

### 8. Aprovação e execução simulada — C07

**Ações:** Novo chat → anexar `SIM-C07`. Antes de enviar, mostre os dados atuais do pedido: 50 pedidas, 20 recebidas, saldo 30.

```text
Registre o recebimento de 10 UN no pedido 4500001007, item 10, em 2026-10-18.
```

**Mostrar:** proposta pendente e saldo 30 → 20. Só depois de conferir, clique em **Sim, autorizar**. Mostre o resultado com identificador `SIM-...`. Abra os detalhes do anexo para mostrar o total recebido passando de 20 para 30. A situação do chamado permanece aberta.

**Fala sugerida:**

> “Aqui todos os parâmetros estão disponíveis. Mesmo assim, a proposta fica pendente. A IA não recebeu ferramenta para aprovar nem acesso direto ao executor.
>
> O clique autoriza somente esta proposta. O gateway confere sessão, conversa, integridade, validade e dados atuais, e executa a operação em uma transação. Repetir a decisão não repete o recebimento.
>
> Agora há um recebimento simulado confirmado. O identificador não é um documento SAP real. E registrar a entrega não resolve automaticamente o chamado; uma mudança de situação exigiria outra aprovação.”

Os fatos da resposta são o snapshot consultado antes da execução. Para mostrar o estado atual, use **Atualizar** e os detalhes do chamado. Não apresente um fato histórico como se devesse ser reescrito após a aprovação.

### 9. Fora do escopo

**Ações:** Novo chat, sem anexo.

```text
Calcule minha folha de pagamento e minhas férias.
```

**Fala sugerida:**

> “A aplicação tem um recorte definido e informa esse limite. Não produz uma resposta de HR nem usa uma fonte de recebimento como fundamento para outro processo.”

### 10. Prompts, segurança e registro

**Na tela:** `prompts/system.txt`, `prompts/knowledge.txt` e uma resposta com etapas. Não mostrar configuração secreta do provedor.

**Fala sugerida:**

> “Separei o prompt de cobertura do prompt de análise. O primeiro verifica se existe suporte; o segundo organiza a resposta e uma eventual proposta. Ambos usam contratos estruturados, validados novamente no servidor.
>
> Mensagens e documentos recuperados são tratados como dados não confiáveis. Um texto pedindo para ignorar regras não vira autorização. URLs de fonte vêm do catálogo e de referências validadas, não de endereços inventados pelo modelo.
>
> Solicitação, resposta, fontes utilizadas, etapas, versões e decisões ficam registradas. No banco, a aplicação se limita ao seu próprio schema, preservando os outros projetos.”

### 11. Testes e medição de resultado

**Na tela:** seção mais recente de [evidencias/README.md](../evidencias/README.md), relatório de jornadas e uma captura. Use os números registrados nessa versão; não some contagens de suítes antigas.

**Fala sugerida:**

> “Testei contratos, recuperação, falta de evidência, parâmetros inválidos, expiração, isolamento, recusa, duplicação e rollback. Também executei conversas pelo navegador com o modelo e o banco reais. Os cliques desses testes são automatizados em dados fictícios e não representam consentimento de uma pessoa.
>
> Para medir ganho de produtividade, compararia os mesmos casos em análise manual e assistida, com avaliação humana equivalente. Mediria tempo até uma orientação aceita, fidelidade das fontes, necessidade de esclarecimento, retrabalho, latência e consumo. Não afirmo um percentual de ganho que ainda não foi medido.”

### 12. Evolução para SAP real e fechamento

**Fala sugerida:**

> “Para acessar SAP real, eu colocaria um adaptador com APIs autorizadas, identidade de privilégio mínimo e separação de leitura e escrita. Credenciais continuariam no servidor. Aprovação, auditoria e validação dos parâmetros seriam preservadas. Uma operação remota ainda exigiria idempotência e conciliação; a transação local do protótipo não garante atomicidade em outro sistema.
>
> Os próximos passos são ampliar e validar a base com especialistas, identificar versões aplicáveis, calibrar a avaliação e adicionar autenticação individual antes de uso mais amplo. O corpus é pequeno e a simulação não implementa estornos, Customizing ou contabilização real.
>
> A entrega demonstra um fluxo completo: interpretar o chamado, buscar evidência, pedir contexto quando necessário, explicar os limites e submeter a ação ao humano antes de alterar os dados.”

## Conferência com o que a banca pede

| Item do enunciado | Onde aparece no vídeo |
| --- | --- |
| Atividade manual transformada e adequação de GenAI | Abertura e arquitetura. |
| Módulo permitido e cinco a dez casos | SAP MM e lista dos oito chamados. |
| Interpretação, processo e orientação | C01 e contexto do recebimento. |
| RAG, fontes, confiança e Prompt Engineering | Diagrama, C01, catálogo e prompts. |
| Perguntas adicionais | C05. |
| Falta de evidência, risco e prevenção de invenções | C06 e limites explicados. |
| Ao menos um sucesso e duas exceções | C01/C07, C05 e C06. |
| Recomendação separada da ação e HITL | C03 com Não e C07 com Sim. |
| Perguntas fora do escopo | Pergunta sobre HR. |
| Registro e organização técnica | Etapas, persistência e evidências. |
| Acesso seguro a SAP real | Evolução com adaptador e limites de autorização. |
| Medição de tempo, qualidade e produtividade | Protocolo de comparação, sem percentuais inventados. |
| Código, README, diagrama, base, casos, decisões, testes e limitações | Arquivos mostrados e referências do repositório. |
| Demonstração de até 20 minutos | Planejamento de 18 minutos com reserva. |

Os pesos do enunciado estão em [01-desafio.md](01-desafio.md). Processo SAP, aplicação de GenAI e RAG/fundamentação somam 60%; segurança e HITL somam outros 25%. Reserve a maior parte do vídeo para esses comportamentos.

## Se algo falhar durante a gravação

Identifique a etapa que falhou. Se utilizar uma captura ou gravação de teste anterior, sinalize que é uma evidência de execução anterior. Não troque silenciosamente por um mock nem descreva como executada uma ação ainda pendente. Pare antes de 20 minutos; arquivos e casos extras ficam disponíveis para perguntas da banca.
