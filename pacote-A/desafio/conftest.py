"""
Configuração compartilhada do pytest (fixtures).

O Selenium 4.6+ já baixa o driver correto sozinho (Selenium Manager):
não é preciso instalar o chromedriver manualmente.

Variáveis de ambiente opcionais:
    BASE_URL  -> endereço do sistema (padrão http://localhost:5000)
    HEADLESS  -> "1" para rodar sem abrir a janela do navegador
    CI        -> "1" ao rodar em contêiner/pipeline (desliga o sandbox do Chrome)

Evidências: ao fim de cada teste (aprovado ou não) a tela é salva em
resultados/pacote-A/prints/<teste>.png e embutida no relatório HTML
(pytest-html). Falhas também vão para evidencias/ (pasta ignorada no git).
"""
import os
import pathlib
import re

import pytest
from selenium import webdriver

BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
PASTA_PRINTS = pathlib.Path(__file__).resolve().parents[2] / "resultados" / "pacote-A" / "prints"


@pytest.fixture
def base_url():
    return BASE_URL


@pytest.fixture
def driver():
    opcoes = webdriver.ChromeOptions()
    if os.getenv("HEADLESS") == "1":
        opcoes.add_argument("--headless=new")
    if os.getenv("CI") == "1":  # contêiner / GitHub Actions
        opcoes.add_argument("--no-sandbox")
        opcoes.add_argument("--disable-dev-shm-usage")
    opcoes.add_argument("--window-size=1280,900")
    drv = webdriver.Chrome(options=opcoes)
    drv.implicitly_wait(0)  # usamos esperas EXPLÍCITAS (WebDriverWait)
    yield drv
    drv.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Ao fim da fase 'call', fotografa a tela final do teste como evidência."""
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call" or "driver" not in item.funcargs:
        return
    drv = item.funcargs["driver"]
    nome = re.sub(r"[^a-zA-Z0-9_-]", "_", item.name)
    try:
        png = drv.get_screenshot_as_png()
    except Exception:  # navegador já fechado: não há o que fotografar
        return
    PASTA_PRINTS.mkdir(parents=True, exist_ok=True)
    (PASTA_PRINTS / f"{nome}.png").write_bytes(png)
    if rep.failed:
        falhas = pathlib.Path("evidencias")
        falhas.mkdir(exist_ok=True)
        (falhas / f"{nome}.png").write_bytes(png)
    html = item.config.pluginmanager.getplugin("html")
    if html is not None:
        extras = getattr(rep, "extras", [])
        extras.append(html.extras.url(drv.current_url, name="URL final"))
        extras.append(html.extras.png(drv.get_screenshot_as_base64(), name=nome))
        rep.extras = extras
