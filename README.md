# FinAssist AI — Assistente Financeiro Inteligente com RAG

## 1. Visão Geral

O **FinAssist AI** é um assistente financeiro inteligente desenvolvido em Python que utiliza modelos de linguagem executados através do **Ollama**, técnicas de **RAG — Retrieval-Augmented Generation**, banco de dados **PostgreSQL** e análise estruturada de dados financeiros.

O objetivo do projeto é oferecer ao usuário uma ferramenta capaz de centralizar suas informações financeiras, analisar seu comportamento de consumo, identificar padrões de gastos, acompanhar receitas e despesas e fornecer informações relevantes para apoiar decisões financeiras.

Além do controle financeiro pessoal, o sistema contará com uma base de conhecimento especializada em investimentos, permitindo que o assistente explique diferentes produtos financeiros e apresente alternativas compatíveis com o perfil, objetivos e tolerância a risco do usuário.

A IA não deverá tomar decisões ou executar investimentos automaticamente. Seu papel será **analisar, explicar, comparar, alertar e auxiliar**, mantendo o usuário como responsável final pelas decisões financeiras.

---

# 2. Problema

Muitas pessoas possuem informações financeiras espalhadas entre aplicativos bancários, planilhas, faturas de cartão e anotações pessoais.

Mesmo quando conseguem visualizar suas movimentações, frequentemente encontram dificuldades para responder perguntas como:

* Quanto estou gastando por mês?
* Quais categorias consomem mais dinheiro?
* Meu padrão de gastos está aumentando?
* Quanto consigo economizar mensalmente?
* Estou gastando mais do que deveria com determinada categoria?
* Minha reserva financeira está crescendo?
* Quanto da minha renda está comprometido?
* Qual seria o impacto de determinada compra?
* Quanto posso investir sem comprometer despesas importantes?
* Quais tipos de investimentos existem?
* Qual investimento possui características compatíveis com meus objetivos?
* Qual a diferença entre renda fixa e renda variável?

O FinAssist AI pretende reunir essas informações em uma única plataforma e permitir que o usuário converse com seus próprios dados financeiros utilizando linguagem natural.

---

# 3. Proposta de Valor

O sistema funcionará como um **copiloto financeiro pessoal**.

Em vez de apenas mostrar tabelas e gráficos, a aplicação deverá ser capaz de interpretar os dados e responder perguntas contextualizadas.

Exemplo:

> Usuário:
> "Onde estou gastando mais dinheiro este mês?"

A aplicação deverá consultar o banco de dados, calcular os gastos por categoria e entregar algo semelhante a:

> "Neste mês seus maiores gastos foram:
>
> Alimentação: R$ 820
> Transporte: R$ 540
> Lazer: R$ 430
>
> Alimentação representa aproximadamente 27% das suas despesas no período."

Outro exemplo:

> Usuário:
> "Se eu comprar um celular de R$ 3.000, isso pode comprometer minhas finanças?"

Nesse caso, a aplicação poderá analisar:

* saldo atual;
* renda média;
* despesas recorrentes;
* orçamento;
* reserva financeira;
* comprometimento da renda.

A resposta da IA será construída a partir desses dados.

---

# 4. Princípio Central da Arquitetura

O sistema utilizará **duas fontes diferentes de conhecimento**.

## Dados estruturados

Informações como:

* transações;
* salários;
* despesas;
* contas;
* cartões;
* categorias;
* orçamento;
* metas financeiras;
* perfil do investidor.

Essas informações ficarão armazenadas no **PostgreSQL**.

A IA não deverá calcular valores diretamente.

Os cálculos serão realizados por funções Python e consultas SQL.

---

## Conhecimento financeiro

Informações como:

* funcionamento de investimentos;
* conceitos financeiros;
* características de produtos;
* riscos;
* liquidez;
* tributação;
* educação financeira;
* diversificação;
* inflação;
* juros;
* renda fixa;
* renda variável.

Essas informações serão armazenadas na base de conhecimento utilizada pelo **RAG**.

---

O objetivo final é desenvolver um **assistente financeiro inteligente, explicável, contextualizado e orientado por dados**, capaz de ajudar o usuário a compreender melhor sua própria situação financeira e tomar decisões de forma mais informada.

---

# 5. Conversa com dados via Ollama

O endpoint `POST /users/{user_id}/chat` usa tool calling para permitir que o
modelo consulte as funções financeiras da aplicação sem receber acesso direto ao
PostgreSQL.

Fluxo da requisição:

1. A API envia ao Ollama a pergunta e os esquemas das ferramentas disponíveis.
2. O modelo escolhe uma ferramenta e devolve seu nome e argumentos estruturados.
3. O backend valida o nome em uma lista permitida, injeta o `user_id` da rota e
   executa a função Python correspondente.
4. A função consulta o PostgreSQL e seu resultado é devolvido ao modelo como uma
   mensagem com papel `tool`.
5. O Ollama produz a resposta final em linguagem natural.

Exemplo:

```powershell
uvicorn app.main:app --reload

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/users/1/chat `
  -ContentType application/json `
  -Body '{"message":"Em qual categoria gastei mais em setembro de 2026?"}'
```

Configurações disponíveis no ambiente:

```text
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/finnassist_db
OLLAMA_MODEL=qwen3:4b
```

O `user_id` na URL é apenas uma etapa inicial. Antes de disponibilizar a API a
usuários reais, ele deve ser obtido de uma autenticação confiável (por exemplo,
um token) em vez de ser aceito livremente na rota.
