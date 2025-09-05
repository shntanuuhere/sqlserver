"""
Simple Python smoke-test for a local SQL Server instance.

This script attempts to connect, run a few basic queries and a temp-table CRUD test.

Usage examples (PowerShell):
  # using Windows Authentication (trusted connection)
  python .\test_sql_server.py --trusted

  # using SQL authentication
  python .\test_sql_server.py --server localhost --uid sa --pwd YourPasswordHere

You can also set environment variables: MSSQL_SERVER, MSSQL_DATABASE, MSSQL_UID, MSSQL_PWD, MSSQL_DRIVER

Exit codes:
  0 - all checks passed
  1 - connection error
  2 - missing credentials when required
  3 - test/assertion failure

"""
from __future__ import annotations

import argparse
import os
import sys
import traceback

try:
    import pyodbc
except Exception:
    pyodbc = None


def build_conn_string(args: argparse.Namespace) -> str:
    driver = args.driver or os.getenv("MSSQL_DRIVER", "ODBC Driver 17 for SQL Server")
    server = args.server or os.getenv("MSSQL_SERVER", "localhost")
    database = args.database or os.getenv("MSSQL_DATABASE", "master")
    trusted = args.trusted or os.getenv("MSSQL_TRUSTED", "false").lower() in ("1", "true", "yes")

    if trusted:
        return f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes"

    uid = args.uid or os.getenv("MSSQL_UID")
    pwd = args.pwd or os.getenv("MSSQL_PWD")
    if not uid or not pwd:
        raise RuntimeError("No credentials provided. Provide --uid/--pwd or use --trusted for Windows Authentication.")

    return f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={uid};PWD={pwd};TrustServerCertificate=yes"


def run_basic_checks(conn: pyodbc.Connection) -> None:
    cur = conn.cursor()

    # Version
    cur.execute("SELECT @@VERSION")
    row = cur.fetchone()
    print("Server version:", row[0])

    # Current DB
    cur.execute("SELECT DB_NAME()")
    print("Connected database:", cur.fetchone()[0])

    # Temp table CRUD
    cur.execute("CREATE TABLE #tmp_test (id INT PRIMARY KEY, val NVARCHAR(100))")
    cur.execute("INSERT INTO #tmp_test (id, val) VALUES (1, ?)", ("hello",))
    cur.execute("SELECT val FROM #tmp_test WHERE id=1")
    val = cur.fetchone()[0]
    if val != "hello":
        raise AssertionError("Temp table returned unexpected value: %r" % (val,))
    cur.execute("DROP TABLE #tmp_test")

    print("Basic CRUD checks passed.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SQL Server smoke-test")
    parser.add_argument("--server", help="SQL Server host (default: localhost)")
    parser.add_argument("--database", help="Database to use (default: master)")
    parser.add_argument("--driver", help="ODBC driver name (default: ODBC Driver 17 for SQL Server)")
    parser.add_argument("--uid", help="SQL username (use with --pwd)")
    parser.add_argument("--pwd", help="SQL password (use with --uid)")
    parser.add_argument("--trusted", action="store_true", help="Use Windows Authentication (Trusted Connection)")
    parser.add_argument("--timeout", type=int, default=5, help="Connection timeout seconds")
    args = parser.parse_args(argv)

    if pyodbc is None:
        print("pyodbc is not installed. Install from requirements.txt: python -m pip install -r requirements.txt", file=sys.stderr)
        return 4

    try:
        conn_str = build_conn_string(args)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 2

    print("Using connection string (masked):", _mask_conn_str(conn_str))

    try:
        conn = pyodbc.connect(conn_str, timeout=args.timeout)
    except Exception as e:
        print("Connection failed:", e, file=sys.stderr)
        traceback.print_exc()
        return 1

    try:
        run_basic_checks(conn)
    except Exception as e:
        print("Test failed:", e, file=sys.stderr)
        traceback.print_exc()
        return 3
    finally:
        try:
            conn.close()
        except Exception:
            pass

    print("All checks passed.")
    return 0


def _mask_conn_str(s: str) -> str:
    # mask PWD if present
    parts = s.split(";")
    masked = []
    for p in parts:
        if p.upper().startswith("PWD="):
            masked.append("PWD=****")
        else:
            masked.append(p)
    return ";".join(masked)


if __name__ == '__main__':
    raise SystemExit(main())
