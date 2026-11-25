"""
DESAFIO B - Trabalho 2: inscrições em minicursos (Selenium + pytest)

Sistema: http://127.0.0.1:8000/inscricoes  (3 cursos: 1 Python, 2 Java,
3 Testes de Software, com 2 vagas cada).

Casos (matriz completa em resultados/pacote-B/Matriz_Casos_de_Teste.csv):
  Fluxos válidos          CT01 inscrição válida; CT02 mesmo e-mail em outro curso
  Obrigatórios/formato    CT03 nome vazio; CT04 e-mail inválido [parametrize];
                          CT05 curso ausente
  Valores-limite          CT06..CT09 nome com 2, 3, 60 e 61 caracteres [parametrize]
  Regras com estado       CT10 duplicidade com maiúsculas/espaços; CT11 lotação;
                          CT12 cancelamento seguido de nova inscrição
  Normalização (extra)    CT13 nome aparado fica com 2 caracteres;
                          CT14 e-mail com espaços nas pontas é aceito e aparado

A API só PREPARA o estado (reset e inscrições prévias). A ação avaliada e a
verificação principal são sempre feitas pela tela. Nas rejeições, o teste
também confere que a lista não recebeu a inscrição.

Executar em sequência (estado compartilhado), nunca em paralelo:
    python -m pytest test_inscricoes.py -v --html=../../resultados/pacote-B/inscricoes_r1.html --self-contained-html
"""
import json
import urllib.request

import pytest

from pages.inscricoes_page import BASE_URL, InscricoesPage

PYTHON, JAVA, TESTES = 1, 2, 3


def _post(caminho, corpo=None):
    req = urllib.request.Request(
        BASE_URL + caminho,
        data=json.dumps(corpo or {}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


def inscrever_pela_api(nome, email, curso):
    return _post("/api/inscricoes", {"nome": nome, "email": email, "curso": curso})


@pytest.fixture(autouse=True)
def inscricoes_zeradas():
    """Cada teste começa sem nenhuma inscrição (testes independentes, qualquer ordem)."""
    _post("/api/reset")


@pytest.fixture
def tela(driver):
    return InscricoesPage(driver).abrir()


# ---------------------------------------------------------------------------
# Fluxos válidos
# ---------------------------------------------------------------------------
def test_ct01_inscricao_valida(tela):
    tela.inscrever("Ana Souza", "ana@ads.local", PYTHON)

    assert tela.mensagem_sucesso() == "Inscrição realizada"
    assert tela.mensagem_erro() == ""
    tela.esperar_quantidade(1)
    item = tela.itens()[0]
    assert (item["nome"], item["email"], item["curso"]) == ("Ana Souza", "ana@ads.local", PYTHON)


def test_ct02_mesmo_email_em_outro_curso(driver):
    inscrever_pela_api("Ana Souza", "ana@ads.local", PYTHON)
    tela = InscricoesPage(driver).abrir(itens_esperados=1)

    tela.inscrever("Ana Souza", "ana@ads.local", JAVA)

    assert tela.mensagem_sucesso() == "Inscrição realizada"
    tela.esperar_quantidade(2)
    assert sorted(i["curso"] for i in tela.itens() if i["email"] == "ana@ads.local") == [PYTHON, JAVA]


# ---------------------------------------------------------------------------
# Obrigatórios e formato
# ---------------------------------------------------------------------------
def test_ct03_nome_vazio(tela):
    tela.inscrever("", "ana@ads.local", PYTHON)

    assert tela.mensagem_erro() == "Nome deve ter de 3 a 60 caracteres"
    assert tela.mensagem_sucesso() == ""
    assert tela.itens() == []


@pytest.mark.parametrize(
    "email",
    ["anaads.local", "ana@adslocal", "ana souza@ads.local", "@ads.local", ""],
    ids=["sem_arroba", "dominio_sem_ponto", "espaco_no_meio", "sem_texto_antes_arroba", "vazio"],
)
def test_ct04_email_invalido(tela, email):
    tela.inscrever("Ana Souza", email, PYTHON)

    assert tela.mensagem_erro() == "E-mail inválido"
    assert tela.mensagem_sucesso() == ""
    assert tela.itens() == []


def test_ct05_curso_ausente(tela):
    tela.inscrever("Ana Souza", "ana@ads.local", "")   # opção "Selecione"

    assert tela.mensagem_erro() == "Curso obrigatório"
    assert tela.mensagem_sucesso() == ""
    assert tela.itens() == []


# ---------------------------------------------------------------------------
# Valores-limite do nome (3 a 60 caracteres) - orientado a dados
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "tamanho, aceito",
    [(2, False), (3, True), (60, True), (61, False)],
    ids=["CT06_2_caracteres", "CT07_3_caracteres", "CT08_60_caracteres", "CT09_61_caracteres"],
)
def test_ct06_a_ct09_limites_do_nome(tela, tamanho, aceito):
    nome = "N" * tamanho
    tela.inscrever(nome, f"limite{tamanho}@ads.local", TESTES)

    if aceito:
        assert tela.mensagem_sucesso() == "Inscrição realizada"
        tela.esperar_quantidade(1)
        assert tela.itens()[0]["nome"] == nome
    else:
        assert tela.mensagem_erro() == "Nome deve ter de 3 a 60 caracteres"
        assert tela.itens() == []


# ---------------------------------------------------------------------------
# Regras com estado
# ---------------------------------------------------------------------------
def test_ct10_duplicidade_ignora_maiusculas_e_espacos(driver):
    inscrever_pela_api("Ana Souza", "ana@ads.local", PYTHON)
    tela = InscricoesPage(driver).abrir(itens_esperados=1)

    tela.inscrever("Ana Souza", "  ANA@ADS.Local  ", PYTHON)

    assert tela.mensagem_erro() == "Inscrição já existente"
    assert tela.mensagem_sucesso() == ""
    assert len(tela.itens()) == 1


def test_ct11_lotacao_terceira_inscricao(driver):
    inscrever_pela_api("Bruno Lima", "bruno@ads.local", TESTES)
    inscrever_pela_api("Carla Dias", "carla@ads.local", TESTES)
    tela = InscricoesPage(driver).abrir(itens_esperados=2)

    tela.inscrever("Diego Reis", "diego@ads.local", TESTES)

    assert tela.mensagem_erro() == "Curso sem vagas"
    assert tela.mensagem_sucesso() == ""
    assert "diego@ads.local" not in [i["email"] for i in tela.itens()]
    assert len(tela.itens()) == 2


def test_ct12_cancelamento_libera_vaga(driver):
    inscrever_pela_api("Bruno Lima", "bruno@ads.local", JAVA)
    carla = inscrever_pela_api("Carla Dias", "carla@ads.local", JAVA)
    tela = InscricoesPage(driver).abrir(itens_esperados=2)

    tela.cancelar(carla["id"])

    assert tela.mensagem_sucesso() == "Inscrição cancelada"
    assert [i["email"] for i in tela.itens()] == ["bruno@ads.local"]

    # A vaga liberada pode ser ocupada por outra pessoa.
    tela.inscrever("Diego Reis", "diego@ads.local", JAVA)

    assert tela.mensagem_sucesso() == "Inscrição realizada"
    tela.esperar_quantidade(2)
    assert sorted(i["email"] for i in tela.itens()) == ["bruno@ads.local", "diego@ads.local"]


# ---------------------------------------------------------------------------
# Normalização (casos extras)
# ---------------------------------------------------------------------------
def test_ct13_nome_aparado_com_2_caracteres(tela):
    tela.inscrever("   Al   ", "al@ads.local", PYTHON)   # 8 caracteres, 2 após aparar

    assert tela.mensagem_erro() == "Nome deve ter de 3 a 60 caracteres"
    assert tela.itens() == []


def test_ct14_email_com_espacos_nas_pontas_e_aceito(tela):
    tela.inscrever("Bia Melo", "  Bia@ADS.local  ", JAVA)

    assert tela.mensagem_sucesso() == "Inscrição realizada"
    tela.esperar_quantidade(1)
    # A regra exige aparar espaços; maiúsculas só importam na duplicidade.
    assert tela.itens()[0]["email"].casefold() == "bia@ads.local"
