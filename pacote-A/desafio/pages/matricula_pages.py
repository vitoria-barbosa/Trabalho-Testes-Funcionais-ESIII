"""Page Objects do portal de Matrícula Acadêmica - DESAFIO A.

Telas: /matricula/login, /matricula/disciplinas e o comprovante.
Localizadores usados (todos por id ou data-testid, nunca XPath absoluto):
  login:        #matricula, #senha, #btn-entrar, #mensagem-erro
  disciplinas:  #tabela-disciplinas, #chk-<CODIGO> (ex.: #chk-ES3), #btn-confirmar,
                #mensagem-erro, [data-testid='disc-<CODIGO>'] .vagas
  comprovante:  #mensagem-sucesso, #comprovante, #disciplinas-matriculadas

Regra do padrão: as classes sabem COMO interagir com a tela (localizadores,
cliques, esperas). Os assert ficam nos testes.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TEMPO_ESPERA = 5


class LoginMatriculaPage:
    CAMPO_MATRICULA = (By.ID, "matricula")
    CAMPO_SENHA = (By.ID, "senha")
    BOTAO_ENTRAR = (By.ID, "btn-entrar")
    MENSAGEM_ERRO = (By.ID, "mensagem-erro")

    def __init__(self, driver, base_url):
        self.driver, self.base_url = driver, base_url
        self.wait = WebDriverWait(driver, TEMPO_ESPERA)

    def abrir(self):
        self.driver.get(f"{self.base_url}/matricula/login")
        self.wait.until(EC.visibility_of_element_located(self.CAMPO_MATRICULA))
        return self

    def entrar(self, matricula, senha):
        campo = self.wait.until(EC.visibility_of_element_located(self.CAMPO_MATRICULA))
        campo.clear()
        campo.send_keys(matricula)
        self.driver.find_element(*self.CAMPO_SENHA).send_keys(senha)
        botao = self.driver.find_element(*self.BOTAO_ENTRAR)
        botao.click()
        # O POST recarrega a página: espera a página antiga sair antes de seguir.
        self.wait.until(EC.staleness_of(botao))
        return DisciplinasPage(self.driver, self.base_url)

    def mensagem_erro(self):
        return self.wait.until(EC.visibility_of_element_located(self.MENSAGEM_ERRO)).text

    def esta_aberta(self):
        self.wait.until(EC.url_contains("/matricula/login"))
        return self.driver.find_element(*self.CAMPO_MATRICULA).is_displayed()


class DisciplinasPage:
    TABELA = (By.ID, "tabela-disciplinas")
    BOTAO_CONFIRMAR = (By.ID, "btn-confirmar")
    MENSAGEM_ERRO = (By.ID, "mensagem-erro")
    USUARIO_LOGADO = (By.ID, "usuario-logado")

    def __init__(self, driver, base_url):
        self.driver, self.base_url = driver, base_url
        self.wait = WebDriverWait(driver, TEMPO_ESPERA)

    def abrir(self):
        self.driver.get(f"{self.base_url}/matricula/disciplinas")
        return self

    def esta_aberta(self):
        """True quando a oferta de disciplinas está visível."""
        return self.wait.until(EC.visibility_of_element_located(self.TABELA)).is_displayed()

    def tabela_presente(self):
        """Verificação sem espera: usada para comprovar que a oferta NÃO abriu."""
        return len(self.driver.find_elements(*self.TABELA)) > 0

    def usuario_logado(self):
        return self.driver.find_element(*self.USUARIO_LOGADO).text

    def selecionar(self, *codigos):
        for codigo in codigos:
            chk = self.wait.until(EC.element_to_be_clickable((By.ID, f"chk-{codigo}")))
            if not chk.is_selected():
                chk.click()
        return self

    def confirmar(self):
        botao = self.wait.until(EC.element_to_be_clickable(self.BOTAO_CONFIRMAR))
        botao.click()
        # Sucesso abre o comprovante; erro recarrega a oferta. Nos dois casos
        # a página antiga fica "stale".
        self.wait.until(EC.staleness_of(botao))
        return self

    def matricular(self, *codigos):
        self.selecionar(*codigos).confirmar()
        return ComprovantePage(self.driver)

    def mensagem_erro(self):
        return self.wait.until(EC.visibility_of_element_located(self.MENSAGEM_ERRO)).text

    def vagas(self, codigo):
        celula = self.wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, f"[data-testid='disc-{codigo}'] .vagas")))
        return int(celula.text)

    def todas_as_vagas(self, codigos):
        return {c: self.vagas(c) for c in codigos}


class ComprovantePage:
    MENSAGEM_SUCESSO = (By.ID, "mensagem-sucesso")
    COMPROVANTE = (By.ID, "comprovante")
    DISCIPLINAS = (By.ID, "disciplinas-matriculadas")

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, TEMPO_ESPERA)

    def mensagem(self):
        return self.wait.until(EC.visibility_of_element_located(self.MENSAGEM_SUCESSO)).text

    def numero(self):
        return self.wait.until(EC.visibility_of_element_located(self.COMPROVANTE)).text

    def disciplinas(self):
        texto = self.wait.until(EC.visibility_of_element_located(self.DISCIPLINAS)).text
        return [c.strip() for c in texto.split(",") if c.strip()]
