"""Page Object da tela de inscrições em minicursos (/inscricoes) - DESAFIO B.

Localizadores (id / data-testid, nunca XPath absoluto):
  #nome, #email, #curso, #confirmar, #erro, #sucesso, #lista,
  [data-testid="cancelar-<ID>"]

A tela é uma página única com JavaScript: o envio usa fetch() e a lista é
redesenhada de forma assíncrona. Por isso todas as leituras usam
WebDriverWait (esperas explícitas), nunca sleep fixo.
"""
import re

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

BASE_URL = "http://127.0.0.1:8000"
TEMPO_ESPERA = 5
_LINHA = re.compile(r"^(?P<nome>.*) / (?P<email>\S+) / curso (?P<curso>\d+)")


class InscricoesPage:
    NOME = (By.ID, "nome")
    EMAIL = (By.ID, "email")
    CURSO = (By.ID, "curso")
    CONFIRMAR = (By.ID, "confirmar")
    ERRO = (By.ID, "erro")
    SUCESSO = (By.ID, "sucesso")
    ITENS_LISTA = (By.CSS_SELECTOR, "#lista li")

    def __init__(self, driver, base_url=BASE_URL):
        self.driver, self.base_url = driver, base_url
        self.wait = WebDriverWait(driver, TEMPO_ESPERA,
                                  ignored_exceptions=[StaleElementReferenceException])

    # ----------------------------------------------------------------- ações
    def abrir(self, itens_esperados=0):
        """Abre a tela e espera a lista inicial (carregada por fetch) aparecer."""
        self.driver.get(f"{self.base_url}/inscricoes")
        self.wait.until(EC.element_to_be_clickable(self.CONFIRMAR))
        self.esperar_quantidade(itens_esperados)
        return self

    def preencher(self, nome="", email="", curso=""):
        for localizador, valor in ((self.NOME, nome), (self.EMAIL, email)):
            campo = self.driver.find_element(*localizador)
            campo.clear()
            campo.send_keys(valor)
        Select(self.driver.find_element(*self.CURSO)).select_by_value(str(curso))
        return self

    def confirmar(self):
        """Envia o formulário e espera o servidor responder (#erro ou #sucesso preenchido)."""
        self.driver.find_element(*self.CONFIRMAR).click()
        self.wait.until(lambda d: d.find_element(*self.ERRO).text or d.find_element(*self.SUCESSO).text)
        return self

    def inscrever(self, nome, email, curso):
        return self.preencher(nome, email, curso).confirmar()

    def cancelar(self, inscricao_id):
        botao = self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, f"[data-testid='cancelar-{inscricao_id}']")))
        botao.click()
        self.wait.until(EC.text_to_be_present_in_element(self.SUCESSO, "Inscrição cancelada"))
        # A lista é redesenhada depois da mensagem: espera o item sumir.
        self.wait.until(lambda d: str(inscricao_id) not in [i["id"] for i in self._ler_itens()])
        return self

    # --------------------------------------------------------------- leituras
    def mensagem_erro(self):
        return self.driver.find_element(*self.ERRO).text

    def mensagem_sucesso(self):
        return self.driver.find_element(*self.SUCESSO).text

    def esperar_quantidade(self, quantidade):
        self.wait.until(lambda d: len(d.find_elements(*self.ITENS_LISTA)) == quantidade)
        return self

    def itens(self):
        """Lista atual como [{'id', 'nome', 'email', 'curso'}].

        A tupla é sempre "verdadeira", então o wait só repete se a lista for
        redesenhada no meio da leitura (StaleElementReferenceException ignorada).
        """
        return self.wait.until(lambda d: (self._ler_itens(),))[0]

    def _ler_itens(self):
        itens = []
        for li in self.driver.find_elements(*self.ITENS_LISTA):
            m = _LINHA.match(li.text)
            if m:
                itens.append({"id": li.get_attribute("data-id"), **m.groupdict(),
                              "curso": int(m.group("curso"))})
        return itens
