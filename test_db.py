import ollama

response = ollama.embed(
    model="embeddinggemma",
    input="O que é uma reserva de emergência?",
)

embedding = response["embeddings"][0]

print(len(embedding))