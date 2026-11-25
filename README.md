# Trabalho 2 – Testes funcionais (ES III)

Testes funcionais pela interface web com **Selenium + pytest (Python)**.

## Equipe

- Kamila Rocha
- Mylena Duarte
- Vitória Barbosa

## O que são testes funcionais

Testes funcionais verificam se o sistema faz o que os requisitos pedem, olhando
**de fora**, do jeito que o usuário usa: abrir a página, preencher campos, clicar
em botões e conferir o que aparece na tela. Eles não olham o código interno
(teste caixa-preta). Cada caso de teste diz qual é a entrada, qual é a ação e qual
é o resultado esperado. Os casos deste trabalho foram montados com estas técnicas:

- **partição de equivalência**: um representante de cada grupo de entradas válidas e inválidas;
- **valores-limite**: valores logo abaixo, em cima e logo acima de cada limite (por exemplo, 0, 1, 5 e 6 disciplinas);
- **tabela de decisão**: combinações de condições (por exemplo, mesmo e-mail em curso igual ou diferente);
- **transição de estado**: regras que dependem do que já aconteceu (vagas esgotadas, cancelamento, matrícula repetida).

## Papel do pytest

O **pytest** é o framework que organiza e executa os testes:

- encontra e roda as funções `test_*` dos arquivos `test_*.py`;
- usa `assert` para comparar o resultado obtido com o esperado e mostra o motivo quando um teste falha;
- usa **fixtures** (no `conftest.py` e nos próprios testes) para preparar e limpar o ambiente: abrir e fechar o navegador, zerar o sistema antes de cada teste, deixar o aluno logado;
- usa `@pytest.mark.parametrize` para rodar o mesmo teste com vários dados (testes orientados a dados);
- com o plugin **pytest-html**, gera um relatório HTML com o resultado e o print de cada teste.

## Papel do Selenium

O **Selenium WebDriver** controla o navegador (Google Chrome) como se fosse uma
pessoa: abre URLs, encontra elementos pelo `id` ou `data-testid`, digita, clica,
seleciona opções e lê textos e mensagens da página. Ele também tira os prints usados
como evidência. Os testes usam **esperas explícitas** (`WebDriverWait`), que aguardam
o elemento ou a mensagem aparecer, em vez de pausas fixas (`sleep`). O Selenium
Manager baixa o driver do Chrome sozinho, então não é preciso instalar o chromedriver.

Resumindo: o pytest decide **o que** testar e **se passou**; o Selenium faz **a
interação com a tela**.

## Estrutura e papel de cada arquivo

```
trabalho2-funcionais/
  README.md
  requirements.txt
  pacote-A/desafio/
    conftest.py
    pages/__init__.py
    pages/matricula_pages.py
    test_matricula.py
  pacote-B/desafio/
    conftest.py
    pages/__init__.py
    pages/inscricoes_page.py
    test_inscricoes.py
  resultados/
    pacote-A/  desafio_r1.html, Matriz_Casos_de_Teste.csv, prints/
    pacote-B/  inscricoes_r1.html, Matriz_Casos_de_Teste.csv, prints/
```

| Arquivo                                                 | Papel                                                                                                                                                                                                                                  |
| ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `requirements.txt`                                      | Bibliotecas Python necessárias (Selenium, pytest, pytest-html, Flask para subir os sistemas).                                                                                                                                          |
| `conftest.py`                                           | Fixtures compartilhadas do pytest: cria o navegador Chrome (com opção `HEADLESS=1` para rodar sem janela), fecha no final e, depois de cada teste, salva o print da tela em `resultados/pacote-X/prints/` e o anexa ao relatório HTML. |
| `pages/__init__.py`                                     | Arquivo vazio que transforma `pages/` em pacote Python, para os testes poderem importar as páginas.                                                                                                                                    |
| `pages/matricula_pages.py` / `pages/inscricoes_page.py` | **Page Objects**: uma classe por tela, com os localizadores e as ações (preencher, clicar, esperar, ler mensagens). Eles sabem _como_ mexer na tela; os `assert` ficam nos testes.                                                     |
| `test_matricula.py` / `test_inscricoes.py`              | Os casos de teste. Cada teste zera o sistema pela API, prepara o estado necessário, executa a ação pela tela e confere o resultado com `assert`.                                                                                       |
| `resultados/pacote-X/*_r1.html`                         | Relatório do pytest-html com o resultado e o print de cada teste.                                                                                                                                                                      |
| `resultados/pacote-X/Matriz_Casos_de_Teste.csv`         | Matriz de casos de teste: regra, técnica, pré-condição, dados, passos, resultado esperado, resultado obtido, status e evidência.                                                                                                       |
| `resultados/pacote-X/prints/`                           | Print da tela final de cada teste.                                                                                                                                                                                                     |

## Pacote A – Portal de Matrícula Acadêmica

Sistema em `http://localhost:5000`. O aluno entra com matrícula e senha, vê a
oferta de disciplinas, marca as que quer cursar e confirma. Se der certo, recebe um
comprovante. Regras testadas: login (R1), acesso só com login (R2), quantidade de
disciplinas (R3), choque de horário (R4), vagas (R5), matrícula única (R6) e
sucesso com comprovante (R7).

Telas cobertas pelos Page Objects (`matricula_pages.py`): `LoginMatriculaPage`,
`DisciplinasPage` e `ComprovantePage`.

| Caso | Regra | O que verifica                                                                                                                             |
| ---- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| CT01 | R1    | Login válido nas matrículas limite da faixa (20260001 e 20260200) abre a oferta.                                                           |
| CT02 | R1    | Login inválido (senha errada, matrícula 20260201 fora da faixa, campos vazios) mostra "Matrícula ou senha inválidas." e não abre a oferta. |
| CT03 | R2    | Abrir a oferta pela URL sem login redireciona para o login.                                                                                |
| CT04 | R3    | 0 disciplinas: "Selecione ao menos uma disciplina." e nenhuma vaga consumida.                                                              |
| CT05 | R3    | 1 disciplina: matrícula realizada.                                                                                                         |
| CT06 | R3    | 5 disciplinas (máximo): matrícula realizada.                                                                                               |
| CT07 | R3    | 6 disciplinas: "Máximo de 5 disciplinas por semestre." e nenhuma vaga consumida.                                                           |
| CT08 | R4    | ES3 e RED no mesmo horário (SEG-19h): "Choque de horário entre disciplinas selecionadas."                                                  |
| CT09 | R5    | MOB lotada (5 alunos matriculados pela API): "Vagas esgotadas: MOB.", vagas nunca negativas e a outra disciplina não é descontada.         |
| CT10 | R6    | Aluno que já tem matrícula tenta de novo: "Aluno já possui matrícula neste semestre."                                                      |
| CT11 | R7    | Sucesso: mensagem, comprovante no formato `COMP-NNNNNN`, disciplinas listadas e uma vaga a menos em cada.                                  |

Nos casos de rejeição o teste também confere que nada foi gravado (vagas iguais às iniciais).

## Pacote B – Inscrições em minicursos

Sistema em `http://127.0.0.1:8000/inscricoes`. Uma página única (com JavaScript)
onde a pessoa informa nome, e-mail e curso (1 Python, 2 Java, 3 Testes de
Software, com 2 vagas cada), vê a lista de inscritos e pode cancelar uma inscrição.
Como a lista é atualizada de forma assíncrona, o Page Object (`InscricoesPage`)
espera a resposta do servidor e o redesenho da lista antes de ler os dados.

| Caso | Grupo        | O que verifica                                                                                              |
| ---- | ------------ | ----------------------------------------------------------------------------------------------------------- |
| CT01 | Fluxo válido | Inscrição válida mostra "Inscrição realizada" e aparece na lista.                                           |
| CT02 | Fluxo válido | O mesmo e-mail pode se inscrever em outro curso.                                                            |
| CT03 | Obrigatórios | Nome vazio: "Nome deve ter de 3 a 60 caracteres".                                                           |
| CT04 | Formato      | E-mail inválido (sem @, domínio sem ponto, espaço no meio, sem texto antes do @, vazio): "E-mail inválido". |
| CT05 | Obrigatórios | Sem curso selecionado: "Curso obrigatório".                                                                 |
| CT06 | Valor-limite | Nome com 2 caracteres é rejeitado.                                                                          |
| CT07 | Valor-limite | Nome com 3 caracteres (mínimo) é aceito.                                                                    |
| CT08 | Valor-limite | Nome com 60 caracteres (máximo) é aceito.                                                                   |
| CT09 | Valor-limite | Nome com 61 caracteres é rejeitado.                                                                         |
| CT10 | Estado       | Duplicidade no mesmo curso, mesmo com maiúsculas e espaços no e-mail: "Inscrição já existente".             |
| CT11 | Estado       | Terceira inscrição num curso de 2 vagas: "Curso sem vagas".                                                 |
| CT12 | Estado       | Cancelar uma inscrição remove da lista e libera a vaga para outra pessoa.                                   |
| CT13 | Normalização | Nome " Al " fica com 2 caracteres depois de aparado e é rejeitado.                                          |
| CT14 | Normalização | E-mail com espaços nas pontas é aceito e salvo sem os espaços.                                              |

A API só prepara o estado (reset e inscrições prévias); a ação testada e a
verificação principal são sempre feitas pela tela. Nas rejeições o teste confere
que a lista não recebeu a inscrição.

## Como rodar

Todos os comandos abaixo partem da raiz deste repositório (`trabalho2-funcionais/`).

### 1. Preparar o ambiente

Requisitos: Python 3.10 ou mais novo e Google Chrome instalados.

```powershell
git clone <url-do-repositorio> trabalho2-funcionais
cd trabalho2-funcionais
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Subir os sistemas testados

Os sistemas **não fazem parte deste repositório**: eles vêm no kit da disciplina
(`ESIII_Testes_Funcionais.zip`). Extraia o kit em qualquer pasta e, em um terminal
separado para cada sistema (com o `.venv` deste repositório ativado), rode:

```powershell
# Pacote A - Portal de Matrícula (http://localhost:5000)
cd <pasta-do-kit>\02_Pacote_A_SaborExpress_Matricula\app
python app.py

# Pacote B - Inscrições em minicursos (http://127.0.0.1:8000)
cd <pasta-do-kit>\03_Pacote_B_Biblioteca_Minicursos
python app.py
```

Deixe esses terminais abertos enquanto os testes rodam.

### 3. Rodar os testes

Em outro terminal, na raiz do repositório e com o `.venv` ativado:

```powershell
# Pacote A
cd pacote-A\desafio
python -m pytest test_matricula.py -v --html=..\..\resultados\pacote-A\desafio_r1.html --self-contained-html
cd ..\..

# Pacote B
cd pacote-B\desafio
python -m pytest test_inscricoes.py -v --html=..\..\resultados\pacote-B\inscricoes_r1.html --self-contained-html
cd ..\..
```

Cada pacote precisa ser rodado de dentro da própria pasta `desafio`, porque os dois
têm um pacote `pages/` e o pytest importa o de cada pasta.

O relatório HTML fica em `resultados/pacote-X/` e os prints em
`resultados/pacote-X/prints/`. Prints de testes que falharem também são copiados
para `evidencias/` (pasta ignorada pelo git).

Dicas:

- `$env:HEADLESS="1"` roda sem abrir a janela do Chrome.
- Se o sistema do Pacote A estiver em outro endereço, use `$env:BASE_URL="http://..."`.
- Rode os testes em sequência, nunca em paralelo, porque o estado do sistema é compartilhado.
