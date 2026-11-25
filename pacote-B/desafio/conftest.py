"""Fixtures do desafio B.

Variáveis de ambiente opcionais:
    HEADLESS=1      roda sem abrir a janela do Chrome
    CHROME_BINARY   Chrome fora do caminho padrão
    CHROMEDRIVER    driver local (senão o Selenium Manager resolve sozinho)

Evidências: ao fim de cada teste (aprovado ou não) a tela é salva em
resultados/pacote-B/prints/<teste>.png e embutida no relatório HTML, se
pytest-html estiver ativo. Falhas também vão para evidencias/ (ignorada no git).
"""
from pathlib import Path
import os, re
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

PASTA_PRINTS = Path(__file__).resolve().parents[2] / 'resultados' / 'pacote-B' / 'prints'


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    if os.environ.get('HEADLESS') == '1': options.add_argument('--headless=new')
    options.add_argument('--window-size=1280,900')
    if os.environ.get('CHROME_BINARY'): options.binary_location=os.environ['CHROME_BINARY']
    service = Service(os.environ['CHROMEDRIVER']) if os.environ.get('CHROMEDRIVER') else Service()
    browser = webdriver.Chrome(options=options, service=service)
    browser.implicitly_wait(0)  # só esperas explícitas
    yield browser
    browser.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != 'call' or 'driver' not in item.funcargs:
        return
    drv = item.funcargs['driver']
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', item.name)
    try:
        png = drv.get_screenshot_as_png()
    except Exception:
        return
    PASTA_PRINTS.mkdir(parents=True, exist_ok=True)
    (PASTA_PRINTS / (name + '.png')).write_bytes(png)
    if report.failed:
        dest = Path('evidencias'); dest.mkdir(exist_ok=True)
        (dest / (name + '.png')).write_bytes(png)
    html = item.config.pluginmanager.getplugin('html')
    if html is not None:
        extras = getattr(report, 'extras', [])
        extras.append(html.extras.png(drv.get_screenshot_as_base64(), name=name))
        report.extras = extras
