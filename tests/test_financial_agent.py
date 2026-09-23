import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.ai.financial_agent import _visible_content, answer_financial_question


class FinancialAgentTests(unittest.TestCase):
    def test_hides_reasoning_leaked_by_old_qwen_template(self):
        content = "análise interna longa</think>\n\nResposta visível."
        self.assertEqual(_visible_content(content), "Resposta visível.")

    @patch("app.ai.financial_agent.execute_financial_tool")
    @patch("app.ai.financial_agent.chat")
    def test_tool_result_is_returned_to_model(self, mock_chat, mock_execute):
        tool_call = SimpleNamespace(
            function=SimpleNamespace(
                name="get_monthly_balance",
                arguments={"year": 2026, "month": 9},
            )
        )
        mock_chat.side_effect = [
            SimpleNamespace(
                message=SimpleNamespace(content="", tool_calls=[tool_call])
            ),
            SimpleNamespace(
                message=SimpleNamespace(
                    content="Seu saldo mensal é R$ 4.420,00.",
                    tool_calls=[],
                )
            ),
        ]
        mock_execute.return_value = '"4420.00"'

        answer = answer_financial_question(1, "Qual foi meu saldo em setembro?")

        self.assertEqual(answer, "Seu saldo mensal é R$ 4.420,00.")
        mock_execute.assert_called_once_with(
            "get_monthly_balance",
            {"year": 2026, "month": 9},
            user_id=1,
        )
        second_messages = mock_chat.call_args_list[1].kwargs["messages"]
        tool_message = next(
            message
            for message in second_messages
            if isinstance(message, dict) and message.get("role") == "tool"
        )
        self.assertEqual(tool_message["content"], '"4420.00"')


if __name__ == "__main__":
    unittest.main()
