"""Run retrieval directly, without the conversational model."""

import argparse

from app.services.knowledge_service import search_financial_knowledge


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", help="Pergunta usada na busca semântica")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    response = search_financial_knowledge(args.question, args.limit)
    for index, result in enumerate(response["results"], start=1):
        print(
            f"{index}. {result['title']} | {result['source']} | "
            f"similarity={result['similarity']:.6f}"
        )
        print(result["content"])
        print()


if __name__ == "__main__":
    main()
