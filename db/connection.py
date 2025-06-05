from langchain_community.utilities import SQLDatabase

def connect_to_db(
    dbms: str,
    db_name: str = "",
    host: str = "",
    port: str = "",
    user: str = "",
    password: str = "",
) -> SQLDatabase:
    '''
        Connect to database

        Args: 
            dbms (str): Database Management System
            db_name (str): Name of the database
            host (str): Host of the database
            port (str): Databse port
            user (str): Username
            password (str): Password

        Return LangChain SQLDatabase
    '''

    dbms = dbms.lower()
    if dbms == "mysql":
        return SQLDatabase.from_uri(
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
        )
    elif dbms == "sqlite":
        return SQLDatabase.from_uri(
            f"sqlite:///{db_name}"
        )
    elif dbms == "postgressql":
        return SQLDatabase.from_uri(
            f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"
        )


        