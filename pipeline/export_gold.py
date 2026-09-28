"""Publica a camada gold: CSVs versionados no repositório + um DuckDB pequeno para o dashboard."""
from __future__ import annotations

import logging

import duckdb

from pipeline.config import DASHBOARD_GOLD_DB, DUCKDB_PATH, GOLD_DIR

log = logging.getLogger(__name__)


def exportar(referencia: str, amostra: bool) -> None:
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    DASHBOARD_GOLD_DB.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_GOLD_DB.unlink(missing_ok=True)

    con = duckdb.connect()
    try:
        con.execute(f"ATTACH '{DUCKDB_PATH.as_posix()}' AS radar (READ_ONLY)")
        con.execute(f"ATTACH '{DASHBOARD_GOLD_DB.as_posix()}' AS painel")
        tabelas = [r[0] for r in con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_catalog = 'radar' AND table_name LIKE 'gold_%' ORDER BY 1"
        ).fetchall()]
        if not tabelas:
            raise RuntimeError("Nenhuma tabela gold_* encontrada. O dbt rodou?")

        for t in tabelas:
            csv = (GOLD_DIR / f"{t}.csv").as_posix()
            con.execute(f"COPY radar.main.{t} TO '{csv}' (HEADER, DELIMITER ',')")
            con.execute(f"CREATE TABLE painel.main.{t} AS SELECT * FROM radar.main.{t}")
            n = con.execute(f"SELECT count(*) FROM radar.main.{t}").fetchone()[0]
            log.info("gold: %s (%s linhas)", t, n)
        con.execute("DETACH painel")
    finally:
        con.close()

    # Amostra nunca conta como publicada: a próxima execução completa não é pulada.
    marca = f"{referencia}-amostra" if amostra else referencia
    (GOLD_DIR / "_referencia.txt").write_text(marca + "\n", encoding="utf-8")


def referencia_publicada() -> str | None:
    arq = GOLD_DIR / "_referencia.txt"
    return arq.read_text(encoding="utf-8").strip() if arq.exists() else None
