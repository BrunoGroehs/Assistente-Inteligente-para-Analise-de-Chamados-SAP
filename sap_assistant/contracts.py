from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReceiptParameters(Contract):
    purchase_order: str = Field(pattern=r"^\d{10}$")
    item: str = Field(pattern=r"^\d{1,5}$")
    quantity: Decimal = Field(gt=0, le=1000000000, max_digits=16, decimal_places=3, allow_inf_nan=False)
    unit: str = Field(min_length=1, max_length=8)
    material: str = Field(min_length=1, max_length=40)
    plant: str = Field(min_length=1, max_length=10)
    storage_location: str = Field(min_length=1, max_length=10)
    posting_date: date


class StatusParameters(Contract):
    status: Literal["em_validacao_humana", "resolvido"]


class ReceiptRequest(Contract):
    operation: Literal["registrar_recebimento_simulado"]
    parameters: ReceiptParameters
    confirmation_phrase: str = Field(min_length=10, max_length=500)


class StatusRequest(Contract):
    operation: Literal["atualizar_status_chamado"]
    parameters: StatusParameters
    confirmation_phrase: str = Field(min_length=10, max_length=500)


ActionRequest = Annotated[ReceiptRequest | StatusRequest, Field(discriminator="operation")]


class Fact(Contract):
    text: str = Field(min_length=1, max_length=1500)
    evidence_ids: list[str] = Field(min_length=1, max_length=8)


class Analysis(Contract):
    summary: str = Field(min_length=1, max_length=2000)
    process: Literal["recebimento_pedido_compra", "fora_do_escopo"]
    facts: list[Fact] = Field(max_length=12)
    hypotheses: list[str] = Field(max_length=8)
    missing_information: list[str] = Field(max_length=8)
    next_steps: list[str] = Field(max_length=8)
    references: list[str] = Field(max_length=12)
    confidence: Literal["alta", "media", "baixa"]
    confidence_reason: str = Field(min_length=1, max_length=1200)
    human_review: bool
    action: ActionRequest | None

    @model_validator(mode="after")
    def check_action(self):
        if self.action and (self.process == "fora_do_escopo" or self.missing_information):
            raise ValueError("Ação não permitida fora do escopo ou com dados faltantes.")
        if isinstance(self.action, ReceiptRequest) and self.confidence == "baixa":
            raise ValueError("Recebimento não pode ser proposto sem fundamentação suficiente.")
        if self.process == "fora_do_escopo" and self.facts:
            raise ValueError("Resposta fora do escopo não deve afirmar fatos SAP.")
        return self


class Evidence(Contract):
    id: str
    title: str
    content: str
    kind: str
    source_url: str | None = None
    version: str

