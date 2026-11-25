"""
DESAFIO A - Trabalho 2: portal de Matrícula Acadêmica (Selenium + pytest)

Casos de teste (matriz completa em resultados/pacote-A/Matriz_Casos_de_Teste.csv):
  CT01  R1  Login válido (limites da faixa: 20260001 e 20260200)   [parametrize]
  CT02  R1  Login inválido (senha errada, matrícula fora da faixa,
            campos vazios)                                         [parametrize]
  CT03  R2  Oferta sem login redireciona para o login
  CT04  R3  0 disciplinas   -> "Selecione ao menos uma disciplina." [parametrize]
  CT05  R3  1 disciplina    -> sucesso                              [parametrize]
  CT06  R3  5 disciplinas   -> sucesso                              [parametrize]
  CT07  R3  6 disciplinas   -> "Máximo de 5 disciplinas por semestre." [parametrize]
  CT08  R4  Choque de horário (ES3 x RED, SEG-19h)
  CT09  R5  Vagas esgotadas (MOB lotada pela API)
  CT10  R6  Segunda matrícula do mesmo aluno
  CT11  R7  Sucesso: mensagem, comprovante COMP-NNNNNN, disciplinas e -1 vaga

Os casos de rejeição também conferem que NADA foi gravado (vagas inalteradas).

Sistema: <pasta-do-kit>/02_Pacote_A_SaborExpress_Matricula/app/app.py (http://localhost:5000)
Executar: pytest -v --html=../../resultados/pacote-A/desafio_r1.html --self-contained-html
          ($env:HEADLESS="1" para rodar sem janela)
"""
import json
import re
import urllib.request

import pytest

from pages.matricula_pages import ComprovantePage, DisciplinasPage, LoginMatriculaPage

ALUNO = "20260001"
SENHA = "senha123"
TODAS = ["ES3", "BD2", "PW2", "RED", "IHC", "EMP", "MOB"]
VAGAS_INICIAIS = {"ES3": 40, "BD2": 40, "PW2": 35, "RED": 30, "IHC": 30, "EMP": 50, "MOB": 5}


# ---------------------------------------------------------------------------
# Preparação de dados pela API (só o que a tela não monta rapidamente)
# ---------------------------------------------------------------------------
def _post(base_url, caminho, corpo=None):
    req = urllib.request.Request(
        f"{base_url}{caminho}",
        data=json.dumps(corpo or {}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as erro:
        return erro.code, json.loads(erro.read() or b"{}")


def matricular_pela_api(base_url, aluno, disciplinas):
    status, corpo = _post(base_url, "/api/matriculas", {"aluno": aluno, "disciplinas": disciplinas})
    assert status == 201, f"pré-condição falhou: {status} {corpo}"
    return corpo


@pytest.fixture(autouse=True)
def sistema_zerado(base_url):
    """Cada teste começa com vagas originais e nenhuma matrícula (testes independentes)."""
    status, _ = _post(base_url, "/api/admin/reset")
    assert status == 200


@pytest.fixture
def oferta(driver, base_url):
    """Pré-condição comum: aluno 20260001 logado, na tela de oferta."""
    pagina = LoginMatriculaPage(driver, base_url).abrir().entrar(ALUNO, SENHA)
    assert pagina.esta_aberta()
    return pagina


# ---------------------------------------------------------------------------
# R1 - Login
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("matricula", ["20260001", "20260200"], ids=["primeira_matricula", "ultima_matricula"])
def test_ct01_login_valido_abre_oferta(driver, base_url, matricula):
    oferta = LoginMatriculaPage(driver, base_url).abrir().entrar(matricula, SENHA)

    assert oferta.esta_aberta()
    assert driver.current_url.endswith("/matricula/disciplinas")
    assert oferta.usuario_logado() == matricula


@pytest.mark.parametrize(
    "matricula, senha",
    [
        ("20260001", "senha-errada"),
        ("20260201", "senha123"),   # valor-limite: logo acima da faixa 20260001..20260200
        ("", ""),
    ],
    ids=["senha_errada", "matricula_fora_da_faixa", "campos_vazios"],
)
def test_ct02_login_invalido_exibe_erro(driver, base_url, matricula, senha):
    login = LoginMatriculaPage(driver, base_url).abrir()
    oferta = login.entrar(matricula, senha)

    assert login.mensagem_erro() == "Matrícula ou senha inválidas."
    assert driver.current_url.endswith("/matricula/login")
    assert not oferta.tabela_presente()


# ---------------------------------------------------------------------------
# R2 - Acesso
# ---------------------------------------------------------------------------
def test_ct03_oferta_sem_login_redireciona(driver, base_url):
    DisciplinasPage(driver, base_url).abrir()

    login = LoginMatriculaPage(driver, base_url)
    assert login.esta_aberta()
    assert driver.current_url.endswith("/matricula/login")
    assert not DisciplinasPage(driver, base_url).tabela_presente()


# ---------------------------------------------------------------------------
# R3 - Quantidade (valores-limite 0, 1, 5 e 6) - teste orientado a dados
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "codigos, mensagem_erro",
    [
        ([], "Selecione ao menos uma disciplina."),
        (["ES3"], None),
        (["ES3", "BD2", "PW2", "IHC", "EMP"], None),
        (["ES3", "BD2", "PW2", "IHC", "EMP", "MOB"], "Máximo de 5 disciplinas por semestre."),
    ],
    ids=["CT04_0_disciplinas", "CT05_1_disciplina", "CT06_5_disciplinas", "CT07_6_disciplinas"],
)
def test_ct04_a_ct07_quantidade_de_disciplinas(driver, base_url, oferta, codigos, mensagem_erro):
    oferta.selecionar(*codigos).confirmar()

    if mensagem_erro is None:
        comprovante = ComprovantePage(driver)
        assert comprovante.mensagem() == "Matrícula realizada com sucesso!"
        assert comprovante.disciplinas() == codigos
    else:
        assert oferta.mensagem_erro() == mensagem_erro
        # Nada foi gravado: nenhuma vaga foi consumida.
        assert oferta.todas_as_vagas(TODAS) == VAGAS_INICIAIS


# ---------------------------------------------------------------------------
# R4 - Choque de horário
# ---------------------------------------------------------------------------
def test_ct08_choque_de_horario(oferta):
    oferta.selecionar("ES3", "RED").confirmar()   # ambas SEG-19h

    assert oferta.mensagem_erro() == "Choque de horário entre disciplinas selecionadas."
    assert oferta.vagas("ES3") == 40
    assert oferta.vagas("RED") == 30


# ---------------------------------------------------------------------------
# R5 - Vagas esgotadas
# ---------------------------------------------------------------------------
def test_ct09_vagas_esgotadas(driver, base_url):
    # Pré-condição pela API: 5 outros alunos ocupam as 5 vagas de MOB.
    for n in range(101, 106):
        matricular_pela_api(base_url, f"2026{n:04d}", ["MOB"])

    oferta = LoginMatriculaPage(driver, base_url).abrir().entrar(ALUNO, SENHA)
    assert oferta.vagas("MOB") == 0

    oferta.selecionar("ES3", "MOB").confirmar()

    assert oferta.mensagem_erro() == "Vagas esgotadas: MOB."
    assert oferta.vagas("MOB") == 0      # nunca negativa
    assert oferta.vagas("ES3") == 40     # a outra disciplina não foi descontada


# ---------------------------------------------------------------------------
# R6 - Matrícula única
# ---------------------------------------------------------------------------
def test_ct10_matricula_repetida(driver, base_url):
    matricular_pela_api(base_url, ALUNO, ["ES3"])   # matrícula prévia do mesmo aluno

    oferta = LoginMatriculaPage(driver, base_url).abrir().entrar(ALUNO, SENHA)
    oferta.selecionar("BD2").confirmar()

    assert oferta.mensagem_erro() == "Aluno já possui matrícula neste semestre."
    assert oferta.vagas("BD2") == 40     # segunda matrícula não consumiu vaga
    assert oferta.vagas("ES3") == 39     # só a matrícula prévia


# ---------------------------------------------------------------------------
# R7 - Sucesso
# ---------------------------------------------------------------------------
def test_ct11_sucesso_gera_comprovante_e_desconta_vagas(driver, base_url, oferta):
    antes = oferta.todas_as_vagas(["ES3", "BD2"])

    comprovante = oferta.matricular("ES3", "BD2")

    assert comprovante.mensagem() == "Matrícula realizada com sucesso!"
    assert re.fullmatch(r"COMP-\d{6}", comprovante.numero())
    assert comprovante.disciplinas() == ["ES3", "BD2"]

    depois = DisciplinasPage(driver, base_url).abrir().todas_as_vagas(["ES3", "BD2"])
    assert depois == {c: antes[c] - 1 for c in antes}
