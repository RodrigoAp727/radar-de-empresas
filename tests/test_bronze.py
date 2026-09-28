import duckdb

from pipeline import bronze
from tests.sintetico import dv_cnpj, gerar


def test_dv_cnpj_exemplos_oficiais():
    assert dv_cnpj("112223330001") == "81"
    assert dv_cnpj("12ABC34501DE") == "35"  # exemplo da Receita para o CNPJ alfanumérico


def test_zip_para_parquet_preserva_acentos_e_quebras_de_linha(tmp_path, monkeypatch):
    monkeypatch.setattr(bronze, "TMP_DIR", tmp_path / "tmp")
    raw, bronze_dir = tmp_path / "raw", tmp_path / "bronze"
    esperado = gerar(raw, n_empresas=50)

    zip_path = raw / "Estabelecimentos0.zip"
    stats = bronze.zip_para_parquet(zip_path, "estabelecimentos", 0, "2026-09", bronze_dir)

    assert stats == {"linhas": esperado["Estabelecimentos0.zip"], "rejeitadas": 0}
    parquet = (bronze_dir / "estabelecimentos" / "estabelecimentos_0.parquet").as_posix()
    nomes = {r[0] for r in duckdb.sql(f"select distinct nome_fantasia from '{parquet}'").fetchall()}
    assert "PADARIA SÃO JOÃO" in nomes
    assert "LOJA\nCOM QUEBRA" in nomes
    # O CSV temporário é apagado e não sobra arquivo parcial.
    assert not list((tmp_path / "tmp").iterdir())
    assert not list((bronze_dir / "estabelecimentos").glob("*.tmp"))


def test_zip_para_parquet_tudo_como_texto(tmp_path, monkeypatch):
    monkeypatch.setattr(bronze, "TMP_DIR", tmp_path / "tmp")
    gerar(tmp_path / "raw", n_empresas=5)
    bronze.zip_para_parquet(tmp_path / "raw" / "Empresas0.zip", "empresas", 0, "2026-09", tmp_path / "b")

    tipos = duckdb.sql(
        f"describe select * from '{(tmp_path / 'b' / 'empresas' / 'empresas_0.parquet').as_posix()}'"
    ).fetchall()
    assert {t[1] for t in tipos} == {"VARCHAR"}
    # cnpj_basico mantém zeros à esquerda (nunca vira número)
    assert [t[0] for t in tipos][:2] == ["cnpj_basico", "razao_social"]
