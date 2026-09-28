"""Roda bronze + dbt build (modelos, testes de dados e testes unitários) em dados sintéticos."""
import json
import os
import subprocess
import sys

import duckdb
import pytest

from pipeline import bronze
from pipeline.config import DBT_DIR, tabela_do_arquivo
from tests.sintetico import gerar


@pytest.fixture(scope="module")
def warehouse(tmp_path_factory):
    raiz = tmp_path_factory.mktemp("radar")
    raw, bronze_dir, tmp = raiz / "raw", raiz / "bronze", raiz / "tmp"
    gerar(raw, n_empresas=300)

    bronze.TMP_DIR = tmp
    for zip_path in raw.glob("*.zip"):
        tabela, parte = tabela_do_arquivo(zip_path.name)
        bronze.zip_para_parquet(zip_path, tabela, parte, "2026-09", bronze_dir)

    env = {
        **os.environ,
        "RADAR_DATA_DIR": raiz.as_posix(),
        "RADAR_DUCKDB": (raiz / "radar.duckdb").as_posix(),
        "RADAR_TMP_DIR": tmp.as_posix(),
        "RADAR_MEMORY_LIMIT": "1GB",
    }
    resultado = subprocess.run(
        [
            sys.executable, "-c", "from dbt.cli.main import cli; cli()", "build",
            "--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR),
            "--target-path", str(raiz / "target"), "--log-path", str(raiz / "logs"),
            "--vars", json.dumps({"referencia": "2026-09", "min_estabelecimentos": 1}),
        ],
        env=env, capture_output=True, text=True, encoding="utf-8", check=False,
    )
    assert resultado.returncode == 0, resultado.stdout[-4000:]
    return raiz / "radar.duckdb"


def test_dbt_build_passa(warehouse):
    assert warehouse.exists()


def test_gold_tem_dados_e_cnpj_alfanumerico(warehouse):
    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        aberturas = con.sql("select sum(aberturas) from gold_aberturas_fechamentos").fetchone()[0]
        assert aberturas > 0
        alfa = con.sql("select sum(cnpjs_alfanumericos) from gold_retrato_uf").fetchone()[0]
        assert alfa == 1
        # Motivo 54 (baixa simplificada ME/EPP) precisa ser classificado como voluntário.
        tipo = con.sql("select tipo_baixa from stg_motivos where motivo = '54'").fetchone()[0]
        assert tipo == "Voluntária"
        # CNPJ de campanha eleitoral fica fora das métricas de empresas e vai para tabela própria.
        campanhas = con.sql(
            "select sum(cnpjs_abertos), sum(baixados_em_31_dez) from gold_campanhas_eleitorais"
        ).fetchone()
        assert campanhas == (1, 1)
        total = con.sql("select count(*) from int_empresas where data_inicio_atividade >= '2010-01-01'")
        assert aberturas == total.fetchone()[0] - 1
    finally:
        con.close()
