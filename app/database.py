import pyodbc
from contextlib import contextmanager
from app.config import settings

@contextmanager
def get_db_connection():
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={settings.DB_HOST};"
        f"DATABASE={settings.DB_NAME};"
        f"UID={settings.db_user};"
        f"PWD={settings.db_password};"
        f"PORT={settings.DB_PORT}"
    )
    conn = pyodbc.connect(conn_str)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def execute_query(query, params=None, as_dict=True):
    """
    Execute a SELECT query and return results.
    
    Args:
        query: SQL query string
        params: Query parameters
        as_dict: If True, return results as list of dictionaries
    
    Returns:
        List of dictionaries (if as_dict=True) or list of pyodbc.Row objects
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            
            if as_dict:
                # Get column names
                columns = [column[0] for column in cursor.description]
                # Convert rows to dictionaries
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            else:
                return cursor.fetchall()

def execute_command(query, params=None):
    """
    Execute an INSERT, UPDATE, or DELETE command.
    Returns the number of affected rows.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            affected_rows = cursor.rowcount
            conn.commit()
            return affected_rows

def execute_scalar(query, params=None):
    """
    Execute a query that returns a single value.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            result = cursor.fetchone()
            return result[0] if result else None
        
def execute_insert_get_id(query, params=None):
    """
    Execute an INSERT command and return the ID of the newly created record.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            # Use SELECT SCOPE_IDENTITY() for SQL Server with pyodbc
            cursor.execute("SELECT @@IDENTITY")
            result = cursor.fetchone()
            last_id = int(result[0]) if result and result[0] is not None else None
            conn.commit()
            return last_id