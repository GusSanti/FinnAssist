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
    get_total_expenses,
    get_total_income,
)


def _tool(
    name: str,
    description: str,
    properties: dict[str, Any] | None = None,
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
    _tool("get_total_expenses", "Obtém a soma histórica de todas as despesas do usuário."),
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
]


TOOL_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "get_financial_summary": get_financial_summary,
    "get_balance": get_balance,
    "get_total_income": get_total_income,
    "get_total_expenses": get_total_expenses,
    "get_monthly_balance": get_monthly_balance,
    "get_expenses_by_category": get_expenses_by_category,
    "get_monthly_average": get_monthly_average,
}


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
        result = function(user_id=user_id, **arguments)
        return json.dumps(result, default=_json_default, ensure_ascii=False)
    except (TypeError, ValueError) as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)
    except Exception:
        # Database and infrastructure details must not be exposed to the model/user.
        return json.dumps(
            {"error": "Não foi possível consultar os dados financeiros."},
            ensure_ascii=False,
        )
