# SQL Server smoke-test script

This repository contains a small Python script, `test_sql_server.py`, that attempts to connect to a local SQL Server instance and run a few basic checks (version query and a temporary-table CRUD test).

Prerequisites

- Python 3.7+ installed on your machine.
- An ODBC driver for SQL Server installed (e.g. "ODBC Driver 17 for SQL Server" or newer). On Windows, install from Microsoft: https://learn.microsoft.com/sql/connect/odbc/windows/microsoft-odbc-driver-for-sql-server
- If using SQL authentication, know the username and password. For Windows Authentication, run with `--trusted`.

Install dependencies

PowerShell:

```powershell
python -m pip install --upgrade pip; 
python -m pip install -r .\requirements.txt
```

Examples

Trusted (Windows) authentication:

```powershell
python .\test_sql_server.py --trusted
```

SQL authentication:

```powershell
python .\test_sql_server.py --server localhost --uid sa --pwd YourPasswordHere
```

You can also set environment variables instead of passing args:

- `MSSQL_SERVER` - host
- `MSSQL_DATABASE` - database
- `MSSQL_UID` - username
- `MSSQL_PWD` - password
- `MSSQL_DRIVER` - ODBC driver name

Notes

- The script prints a masked connection string before connecting.
- Exit codes: 0 (success), 1 (connection failed), 2 (missing credentials), 3 (test failure), 4 (pyodbc missing).

If you want, I can also add a small PowerShell wrapper or a GitHub Actions workflow to run this automatically.
