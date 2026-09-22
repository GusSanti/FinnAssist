from ollama import chat

response = chat(
    model="qwen3:4b",
    messages=[
        {
            "role": "user",
            "content": "Explique o que é renda fixa."
        }
    ]
)

print(response.message.content)