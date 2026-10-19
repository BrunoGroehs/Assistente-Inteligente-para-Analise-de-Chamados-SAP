"""Consolida as jornadas de navegador e lê metadados das próprias mensagens de teste.

Não chama LLM, não escreve no banco e não consulta dados de tabelas externas.
O catálogo externo é comparado apenas em sua estrutura.
"""
import hashlib
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from sap_assistant.config import Settings
from sap_assistant.database import Message, Store, utcnow
from verify_web_live import outside_catalog

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "evidencias/jornadas-usuario"


def main():
    reports = []
    runs = ("inicial", "reteste", "reteste-verificacao", "reteste-cautela")
    for run in runs:
        for path in sorted((DIRECTORY / run).glob("U*.json")):
            reports.append({"run": run, "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                            **json.loads(path.read_text(encoding="utf-8"))})
    ids = {question["answer"]["id"] for report in reports for question in report["questions"]}
    settings = Settings.load()
    store = Store(settings.database_url)
    provenance, usage, models = [], {}, set()
    try:
        with store.engine.connect() as connection:
            # IDs pertencem exclusivamente às respostas coletadas nestas jornadas.
            rows = connection.execute(select(Message.id, Message.details).where(Message.id.in_(ids))).all()
        for key, details in rows:
            generation = details.get("provider", {})
            coverage = details.get("knowledge_check", {}).get("provider", {})
            attempts = [*generation.get("attempts", []), *([coverage] if coverage.get("model") else [])]
            for attempt in attempts:
                if attempt.get("model"):
                    models.add(attempt["model"])
                for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
                    value = (attempt.get("usage") or {}).get(field)
                    if isinstance(value, int):
                        usage[field] = usage.get(field, 0) + value
            provenance.append({"message_id": key, "prompt_version": generation.get("prompt_version"),
                "application_context": bool(details.get("application_context")),
                "retrieved_ids": (details.get("retrieval") or {}).get("selected_ids", []),
                "references": (details.get("analysis") or {}).get("references", []),
                "coverage_supports": (details.get("knowledge_check") or {}).get("supports", []),
                "chat_requests_with_reported_metadata": len(attempts)})
        previous_path = ROOT / ".local/catalogo-antes-jornadas.json"
        before = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else {}
        after = outside_catalog(store)
    finally:
        store.engine.dispose()
    latest = {report["id"]: report for report in reports}
    timings = [question["elapsed_ms"] for report in reports for question in report["questions"]]
    summary = {"date": utcnow().isoformat(), "mode": "Edge headless com serviços reais e cliques automatizados",
        "runs": {run: {"scenarios": sum(report["run"] == run for report in reports),
                        "questions": sum(len(report["questions"]) for report in reports if report["run"] == run),
                        "passed": all(report["status"] == "passed" for report in reports if report["run"] == run)}
                 for run in runs},
        "unique_scenarios": len(latest), "questions_total": len(timings),
        "scenario_executions": len(reports),
        "last_evidence_all_passed": all(report["status"] == "passed" for report in latest.values()),
        "code_hash_normalization": "Texto UTF-8 com finais de linha LF",
        "code_files_sha256": {name: hashlib.sha256((ROOT / name).read_text(encoding="utf-8").encode()).hexdigest() for name in (
            "prompts/system.txt", "prompts/knowledge.txt", "sap_assistant/application_context.py",
            "sap_assistant/contracts.py", "sap_assistant/service.py", "frontend/e2e/jornadas-reais.spec.ts")},
        "latest_per_scenario": [{"id": key, "file": report["file"], "status": report["status"]}
                                for key, report in sorted(latest.items())],
        "observed_harness_ms": {"min": min(timings), "median": round(statistics.median(timings)), "max": max(timings)},
        "models_reported": sorted(models), "usage_reported_chat_only": usage,
        "chat_requests_with_reported_metadata": sum(item["chat_requests_with_reported_metadata"] for item in provenance),
        "provenance": sorted(provenance, key=lambda item: item["message_id"]),
        "external_catalog": {"before": before.get("hash"), "after": after,
                             "unchanged": before.get("hash") == after if before else None},
        "limits": ["Asserções automatizadas não certificam toda a qualidade semântica; consultar revisão escrita.",
                   "Tempos incluem automação e uma leitura de verificação adicional; não são SLA ou ganho de produtividade.",
                   "Tokens são os campos informados pelas chamadas de chat destas respostas; não incluem embeddings ou custos.",
                   "Comparação do catálogo externo não verifica conteúdo de todas as tabelas externas."]}
    (DIRECTORY / "resumo.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("runs", "questions_total", "unique_scenarios", "models_reported")}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Falha de SQL pode conter DSN; nunca imprimir o erro bruto.
        print(json.dumps({"passed": False, "error_type": type(exc).__name__}))
        raise SystemExit(1) from None
