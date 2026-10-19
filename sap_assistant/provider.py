import json
import math
from pathlib import Path
import time

import httpx
from pydantic import ValidationError

from .contracts import Analysis, Evidence, validate_grounding

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "system.txt"


class ProviderError(RuntimeError):
    def __init__(self, message, metadata=None):
        super().__init__(message)
        self.metadata = metadata or {}


class OpenRouter:
    def __init__(self, settings, client=None):
        self.settings = settings
        self.embedding_model = settings.embedding_model
        self.client = client or httpx.Client(timeout=httpx.Timeout(90, connect=10))

    def _post(self, endpoint, payload):
        if not self.settings.api_key:
            raise ProviderError("Configure OPENROUTER_API_KEY para usar o assistente.")
        for attempt in range(3):
            try:
                response = self.client.post("https://openrouter.ai/api/v1/" + endpoint,
                    headers={"Authorization": "Bearer " + self.settings.api_key,
                             "Content-Type": "application/json", "X-Title": "Assistente SAP MM"}, json=payload)
            except httpx.HTTPError:
                # Um timeout pode ter ocorrido após a cobrança; não repetir cegamente.
                raise ProviderError("Falha de conexão com o OpenRouter. Nenhuma ação foi executada.") from None
            if response.status_code in (429, 502, 503) and attempt < 2:
                time.sleep(0.5 * (attempt + 1))
                continue
            if not response.is_success:
                messages = {401: "Chave OpenRouter inválida.", 402: "Créditos insuficientes no OpenRouter.",
                            429: "Limite temporário do OpenRouter atingido."}
                raise ProviderError(messages.get(response.status_code,
                    f"OpenRouter indisponível ou configuração incompatível (HTTP {response.status_code})."))
            try:
                data = response.json()
                if not isinstance(data, dict) or data.get("error"):
                    raise ValueError()
                return data
            except (ValueError, TypeError):
                raise ProviderError("Resposta inválida recebida do OpenRouter.") from None
        raise ProviderError("OpenRouter indisponível.")

    def embed(self, texts):
        data = self._post("embeddings", {"model": self.embedding_model, "input": texts})
        try:
            items = sorted(data["data"], key=lambda x: x["index"])
            if [x["index"] for x in items] != list(range(len(texts))):
                raise ValueError()
            vectors = [[float(v) for v in x["embedding"]] for x in items]
            if not vectors or not vectors[0] or len({len(x) for x in vectors}) != 1:
                raise ValueError()
            if any(not all(math.isfinite(v) for v in vector) or not any(vector) for vector in vectors):
                raise ValueError()
            return vectors
        except (ValueError, TypeError, KeyError):
            raise ProviderError("Embeddings inválidos ou incompatíveis retornados pelo provedor.") from None

    def analyze(self, context, history):
        prompt = PROMPT_PATH.read_text(encoding="utf-8")
        schema = Analysis.model_json_schema()
        # Alguns endpoints traduzem json_schema para JSON mode. O modelo também
        # recebe o contrato explicitamente, e o servidor continua validando-o.
        messages = [{"role": "system", "content": prompt + "\nJSON_SCHEMA OBRIGATÓRIO:\n" + json.dumps(schema, ensure_ascii=False)},
                    {"role": "user", "content": json.dumps({"context": context, "history": history},
                                                            ensure_ascii=False)}]
        attempts = []
        for repair in range(2):
            data = self._post("chat/completions", {
                "model": self.settings.chat_model, "messages": messages, "temperature": 0.1,
                "max_tokens": 3500, "reasoning": {"enabled": False, "exclude": True},
                "provider": {"require_parameters": True},
                "response_format": {"type": "json_schema", "json_schema": {
                    "name": "sap_analysis", "strict": True, "schema": schema}}})
            attempts.append({"model": data.get("model", self.settings.chat_model),
                             "usage": data.get("usage"), "request_id": data.get("id")})
            try:
                content = data["choices"][0]["message"]["content"]
                raw = json.loads(content)
                scope_policy = isinstance(raw, dict) and raw.get("process") == "fora_do_escopo"
                if scope_policy:
                    # Limite de produto determinado no servidor. Descarta fatos,
                    # recomendações externas e qualquer ação dessa classificação.
                    analysis = Analysis(summary="Este assistente atende recebimento de mercadorias com referência "
                        "a pedidos de compra em SAP MM. Sua solicitação está fora desse escopo.",
                        process="fora_do_escopo", facts=[], hypotheses=[], missing_information=[],
                        next_steps=["Para analisar um recebimento, informe o pedido, o item e o problema apresentado."],
                        references=[], confidence="alta", confidence_reason="Aplicação do escopo configurado, sem diagnóstico SAP.",
                        human_review=False, action=None)
                else:
                    analysis = Analysis.model_validate(raw)
                validate_grounding(analysis, [Evidence.model_validate(x) for x in context.get("evidence", [])],
                                   context.get("undocumented_codes", []))
                return analysis, {"requested_model": self.settings.chat_model,
                                  "attempts": attempts, "prompt_version": prompt.splitlines()[0],
                                  "server_policy": "fora_do_escopo" if scope_policy else None}
            except (ValidationError, KeyError, IndexError, TypeError, ValueError) as exc:
                if isinstance(exc, ValidationError):
                    errors = [{"field": list(x["loc"]), "type": x["type"], "message": x["msg"]}
                              for x in exc.errors()[:8]]
                elif type(exc) is ValueError:
                    errors = [{"field": [], "message": str(exc)}]
                else:
                    errors = [{"field": [], "message": "Resposta vazia ou formato inválido."}]
                if repair:
                    raise ProviderError("A IA retornou uma resposta incompatível após uma tentativa de reparo.",
                                        {"requested_model": self.settings.chat_model, "attempts": attempts,
                                         "validation_errors": errors}) from None
                # Não devolver o conteúdo inválido ao modelo nem executar ações para repará-lo.
                messages.append({"role": "user", "content": "A resposta anterior não passou na validação. "
                                 "Responda novamente com todos os campos do esquema, sem ações se houver dúvida. "
                                 "Erros que precisam ser corrigidos: " + json.dumps(errors, ensure_ascii=False)})
        raise ProviderError("Não foi possível validar a resposta.")
