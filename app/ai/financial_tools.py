"""Tool catalogue and safe dispatcher for the financial assistant."""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable

from app.services.financial_service import (
    get_balance,
    get_expenses_by_category,
    get_financial_summary,
    get_monthly_average,
    get_monthly_balance,
    get_monthly_expenses,
    get_total_expenses,
    get_total_income,
)
from app.services.knowledge_service import search_financial_knowledge


def _tool(
    name: str,
    description: str,
    properties: dict[str, Any] | None = None,
    required: list[str] | None = None,
) -> dict[str, Any]:
    """Build the JSON schema sent to Ollama for one application function."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties or {},
                "required": required or [],
                "additionalProperties": False,
            },
        },
    }


PERIOD_PROPERTIES = {
    "year": {
        "type": "integer",
        "minimum": 1,
        "description": "Ano do período. Omitir junto com month para usar o mês atual.",
    },
    "month": {
        "type": "integer",
        "minimum": 1,
        "maximum": 12,
        "description": "Mês de 1 a 12. Omitir junto com year para usar o mês atual.",
    },
}


FINANCIAL_TOOLS = [
    _tool(
        "get_financial_summary",
        "Obtém um resumo financeiro mensal completo: receitas, despesas, saldo, "
        "média de despesas e gastos por categoria. Prefira esta ferramenta para "
        "perguntas amplas sobre a situação financeira do usuário.",
        {
            **PERIOD_PROPERTIES,
            "average_months": {
                "type": "integer",
                "minimum": 1,
                "maximum": 120,
                "description": "Quantidade de meses usada na média; padrão 6.",
            },
        },
    ),
    _tool("get_balance", "Obtém o saldo histórico total do usuário."),
    _tool("get_total_income", "Obtém a soma histórica de todas as receitas do usuário."),
    _tool(
        "get_total_expenses",
        "Obtém a soma histórica de todas as despesas do usuário. Não use para "
        "perguntas limitadas a um mês.",
    ),
    _tool(
        "get_monthly_expenses",
        "Obtém o total de despesas de um mês. Use para perguntas como 'quanto "
        "gastei neste mês?'.",
        PERIOD_PROPERTIES,
    ),
    _tool(
        "get_monthly_balance",
        "Obtém o saldo (receitas menos despesas) de um mês.",
        PERIOD_PROPERTIES,
    ),
    _tool(
        "get_expenses_by_category",
        "Lista as despesas de um mês agrupadas por categoria, da maior para a menor.",
        PERIOD_PROPERTIES,
    ),
    _tool(
        "get_monthly_average",
        "Calcula a média mensal de despesas em uma janela de meses.",
        {
            **PERIOD_PROPERTIES,
            "months": {
                "type": "integer",
                "minimum": 1,
                "maximum": 120,
                "description": "Tamanho da janela em meses; padrão 6.",
            },
        },
    ),
    _tool(
        "search_financial_knowledge",
        "Busca conceitos, explicações e orientações gerais na base de conhecimento "
        "financeiro. Use para perguntas sobre investimentos, reserva de emergência, "
        "riscos e educação financeira. Não use para consultar valores pessoais.",
        {
            "query": {
                "type": "string",
                "minLength": 1,
                "description": "Pergunta completa ou termos que devem ser pesquisados.",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 20,
                "description": "Quantidade de chunks; padrão 5.",
            },
        },
        required=["query"],
    ),
]


TOOL_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "get_financial_summary": get_financial_summary,
    "get_balance": get_balance,
    "get_total_income": get_total_income,
    "get_total_expenses": get_total_expenses,
    "get_monthly_expenses": get_monthly_expenses,
    "get_monthly_balance": get_monthly_balance,
    "get_expenses_by_category": get_expenses_by_category,
    "get_monthly_average": get_monthly_average,
    "search_financial_knowledge": search_financial_knowledge,
}

USER_SCOPED_TOOLS = frozenset(TOOL_FUNCTIONS) - {"search_financial_knowledge"}


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Unsupported result type: {type(value).__name__}")


def execute_financial_tool(
    tool_name: str,
    arguments: dict[str, Any],
    *,
    user_id: int,
) -> str:
    """Execute only an allow-listed tool, always scoped to the API's user."""
    function = TOOL_FUNCTIONS.get(tool_name)
    if function is None:
        return json.dumps({"error": "Ferramenta desconhecida."}, ensure_ascii=False)
    if "user_id" in arguments:
        return json.dumps(
            {"error": "O argumento user_id não pode ser definido pelo modelo."},
            ensure_ascii=False,
        )

    try:
        if tool_name in USER_SCOPED_TOOLS:
            result = function(user_id=user_id, **arguments)
        else:
            result = function(**arguments)
        return json.dumps(result, default=_json_default, ensure_ascii=False)
    except (TypeError, ValueError) as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)
    except Exception:
        # Database and infrastructure details must not be exposed to the model/user.
        message = (
            "Não foi possível consultar a base de conhecimento."
            if tool_name == "search_financial_knowledge"
            else "Não foi possível consultar os dados financeiros."
        )
        return json.dumps(
            {"error": message},
            ensure_ascii=False,
        )
