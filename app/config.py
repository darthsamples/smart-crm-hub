import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient

load_dotenv()

class Settings:
    KEY_VAULT_URL: str = os.getenv("KEY_VAULT_URL", "")
    DB_HOST: str = os.getenv("DB_HOST", "")
    DB_PORT: int = int(os.getenv("DB_PORT", 1433))
    DB_NAME: str = os.getenv("DB_NAME", "")
    
    @property
    def db_user(self) -> str:
        credential = ClientSecretCredential(
            tenant_id=os.getenv("AZURE_TENANT_ID", ""),
            client_id=os.getenv("AZURE_CLIENT_ID", ""),
            client_secret=os.getenv("AZURE_CLIENT_SECRET", "")
        )
        secret_client = SecretClient(vault_url=self.KEY_VAULT_URL, credential=credential)
        return secret_client.get_secret("sqluseradmin").value

    @property
    def db_password(self) -> str:
        credential = ClientSecretCredential(
            tenant_id=os.getenv("AZURE_TENANT_ID", ""),
            client_id=os.getenv("AZURE_CLIENT_ID", ""),
            client_secret=os.getenv("AZURE_CLIENT_SECRET", "")
        )
        secret_client = SecretClient(vault_url=self.KEY_VAULT_URL, credential=credential)
        return secret_client.get_secret("sqlpassword").value
    
    # customers.py queries
    GET_ALL_CUSTOMERS = "SELECT c.[CustomerID], p.[FirstName], p.[LastName], ea.[EmailAddress], ISNULL(c.[LeadStatus],'') AS LeadStatus FROM [Person].[Person] p INNER JOIN [Sales].[Customer] c ON c.[PersonID] = p.[BusinessEntityID] LEFT OUTER JOIN [Person].[EmailAddress] ea ON ea.[BusinessEntityID] = p.[BusinessEntityID] WHERE c.StoreID IS NULL AND c.[CustomerID] IN (12632, 13581, 14429, 15691, 27842, 22435, 27748, 21113)"
    GET_CUSTOMER_BY_ID = "SELECT c.[CustomerID], p.[FirstName], p.[LastName], ea.[EmailAddress], ISNULL(c.[LeadStatus],'') AS LeadStatus FROM [Person].[Person] p INNER JOIN [Sales].[Customer] c ON c.[PersonID] = p.[BusinessEntityID] LEFT OUTER JOIN [Person].[EmailAddress] ea ON ea.[BusinessEntityID] = p.[BusinessEntityID] WHERE c.[CustomerID] = ?"
    UPDATE_LeadStatus = "UPDATE Sales.Customer SET LeadStatus = ? WHERE CustomerID = ?"

    # orders.py queries
    GET_ALL_ORDERS = "SELECT SalesOrderID, CustomerID, OrderDate, TotalDue FROM Sales.SalesOrderHeader WHERE CustomerID IN (12632, 13581, 14429, 15691, 27842, 22435, 27748, 21113)"
    GET_ORDERS_BY_CUSTOMERID = "SELECT SalesOrderID, CustomerID, OrderDate, TotalDue FROM Sales.SalesOrderHeader WHERE CustomerID = ?"

    # tasks.py queries
    GET_ALL_TASKS = "SELECT TaskID, CustomerID, TaskDescription, AssignedTo, DueDate FROM Sales.LeadTasks"
    GET_TASK_BY_ID = "SELECT TaskID, CustomerID, TaskDescription, AssignedTo, DueDate FROM Sales.LeadTasks WHERE TaskID = ?"
    CREATE_TASK = "INSERT INTO Sales.LeadTasks (CustomerID, TaskDescription, AssignedTo, DueDate) VALUES (?, ?, ?, ?)"
    UPDATE_TASK = "UPDATE Sales.LeadTasks SET CustomerID = ?, TaskDescription = ?, AssignedTo = ?, DueDate = ? WHERE TaskID = ?"
    DELETE_TASK = "DELETE FROM Sales.LeadTasks WHERE TaskID = ?"

    # reports.py
    LEAD_QUERY = "SELECT COUNT(*) FROM Sales.Customer WHERE LeadStatus = 'High Priority'"
    TASK_QUERY = "SELECT COUNT(*) FROM Sales.LeadTasks"

settings = Settings()
