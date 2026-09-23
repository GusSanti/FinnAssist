"""Ollama agent loop for conversations grounded in financial data."""

import os
from typing import Any

from ollama import chat

from app.ai.financial_tools import FINANCIAL_TOOLS, execute_financial_tool


SYSTEM_PROMPT = """
Você é o assistente financeiro do FinnAssist.
Quando a pergunta depender dos dados pessoais do usuário, use as ferramentas
disponíveis. Nunca invente valores e não tente calcular totais que uma ferramenta
pode consultar. Os resultados monetários estão em reais. Explique a resposta de
forma clara e concisa. Você pode analisar, explicar e alertar, mas não pode executar
investimentos nem tomar decisões financeiras pelo usuário.
""".strip()


def _visible_content(content: str | None) -> str:
    """Remove reasoning leaked into content by older Qwen3 model templates."""
    visible = content or ""
    if "</think>" in visible:
        visible = visible.rsplit("</think>", 1)[1]
    return visible.strip()


def answer_financial_question(
    user_id: int,
    question: str,
    *,
    model: str | None = None,
    max_steps: int = 8,
) -> str:
    """Run a bounded tool-calling loop and return Ollama's final answer."""
    if not question.strip():
        raise ValueError("question must not be empty")
    if max_steps < 1:
        raise ValueError("max_steps must be greater than zero")

    selected_model = model or os.getenv("OLLAMA_MODEL", "qwen3:4b")
    messages: list[Any] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        # This model tag also disables long reasoning on older Qwen3 templates.
        {"role": "user", "content": f"{question.strip()} /no_think"},
    ]

    for _ in range(max_steps):
        try:
            response = chat(
                model=selected_model,
                messages=messages,
                tools=FINANCIAL_TOOLS,
                think=False,
            )
        except Exception as error:
            raise RuntimeError("Não foi possível consultar o Ollama.") from error
        messages.append(response.message)
        tool_calls = response.message.tool_calls or []

        if not tool_calls:
            content = _visible_content(response.message.content)
            if not content:
                raise RuntimeError("Ollama returned an empty response")
            return content

        for tool_call in tool_calls:
            result = execute_financial_tool(
                tool_call.function.name,
                dict(tool_call.function.arguments),
                user_id=user_id,
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_name": tool_call.function.name,
                    "content": result,
                }
            )

    raise RuntimeError("Ollama exceeded the maximum number of tool-calling steps")
