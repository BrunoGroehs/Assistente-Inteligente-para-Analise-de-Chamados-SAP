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
    correction_operation: Literal["registrar_recebimento_simulado", "atualizar_status_chamado"] | None = None

    @model_validator(mode="after")
    def check_action(self):
        if (self.action or self.correction_operation) and self.process == "fora_do_escopo":
            raise ValueError("Ação não permitida fora do escopo.")
        if self.action and self.correction_operation and self.action.operation != self.correction_operation:
            raise ValueError("A proposta deve corresponder à correção indicada.")
        if isinstance(self.action, ReceiptRequest) and self.missing_information:
            raise ValueError("Recebimento não permitido com dados faltantes. Use action=null.")
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


def validate_grounding(analysis, evidence, undocumented_codes=()):
    allowed = {x.id for x in evidence}
    referenced = set(analysis.references)
    facts = {key for fact in analysis.facts for key in fact.evidence_ids}
    if not referenced <= allowed or not facts <= referenced:
        raise ValueError("references deve conter todos os IDs de facts, inclusive DATA/RELATO, e somente IDs fornecidos.")
    knowledge = {x.id for x in evidence if x.kind not in {"consulta_simulada", "relato_usuario"}}
    if analysis.process != "fora_do_escopo" and analysis.confidence == "alta" and not (referenced & knowledge):
        raise ValueError("Confiança alta exige citar conhecimento aplicável além do relato/dados.")
    if (isinstance(analysis.action, ReceiptRequest) or analysis.correction_operation == "registrar_recebimento_simulado") and "DATA" not in referenced:
        raise ValueError("Recebimento exige citar os dados consultados em DATA.")
    if analysis.process != "fora_do_escopo" and undocumented_codes and (analysis.hypotheses or analysis.confidence != "baixa" or not analysis.human_review
                               or isinstance(analysis.action, ReceiptRequest) or analysis.correction_operation):
        raise ValueError("Código não documentado: hypotheses=[], confidence=baixa, human_review=true; não propor recebimento.")

