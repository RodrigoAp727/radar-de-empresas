"""Camada bronze: zip da Receita -> Parquet, sem transformar nenhum valor.

Tudo entra como texto. Tipos, datas e regras de negócio ficam para o dbt
(camada silver), onde são testados.
"""
from __future__ import annotations

import logging
import zipfile
from pathlib import Path

import duckdb

from pipeline.config import LAYOUTS, TMP_DIR

log = logging.getLogger(__name__)


def _sql_str(valor: str | Path) -> str:
    return "'" + str(valor).replace("\\", "/").replace("'", "''") + "'"


def _extrair_como_utf8(zip_path: Path, csv_path: Path, bloco: int = 16 * 1024 * 1024) -> None:
    """Descompacta em streaming convertendo latin-1 -> UTF-8.

    O leitor latin-1 do DuckDB recusa alguns bytes presentes nos arquivos da Receita.
    Em Python, latin-1 decodifica qualquer byte, então a conversão nunca falha.
    """
    with zipfile.ZipFile(zip_path) as zf:
        membro = zf.namelist()[0]  # cada zip da Receita tem um único arquivo
        with zf.open(membro) as origem, open(csv_path, "wb") as destino:
            while dados := origem.read(bloco):
                destino.write(dados.decode("latin-1").encode("utf-8"))


def destino_parquet(bronze_dir: Path, tabela: str, parte: int) -> Path:
    return bronze_dir / tabela / f"{tabela}_{parte}.parquet"


def zip_para_parquet(
    zip_path: Path, tabela: str, parte: int, referencia: str, bronze_dir: Path
) -> dict[str, int]:
    """Extrai o CSV do zip, converte para Parquet e apaga o CSV. Retorna linhas lidas e rejeitadas."""
    colunas = LAYOUTS[tabela]
    destino = destino_parquet(bronze_dir, tabela, parte)
    parcial = destino.with_suffix(".parquet.tmp")
    destino.parent.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = TMP_DIR / f"{tabela}_{parte}.csv"
    _extrair_como_utf8(zip_path, csv_path)

    colunas_sql = "{" + ", ".join(f"'{c}': 'VARCHAR'" for c in colunas) + "}"
    con = duckdb.connect()
    try:
        con.execute(f"SET temp_directory = {_sql_str(TMP_DIR)}")
        linhas = con.execute(f"""
            COPY (
                SELECT *, {_sql_str(referencia)} AS _referencia, {_sql_str(zip_path.name)} AS _arquivo
                FROM read_csv(
                    {_sql_str(csv_path)},
                    delim = ';', quote = '"', escape = '"', header = false,
                    columns = {colunas_sql},
                    -- A Receita tem campos com quebra de linha entre aspas e linhas malformadas.
                    -- Linhas ilegíveis são descartadas, mas contadas (store_rejects).
                    ignore_errors = true, store_rejects = true
                )
            ) TO {_sql_str(parcial)} (FORMAT parquet, COMPRESSION zstd)
        """).fetchone()[0]
        rejeitadas = con.execute("SELECT count(DISTINCT line) FROM reject_errors").fetchone()[0]
        parcial.replace(destino)  # só aparece com o nome final se a conversão terminou
    finally:
        con.close()
        csv_path.unlink(missing_ok=True)

    fmt = lambda n: f"{n:,}".replace(",", ".")  # noqa: E731
    log.info("bronze/%s/%s: %s linhas", tabela, destino.name, fmt(linhas))
    if rejeitadas:
        log.warning("bronze/%s/%s: %s linhas rejeitadas", tabela, destino.name, fmt(rejeitadas))
    return {"linhas": linhas, "rejeitadas": rejeitadas}
