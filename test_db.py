from sqlalchemy import text
from app.database import engine

try:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT version();")
        )

        print(result.fetchone())

        print("Conexão realizada com sucesso!")

except Exception as error:
    print("erro ao conectar")
    print(error)


from app.services.financial_service import (
    get_total_income,
    get_total_expenses
)

income = get_total_income(1)
expenses = get_total_expenses(1)

print("Ganhos", income)
print("Gastos", expenses)