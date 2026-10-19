# Relação entre recebimento e verificação de fatura

Síntese própria de S06; SAP S/4HANA, release não identificada. Consultado em 18/10/2026. Seção: Supplier Invoices.

Na verificação de fatura baseada em recebimento, quando definida no item do pedido, os dados da fatura são comparados com os recebimentos relacionados. A fonte descreve bloqueio automático para pagamento quando o desvio ultrapassa as tolerâncias configuradas.

O recebimento não equivale à liberação ou pagamento da fatura. Para analisar divergências, são necessários pedido/item, recebimentos e contexto da fatura; a configuração real não pode ser presumida.

A demonstração não consulta faturas nem executa MIRO, liberação de pagamento ou correção contábil. Este guia cobre apenas a relação conceitual com o recebimento.
