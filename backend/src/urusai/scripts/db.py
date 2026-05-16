"""Database admin commands: connectivity, init, rebuild, clear.

Subcommands:
  status   : Connect to Postgres + Milvus and print version / table / collection counts.
  init     : Verify connectivity. (Postgres database is provisioned by docker-compose
             POSTGRES_DB env var; Postgres schema migrations are applied via alembic.)
  rebuild  : Drop all Postgres tables + Milvus collections.
  clear    : Truncate all Postgres tables, preserve schema. Milvus collections are
             left in place; use `rebuild` to drop them.
"""
from __future__ import annotations

import argparse
import sys

from urusai.config.settings import get_settings


def _connect_pg(timeout: float = 5.0):
    import psycopg

    settings = get_settings()
    return psycopg.connect(
        host=settings.pg_host,
        port=settings.pg_port,
        user=settings.pg_user,
        password=settings.pg_password,
        dbname=settings.pg_database,
        connect_timeout=int(timeout),
    )


def _connect_milvus():
    from pymilvus import MilvusClient

    settings = get_settings()
    kwargs: dict = {"uri": settings.milvus_uri}
    if settings.milvus_token:
        kwargs["token"] = settings.milvus_token
    return MilvusClient(**kwargs)


def _section(label: str) -> None:
    print()
    print(f"--- {label} ---")


def cmd_status() -> int:
    settings = get_settings()
    print("=== urusai db status ===")

    ok = True

    _section(f"Postgres  {settings.pg_host}:{settings.pg_port}/{settings.pg_database}")
    try:
        with _connect_pg() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                row = cur.fetchone()
                version_line = (row[0] if row else "").split(",")[0]
                cur.execute(
                    "SELECT count(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
                row = cur.fetchone()
                table_count = row[0] if row else 0
        print(f"  OK   {version_line}")
        print(f"  tables (public schema): {table_count}")
    except Exception as exc:
        print(f"  FAILED  {type(exc).__name__}: {exc}")
        ok = False

    _section(f"Milvus    {settings.milvus_uri}")
    try:
        client = _connect_milvus()
        try:
            collections = client.list_collections()
            print(f"  OK   connected")
            print(f"  collections: {len(collections)} {collections if collections else ''}")
        finally:
            client.close()
    except Exception as exc:
        print(f"  FAILED  {type(exc).__name__}: {exc}")
        ok = False

    return 0 if ok else 1


def cmd_init() -> int:
    """Verify Postgres + Milvus connectivity.

    The Postgres database is provisioned by the docker-compose POSTGRES_DB
    env var; Postgres schema migrations are applied via `alembic upgrade head`.
    """
    print("=== urusai db init ===")
    rc = cmd_status()
    print()
    if rc == 0:
        print("Connection OK. Run `alembic upgrade head` to apply Postgres schema migrations.")
    return rc


def cmd_rebuild() -> int:
    """Drop all Postgres tables + Milvus collections."""
    settings = get_settings()
    print("=== urusai db rebuild (drop) ===")
    ok = True

    _section(f"Postgres  {settings.pg_host}:{settings.pg_port}/{settings.pg_database}")
    try:
        with _connect_pg() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
                tables = [r[0] for r in cur.fetchall()]
                for t in tables:
                    cur.execute(f'DROP TABLE IF EXISTS "{t}" CASCADE')
                    print(f"  dropped table: {t}")
                if not tables:
                    print("  no tables to drop")
            conn.commit()
    except Exception as exc:
        print(f"  FAILED  {type(exc).__name__}: {exc}")
        ok = False

    _section(f"Milvus    {settings.milvus_uri}")
    try:
        client = _connect_milvus()
        try:
            collections = client.list_collections()
            for c in collections:
                client.drop_collection(c)
                print(f"  dropped collection: {c}")
            if not collections:
                print("  no collections to drop")
        finally:
            client.close()
    except Exception as exc:
        print(f"  FAILED  {type(exc).__name__}: {exc}")
        ok = False

    print()
    print("All tables and collections dropped. Run `alembic upgrade head` to re-create Postgres schema.")
    return 0 if ok else 1


def cmd_clear() -> int:
    """Truncate all Postgres tables, preserving schema. Milvus collections are left in place."""
    settings = get_settings()
    print("=== urusai db clear (truncate) ===")
    ok = True

    _section(f"Postgres  {settings.pg_host}:{settings.pg_port}/{settings.pg_database}")
    try:
        with _connect_pg() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
                tables = [r[0] for r in cur.fetchall()]
                if tables:
                    quoted = ", ".join(f'"{t}"' for t in tables)
                    cur.execute(f"TRUNCATE {quoted} RESTART IDENTITY CASCADE")
                    print(f"  truncated {len(tables)} tables: {tables}")
                else:
                    print("  no tables to truncate")
            conn.commit()
    except Exception as exc:
        print(f"  FAILED  {type(exc).__name__}: {exc}")
        ok = False

    _section(f"Milvus    {settings.milvus_uri}")
    try:
        client = _connect_milvus()
        try:
            collections = client.list_collections()
            if collections:
                print(f"  {len(collections)} collections preserved (use db-rebuild to drop)")
            else:
                print("  no collections")
        finally:
            client.close()
    except Exception as exc:
        print(f"  FAILED  {type(exc).__name__}: {exc}")
        ok = False

    return 0 if ok else 1


_CMDS = {
    "status": cmd_status,
    "init": cmd_init,
    "rebuild": cmd_rebuild,
    "clear": cmd_clear,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="urusai.scripts.db")
    parser.add_argument("cmd", choices=list(_CMDS.keys()))
    args = parser.parse_args(argv)
    return _CMDS[args.cmd]()


if __name__ == "__main__":
    sys.exit(main())
