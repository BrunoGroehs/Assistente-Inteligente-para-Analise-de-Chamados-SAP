# Cola de gravação — 18 minutos

**Recomendação:** deixe este arquivo fora da área compartilhada e use o [roteiro completo](11-roteiro-apresentacao.md) para ensaiar as falas.

## Antes de começar

- App executando e janela privada nova; microfone e texto legíveis.
- README, diagrama, catálogo, prompts e evidências abertos; `.env` fechado.
- Nova tomada de C07 exige sessão nova para repetir os números iniciais. Novo chat não reinicia recebimentos.
- Diga logo: **SAP e dados simulados; nenhuma integração SAP real**.

## Ordem e perguntas para copiar

| Minuto | Tela / ação | Pergunta ou observação |
| --- | --- | --- |
| 0–2 | Abertura, Chamados → C01 → Ver detalhes | Problema manual; recorte MM; oito casos; relato separado da consulta. |
| 2–4 | Diagrama e catálogo | React → FastAPI → RAG/OpenRouter/Supabase. Busca híbrida → cobertura → análise validada. |
| 4–6 | Anexar C01; enviar P1 | Mostrar 40 UN, fonte clicável, confiança e etapas. Remover anexo mantém a conversa. |
| 6–7 | Novo chat → C05; enviar P2 | Pedir contexto sem inventar pedido ou causa. |
| 7–8 | Novo chat → C06; enviar P3 | Sem base suficiente, sem diagnóstico nem proposta. |
| 8–11 | Novo chat → C03; enviar P4 | Preparar correção: 35 bloqueado; informar 20 e `2026-10-18`; Revisar → **Não**. |
| 11–13 | Novo chat → C07; enviar P5 | Conferir saldo 30 → 20; **Sim**; resultado SIM; recebida 20 → 30; chamado continua aberto. |
| 13–14 | Novo chat, sem anexo; enviar P6 | Limite de escopo. |
| 14–16 | Prompts e evidências | Contratos; dados não confiáveis; registro; testes; como medir resultado. |
| 16–18 | Encerramento | API SAP autorizada, privilégio mínimo, mesma aprovação; limitações e próximos passos. |

**P1 — C01:**

```text
Recebi 60 UN de 100. Por que ainda aparecem 40? Explique sem solicitar alteração.
```

**P2 — C05:**

```text
Está dando erro ao receber material. Como resolvo?
```

**P3 — C06:**

```text
Qual a causa e a correção da mensagem ZMM_999? Pode corrigir?
```

**P4 — C03:**

```text
como resolvo isso?
```

Preencher quantidade e data é uma decisão do operador, não um valor escolhido pela IA. Preparar não executa. Não afirmar que a proposta parcial resolve as 15 UN excedentes da entrega física.

**P5 — C07:**

```text
Registre o recebimento de 10 UN no pedido 4500001007, item 10, em 2026-10-18.
```

**P6 — sem anexo:**

```text
Calcule minha folha de pagamento e minhas férias.
```

## Frases que não podem faltar

- “O modelo propõe; o servidor valida; o humano autoriza a operação exata.”
- “Consultar dados não comprova uma causa sem documentação aplicável.”
- “A confiança é qualitativa e justificada, não uma probabilidade calibrada.”
- “As etapas são operações observáveis, não raciocínio interno bruto.”
- “Novo chat limpa o contexto, preservando os dados de negócio.”
- “Não medi ainda um percentual de produtividade; compararia tempo, qualidade e retrabalho nos mesmos casos.”
- “Para SAP real, preservaria privilégio mínimo, aprovação, auditoria e conciliação de operações remotas.”

## Checagem final

Um sucesso + duas exceções; fonte e confiança; pergunta por dados; falta de evidência; Não e Sim; fora do escopo; arquitetura; prompts; evidências; riscos; acesso seguro a SAP; medição; menos de 20 minutos.
