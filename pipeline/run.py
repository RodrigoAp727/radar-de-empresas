"""Orquestra o pipeline completo: download -> bronze -> dbt (silver/gold + testes) -> exportação.

Uso:
    python -m pipeline.run                  # última referência publicada pela Receita
    python -m pipeline.run --amostra        # só a parte 0 de cada arquivo (~1/10): bom para desenvolver
    python -m pipeline.run --pular-download # reaproveita a bronze já existente
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys

from pipeline import bronze, download, export_gold
from pipeline.config import (
    BRONZE_DIR,
    DATA_DIR,
    DBT_DIR,
    DUCKDB_PATH,
    PARTE_AMOSTRA,
    PARTICIONADAS,
    RAW_DIR,
    TABELAS_PADRAO,
    TMP_DIR,
    tabela_do_arquivo,
)

log = logging.getLogger("radar")


def _saida_actions(**valores: str) -> None:
    """Expõe valores para os próximos passos do GitHub Actions."""
    arquivo = os.environ.get("GITHUB_OUTPUT")
    if arquivo:
        with open(arquivo, "a", encoding="utf-8") as f:
            for k, v in valores.items():
                f.write(f"{k}={v}\n")


MANIFESTO = BRONZE_DIR / "_manifesto.json"


def _ler_manifesto() -> dict | None:
    return json.loads(MANIFESTO.read_text(encoding="utf-8")) if MANIFESTO.exists() else None


def etapa_bronze(referencia: str, tabelas: list[str], amostra: bool, manter_zips: bool) -> None:
    # Retoma uma carga interrompida da mesma referência; qualquer outra coisa recomeça do zero.
    manifesto = _ler_manifesto()
    if not manifesto or (manifesto["referencia"], manifesto["amostra"]) != (referencia, amostra):
        shutil.rmtree(BRONZE_DIR, ignore_errors=True)
        manifesto = {"referencia": referencia, "amostra": amostra, "completo": False, "arquivos": {}}
    manifesto["completo"] = False

    for nome_zip, tamanho in sorted(download.listar_zips(referencia).items()):
        info = tabela_do_arquivo(nome_zip)
        if not info or info[0] not in tabelas:
            continue
        tabela, parte = info
        if amostra and tabela in PARTICIONADAS and parte != PARTE_AMOSTRA:
            continue
        if nome_zip in manifesto["arquivos"] and bronze.destino_parquet(BRONZE_DIR, tabela, parte).exists():
            log.info("%s já convertido, pulando", nome_zip)
            continue
        # Um arquivo por vez: baixa, converte, apaga. Cabe no disco do runner do GitHub.
        zip_path = download.baixar(referencia, nome_zip, tamanho, RAW_DIR / referencia)
        manifesto["arquivos"][nome_zip] = bronze.zip_para_parquet(
            zip_path, tabela, parte, referencia, BRONZE_DIR
        )
        MANIFESTO.write_text(json.dumps(manifesto, indent=2), encoding="utf-8")
        if not manter_zips:
            zip_path.unlink()

    faltando = [t for t in tabelas if not (BRONZE_DIR / t).exists()]
    if faltando:
        raise RuntimeError(f"Tabelas sem arquivo na referência {referencia}: {faltando}")

    manifesto["completo"] = True
    MANIFESTO.write_text(json.dumps(manifesto, indent=2), encoding="utf-8")


def etapa_dbt(referencia: str, amostra: bool) -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        "RADAR_DATA_DIR": DATA_DIR.as_posix(),
        "RADAR_DUCKDB": DUCKDB_PATH.as_posix(),
        "RADAR_TMP_DIR": TMP_DIR.as_posix(),
    }
    dbt_vars = {"referencia": referencia}
    if amostra:
        dbt_vars["min_estabelecimentos"] = 1_000_000

    # Subprocesso, não dbtRunner: o dbt mantém a conexão com o DuckDB aberta no
    # processo, o que impediria a exportação da gold logo em seguida.
    resultado = subprocess.run(
        [
            sys.executable, "-c", "from dbt.cli.main import cli; cli()",
            "build",
            "--project-dir", str(DBT_DIR),
            "--profiles-dir", str(DBT_DIR),
            "--vars", json.dumps(dbt_vars),
        ],
        env=env,
        check=False,
    )
    if resultado.returncode != 0:
        raise RuntimeError("dbt build falhou (modelo ou teste de qualidade). Veja o log acima.")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--referencia", help="pasta AAAA-MM da Receita (padrão: a mais recente)")
    p.add_argument("--amostra", action="store_true", help="processa só a parte 0 de cada arquivo")
    p.add_argument("--pular-download", action="store_true", help="usa a bronze existente")
    p.add_argument("--forcar", action="store_true", help="roda mesmo se a referência já foi publicada")
    p.add_argument("--manter-zips", action="store_true", help="não apaga os zips após converter")
    p.add_argument("--com-socios", action="store_true", help="inclui a tabela de sócios")
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.pular_download:
        manifesto = _ler_manifesto()
        if not manifesto or not manifesto.get("completo"):
            raise SystemExit("Não há bronze completa para reaproveitar. Rode sem --pular-download.")
        referencia, amostra = manifesto["referencia"], manifesto["amostra"]
    else:
        referencia, amostra = args.referencia or download.ultima_referencia(), args.amostra
        if not args.forcar and referencia == export_gold.referencia_publicada():
            log.info("Referência %s já publicada. Nada a fazer.", referencia)
            _saida_actions(novo="false", referencia=referencia)
            return 0
        tabelas = TABELAS_PADRAO + (["socios"] if args.com_socios else [])
        log.info("Processando referência %s%s", referencia, " (amostra)" if amostra else "")
        etapa_bronze(referencia, tabelas, amostra, args.manter_zips)

    etapa_dbt(referencia, amostra)
    export_gold.exportar(referencia, amostra)
    _saida_actions(novo="true", referencia=referencia)
    log.info("Pipeline concluído para %s", referencia)
    return 0


if __name__ == "__main__":
    sys.exit(main())
