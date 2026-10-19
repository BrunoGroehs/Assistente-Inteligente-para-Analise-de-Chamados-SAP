"""Estado visual derivado, sem conceder autorização ou alterar persistência."""
from copy import deepcopy
from datetime import datetime

from .database import utcnow


def visible_proposals(proposals, now=None):
    """Prazo usa relógio do servidor, mesmo quando a tela usa um snapshot em memória."""
    result = deepcopy(proposals)
    now = now or utcnow()
    for proposal in result:
        if proposal["state"] == "pendente" and datetime.fromisoformat(proposal["expires_at"]) <= now:
            proposal["state"] = "expirada"
            proposal["result"] = {"message": "A solicitação venceu. Envie uma nova análise para continuar."}
    return result
