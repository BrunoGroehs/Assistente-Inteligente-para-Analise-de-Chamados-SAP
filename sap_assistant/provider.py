import json
import math
from pathlib import Path
import time

import httpx
from pydantic import ValidationError

from .contracts import Analysis

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "system.txt"


class ProviderError(RuntimeError):
    pass


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
        messages = [{"role": "system", "content": prompt},
                    {"role": "user", "content": json.dumps({"context": context, "history": history},
                                                            ensure_ascii=False)}]
        attempts = []
        for repair in range(2):
            data = self._post("chat/completions", {
                "model": self.settings.chat_model, "messages": messages, "temperature": 0.1,
                "max_tokens": 3500, "provider": {"require_parameters": True},
                "response_format": {"type": "json_schema", "json_schema": {
                    "name": "sap_analysis", "strict": True, "schema": Analysis.model_json_schema()}}})
            attempts.append({"model": data.get("model", self.settings.chat_model),
                             "usage": data.get("usage"), "request_id": data.get("id")})
            try:
                content = data["choices"][0]["message"]["content"]
                analysis = Analysis.model_validate_json(content)
                return analysis, {"requested_model": self.settings.chat_model,
                                  "attempts": attempts, "prompt_version": prompt.splitlines()[0]}
            except (ValidationError, KeyError, IndexError, TypeError, ValueError):
                if repair:
                    raise ProviderError("A IA retornou uma resposta incompatível após uma tentativa de reparo.") from None
                # Não devolver o conteúdo inválido ao modelo nem executar ações para repará-lo.
                messages.append({"role": "user", "content": "A resposta anterior não passou na validação. "
                                 "Responda novamente com todos os campos do esquema, sem ações se houver dúvida."})
        raise ProviderError("Não foi possível validar a resposta.")
