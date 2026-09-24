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
OLLAMA_EMBEDDING_MODEL=embeddinggemma
```

O `user_id` na URL é apenas uma etapa inicial. Antes de disponibilizar a API a
usuários reais, ele deve ser obtido de uma autenticação confiável (por exemplo,
um token) em vez de ser aceito livremente na rota.

---

# 6. MVP de RAG

O MVP usa somente `knowledge/tesouro_selic.md` e
`knowledge/reserva_emergencia.md`. O modelo `embeddinggemma` deve produzir
vetores de 768 dimensões. A aplicação valida essa dimensão antes de gravar ou
consultar o PostgreSQL.

## Preparação manual do PostgreSQL

O projeto não executa migrations automaticamente. Abra sua ferramenta de banco
(por exemplo, pgAdmin ou `psql`) e execute, na ordem:

```text
database/migrations/001_create_knowledge_base.sql
database/migrations/002_add_documents_source_unique.sql
```

A segunda migration também corrige bancos onde `documents` já existia sem uma
restrição de unicidade em `source`, necessária para a ingestão idempotente.

Depois, confirme que o Ollama está ativo e que os modelos estão instalados:

```powershell
ollama pull embeddinggemma
ollama pull qwen3:4b
```

## Ingestão mínima

Na raiz do repositório, com o ambiente virtual ativado:

```powershell
python -m scripts.ingest_knowledge
```

O script é idempotente por `source`: atualiza os dois documentos, remove seus
chunks antigos e insere os novos dentro de uma única transação por documento.
O Markdown completo também é mantido em `documents.content`, enquanto os trechos
usados na recuperação ficam em `document_chunks`.
Ele não ingere automaticamente outros arquivos.

Confira manualmente no banco:

```sql
SELECT id, title, source
FROM documents
ORDER BY id;

SELECT
    document_id,
    chunk_index,
    LEFT(content, 100) AS content_preview,
    vector_dims(embedding) AS embedding_dimensions
FROM document_chunks
ORDER BY document_id, chunk_index;
```

Todos os valores de `embedding_dimensions` devem ser `768`.

## Teste da recuperação sem IA conversacional

Execute uma pergunta por vez:

```powershell
python -m scripts.search_knowledge "Para que serve o Tesouro Selic?"
python -m scripts.search_knowledge "Onde deixar dinheiro para emergências?"
python -m scripts.search_knowledge "Renda variável é indicada para reserva?"
```

O mesmo teste está disponível por HTTP, sem chamar o Qwen:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/knowledge/search?query=Para%20que%20serve%20o%20Tesouro%20Selic%3F&limit=5"
```

Confira título, fonte, conteúdo e similaridade dos cinco primeiros resultados.
Se os chunks esperados não aparecerem, ajuste os documentos, a divisão feita em
`scripts/ingest_knowledge.py`, o modelo de embedding ou o limite, e faça a
ingestão novamente antes de alterar o prompt do Qwen.

## RAG como ferramenta do agente

`search_financial_knowledge` faz parte do mesmo catálogo das ferramentas de
dados pessoais. Seu retorno contém `title`, `source`, `content` e `similarity`.
O prompt obriga o agente a usar somente os chunks recuperados para conhecimento
financeiro, informar quando a base for insuficiente e citar as fontes.

Testes manuais combinados:

```powershell
$questions = @(
  "Quanto gastei neste mês?",
  "O que é CDB?",
  "Considerando minha média mensal de despesas, como devo pensar minha reserva de emergência?"
)

foreach ($question in $questions) {
  Invoke-RestMethod `
    -Method Post `
    -Uri http://127.0.0.1:8000/users/1/chat `
    -ContentType application/json `
    -Body (@{ message = $question } | ConvertTo-Json)
}
```

Resultados esperados: a primeira pergunta usa somente uma ferramenta financeira;
a segunda usa somente `search_financial_knowledge`; a terceira combina
`get_monthly_average` (ou o resumo financeiro) com a busca RAG. Os nomes das
tools escolhidas aparecem no log do servidor como `FinnAssist tool selecionada`.

---

# 7. MVP utilizável

Ao iniciar a API, a interface web fica disponível em:

```text
http://127.0.0.1:8000/
```

Ela reúne quatro áreas:

- **Visão geral:** receitas, despesas, saldo, média mensal, distribuição por
  categoria e últimas movimentações;
- **Movimentações:** cadastro, edição, exclusão e filtro mensal;
- **Categorias:** cadastro e edição de categorias de receita ou despesa;
- **Assistente:** chat com perguntas sugeridas sobre dados pessoais e a base RAG.

A verificação simples da API foi movida para `GET /health`, e a documentação
interativa continua disponível em `GET /docs`.

## API de categorias

```text
GET    /categories
GET    /categories/{category_id}
POST   /categories
PATCH  /categories/{category_id}
DELETE /categories/{category_id}
```

Exemplo de cadastro:

```json
{
  "name": "Moradia",
  "type": "EXPENSE"
}
```

Uma categoria usada por alguma transação não pode ser excluída. Seu tipo também
não pode ser alterado quando isso tornaria incompatíveis as transações existentes.

## API de movimentações

```text
GET    /users/{user_id}/transactions
GET    /users/{user_id}/transactions/{transaction_id}
POST   /users/{user_id}/transactions
PATCH  /users/{user_id}/transactions/{transaction_id}
DELETE /users/{user_id}/transactions/{transaction_id}
```

A listagem aceita `start_date`, `end_date`, `category_id`, `type`, `limit` e
`offset`. Valores devem ser positivos, e o tipo da categoria precisa coincidir
com o tipo da movimentação.

Exemplo de despesa:

```json
{
  "category_id": 1,
  "description": "Supermercado",
  "amount": "125.90",
  "type": "EXPENSE",
  "transaction_date": "2026-09-24"
}
```

## Tool mensal

`get_monthly_expenses` responde especificamente perguntas como “Quanto gastei
neste mês?”. Isso evita confundir o total mensal com `get_total_expenses`, que
representa o histórico inteiro.

## Controles do Ollama

```text
OLLAMA_TIMEOUT_SECONDS=180
OLLAMA_KEEP_ALIVE=10m
OLLAMA_NUM_PREDICT=400
```

O agente executa no máximo quatro rodadas de tools, usa temperatura zero, limita
o tamanho da resposta e mantém o modelo carregado entre chamadas. O timeout
evita que uma requisição fique aberta indefinidamente. O desempenho final ainda
depende do hardware e de o Ollama conseguir usar aceleração disponível.
