import pytest

from pipeline.config import LAYOUTS, tabela_do_arquivo


@pytest.mark.parametrize(
    ("nome", "esperado"),
    [
        ("Estabelecimentos3.zip", ("estabelecimentos", 3)),
        ("Empresas0.zip", ("empresas", 0)),
        ("Socios9.zip", ("socios", 9)),
        ("Cnaes.zip", ("cnaes", 0)),
        ("Simples.zip", ("simples", 0)),
        ("cnpj.tar.gz", None),
        ("Desconhecido.zip", None),
    ],
)
def test_tabela_do_arquivo(nome, esperado):
    assert tabela_do_arquivo(nome) == esperado


def test_layouts_seguem_dicionario_da_receita():
    # Quantidade de colunas do dicionário de dados oficial.
    assert len(LAYOUTS["estabelecimentos"]) == 30
    assert len(LAYOUTS["empresas"]) == 7
    assert len(LAYOUTS["simples"]) == 7
    assert len(LAYOUTS["socios"]) == 11
