import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.ai.financial_agent import _visible_content, answer_financial_question


class FinancialAgentTests(unittest.TestCase):
    def test_hides_reasoning_leaked_by_old_qwen_template(self):
        content = "análise interna longa</think>\n\nResposta visível."
        self.assertEqual(_visible_content(content), "Resposta visível.")

    @patch("app.ai.financial_agent.execute_financial_tool")
    @patch("app.ai.financial_agent.Client")
    def test_tool_result_is_returned_to_model(self, mock_client, mock_execute):
        tool_call = SimpleNamespace(
            function=SimpleNamespace(
                name="get_monthly_balance",
                arguments={"year": 2026, "month": 9},
            )
        )
        mock_client.return_value.chat.side_effect = [
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
        second_messages = mock_client.return_value.chat.call_args_list[1].kwargs[
            "messages"
        ]
        tool_message = next(
            message
            for message in second_messages
            if isinstance(message, dict) and message.get("role") == "tool"
        )
        self.assertEqual(tool_message["content"], '"4420.00"')

    @patch("app.ai.financial_agent.execute_financial_tool")
    @patch("app.ai.financial_agent.Client")
    def test_combined_question_can_call_financial_and_rag_tools(
        self,
        mock_client,
        mock_execute,
    ):
        financial_call = SimpleNamespace(
            function=SimpleNamespace(name="get_monthly_average", arguments={})
        )
        rag_call = SimpleNamespace(
            function=SimpleNamespace(
                name="search_financial_knowledge",
                arguments={"query": "Como pensar a reserva de emergência?"},
            )
        )
        mock_client.return_value.chat.side_effect = [
            SimpleNamespace(
                message=SimpleNamespace(
                    content="",
                    tool_calls=[financial_call, rag_call],
                )
            ),
            SimpleNamespace(
                message=SimpleNamespace(content="Resposta combinada.", tool_calls=[])
            ),
        ]
        mock_execute.side_effect = [
            '"2500.00"',
            '{"results": [{"source": "knowledge/reserva_emergencia.md"}]}',
        ]

        answer = answer_financial_question(
            3,
            "Como pensar minha reserva usando minha média de despesas?",
        )

        self.assertEqual(answer, "Resposta combinada.")
        self.assertEqual(mock_execute.call_count, 2)
        mock_execute.assert_any_call("get_monthly_average", {}, user_id=3)
        mock_execute.assert_any_call(
            "search_financial_knowledge",
            {"query": "Como pensar a reserva de emergência?"},
            user_id=3,
        )


if __name__ == "__main__":
    unittest.main()
