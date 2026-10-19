# Tolerâncias e entrega concluída

Síntese própria de S04; SAP S/4HANA, release não identificada. Consultado em 18/10/2026. Seções: Under- and Overdeliveries; Delivery Completed Indicator.

Uma entrega menor pode ser tratada como parcial. A tolerância de subentrega influencia avisos. Sobre-entregas dependem de tolerância percentual ou permissão de sobre-entrega ilimitada no item do pedido; não existe um percentual universal.

O indicador de entrega concluída zera a quantidade em aberto, mesmo sem entrega integral. Isso não significa bloqueio universal de lançamentos adicionais; há diferenças entre aplicativos, como documentado em K03.

No simulador, K05 proíbe excedentes e itens concluídos. Essa regra local é mais restritiva e não autoriza alterar tolerâncias no SAP.
