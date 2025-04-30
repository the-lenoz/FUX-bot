import io
from os import getenv

import pandas as pd
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, MetaData, Table


load_dotenv(find_dotenv("../.env"))
database: str = getenv("POSTGRES_DB")
username: str = getenv("POSTGRES_USER", "docker")
password: str = getenv("POSTGRES_PASSWORD", None)
port: int = getenv("POSTGRES_PORT", 5065)
host: str = getenv("POSTGRES_HOST", "")
def export_table_to_memory(table_name: str):
    """
    Подключается к PostgreSQL, выгружает данные из указанной таблицы
    и сохраняет результат в Excel-файл (в памяти, как объект BytesIO).

    :param db_url:     Строка подключения к базе (например, "postgresql://user:password@host:port/dbname").
    :param table_name: Название таблицы в БД, которую нужно выгрузить.
    :return:           Объект BytesIO, содержащий Excel-файл.
    """
    # Создаём engine и MetaData
    try:
        db_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        engine = create_engine(db_url)
        metadata = MetaData()

        # Отражаем структуру таблицы (reflection)
        table = Table(table_name, metadata, autoload_with=engine)

        # Выполняем SELECT * из таблицы и формируем DataFrame
        with engine.connect() as conn:
            result = conn.execute(table.select())
            df = pd.DataFrame(result.fetchall(), columns=list(result.keys()))

        # Создаём BytesIO-объект и сохраняем туда Excel-файл
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        # Перемещаем курсор в начало потока, чтобы файл можно было считывать с самого начала
        output.seek(0)
        return output.read()
    except Exception as e:
        print(e)
        return "Error"


# if __name__ == "__main__":
#     # Параметры для подключения к базе данных
#
#     # Формируем строку подключения
#
#     # Пример вызова функции для таблицы "users"
#     table_name = "users"  # замените на нужную вам таблицу
#
#     excel_in_memory = export_table_to_memory(table_name)
#
#     # Теперь excel_in_memory содержит Excel-файл в виде байтов.
#     # Вы можете, например, сохранить его на диск (если нужно) или передать куда-то дальше:
#     # Пример сохранения в файл:
#     with open("users_data.xlsx", "wb") as f:
#         f.write(excel_in_memory.getbuffer())
#
#     print("Excel-файл успешно сформирован в памяти и сохранён в 'users_data.xlsx'.")
