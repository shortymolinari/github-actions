# GitHub Actions

Apuntes de estudio sobre **GitHub Actions**: qué son, cómo funcionan y cuáles son sus piezas principales.

## Tabla de contenido

- [¿Qué es GitHub Actions?](#qué-es-github-actions)
- [¿Cómo encaja todo?](#cómo-encaja-todo)
- [Componentes principales](#componentes-principales)
  - [Workflows](#1-workflows)
  - [Events](#2-events-eventos)
  - [Jobs](#3-jobs)
  - [Steps](#4-steps)
  - [Actions](#5-actions)
  - [Runners](#6-runners)
- [Otros conceptos importantes](#otros-conceptos-importantes)
- [Ejemplo completo](#ejemplo-completo)
- [Recursos](#recursos)

---

## ¿Qué es GitHub Actions?

**GitHub Actions** es la plataforma de **CI/CD** (Integración Continua / Entrega Continua) y automatización integrada en GitHub. Permite ejecutar tareas automáticamente cuando ocurre algo en tu repositorio, por ejemplo:

- Ejecutar tests cada vez que alguien hace `push` o abre un Pull Request.
- Compilar y publicar una aplicación cuando se crea un release.
- Desplegar a producción al hacer merge en `main`.
- Etiquetar issues, enviar notificaciones, programar tareas periódicas (cron), etc.

Todo se define con archivos **YAML** dentro del propio repositorio, en la carpeta:

```text
.github/workflows/
```

---

## ¿Cómo encaja todo?

```text
Evento (push, pull_request, schedule...)
   │
   ▼
Workflow  (.github/workflows/ci.yml)
   │
   ├── Job "build"  ──► se ejecuta en un Runner (ubuntu-latest)
   │      ├── Step 1: actions/checkout@v4      (usa una Action)
   │      ├── Step 2: npm install              (ejecuta un comando)
   │      └── Step 3: npm test
   │
   └── Job "deploy" ──► se ejecuta en otro Runner (needs: build)
          └── Step 1: ./deploy.sh
```

> **Resumen en una línea:** un **evento** dispara un **workflow**, que contiene uno o más **jobs**, cada job corre en un **runner** y está compuesto por **steps**, y cada step ejecuta un comando o una **action**.

---

## Componentes principales

### 1. Workflows

Un **workflow** es un proceso automatizado configurable que ejecuta uno o más jobs. Se define en un archivo `.yml` o `.yaml` dentro de `.github/workflows/`. Un repositorio puede tener **varios workflows**, cada uno para un propósito distinto (tests, deploy, linting...).

```yaml
name: CI                 # Nombre visible en la pestaña "Actions"

on: [push]               # Evento que lo dispara

jobs:                    # Lista de jobs
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Hola GitHub Actions"
```

| Clave        | Descripción                                                        |
| ------------ | ------------------------------------------------------------------ |
| `name`       | Nombre del workflow (opcional).                                    |
| `run-name`   | Nombre dinámico de cada ejecución (opcional).                      |
| `on`         | Evento(s) que disparan el workflow. **Obligatorio.**               |
| `env`        | Variables de entorno disponibles para todos los jobs.              |
| `permissions`| Permisos del `GITHUB_TOKEN` (lectura/escritura).                   |
| `concurrency`| Evita ejecuciones simultáneas del mismo grupo.                     |
| `defaults`   | Valores por defecto (por ejemplo `shell` o `working-directory`).  |
| `jobs`       | Los trabajos a ejecutar. **Obligatorio.**                          |

---

### 2. Events (eventos)

Un **evento** es una actividad específica que **dispara** un workflow. Se configuran con la clave `on`.

#### Eventos más comunes

| Evento                | Se dispara cuando...                                              |
| --------------------- | ----------------------------------------------------------------- |
| `push`                | Se hace push a una rama o tag.                                    |
| `pull_request`        | Se abre, actualiza o cierra un Pull Request.                      |
| `workflow_dispatch`   | Se lanza **manualmente** desde la UI, la CLI o la API.            |
| `schedule`            | En horarios programados con sintaxis **cron** (en UTC).           |
| `release`             | Se publica, crea o edita un release.                              |
| `issues`              | Se abre, edita, cierra o etiqueta un issue.                       |
| `issue_comment`       | Se comenta en un issue o PR.                                      |
| `workflow_call`       | Otro workflow lo invoca (workflows **reutilizables**).            |
| `workflow_run`        | Termina otro workflow.                                            |
| `repository_dispatch` | Un sistema externo lo dispara vía API.                            |

#### Formas de declararlos

```yaml
# Un solo evento
on: push

# Varios eventos
on: [push, pull_request]

# Con filtros
on:
  push:
    branches: [main, 'release/**']
    paths:
      - 'src/**'
    tags: ['v*']
  pull_request:
    types: [opened, synchronize]
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'     # Todos los lunes a las 06:00 UTC
  workflow_dispatch:
    inputs:
      entorno:
        description: 'Entorno de despliegue'
        required: true
        default: 'staging'
        type: choice
        options: [staging, production]
```

**Filtros útiles:** `branches`, `branches-ignore`, `tags`, `tags-ignore`, `paths`, `paths-ignore`, `types`.

---

### 3. Jobs

Un **job** es un conjunto de **steps** que se ejecutan en el **mismo runner**. Características clave:

- Por defecto, los jobs se ejecutan **en paralelo**.
- Con `needs` puedes hacer que un job **espere** a otro (dependencias).
- Cada job corre en una máquina **limpia e independiente**: no comparten archivos salvo que uses *artifacts* o *cache*.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Compilando..."

  test:
    needs: build              # Espera a que "build" termine bien
    runs-on: ubuntu-latest
    steps:
      - run: echo "Probando..."

  deploy:
    needs: [build, test]      # Espera a ambos
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - run: echo "Desplegando..."
```

#### Opciones de un job

| Clave               | Descripción                                                            |
| ------------------- | ---------------------------------------------------------------------- |
| `runs-on`           | Runner donde se ejecuta. **Obligatorio.**                              |
| `needs`             | Jobs de los que depende.                                               |
| `if`                | Condición para ejecutar el job.                                        |
| `steps`             | Lista de pasos.                                                        |
| `env`               | Variables de entorno del job.                                          |
| `strategy.matrix`   | Ejecuta el job con múltiples combinaciones (versiones, SO...).         |
| `timeout-minutes`   | Tiempo máximo de ejecución (por defecto 360).                          |
| `continue-on-error` | Permite que el workflow siga aunque el job falle.                      |
| `environment`       | Entorno de despliegue (con reglas de protección y secretos propios).   |
| `outputs`           | Valores que el job expone a otros jobs.                                |
| `container`         | Ejecuta los steps dentro de un contenedor Docker.                      |
| `services`          | Contenedores auxiliares (ej. base de datos para tests).                |
| `uses`              | Llama a un **workflow reutilizable** en lugar de definir steps.        |

#### Matrix (matriz)

Permite ejecutar el mismo job con distintas combinaciones:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        node: [18, 20, 22]
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
```

Esto genera **6 jobs** (2 sistemas × 3 versiones).

---

### 4. Steps

Un **step** es una tarea individual dentro de un job. Se ejecutan **en orden secuencial** y comparten el sistema de archivos del runner. Un step puede:

1. **Ejecutar un comando** de shell con `run`.
2. **Usar una action** con `uses`.

```yaml
steps:
  # Usar una action
  - name: Descargar el código
    uses: actions/checkout@v4

  # Usar una action con parámetros
  - name: Configurar Node
    uses: actions/setup-node@v4
    with:
      node-version: 20

  # Ejecutar un comando
  - name: Instalar dependencias
    run: npm ci

  # Ejecutar varios comandos
  - name: Build y tests
    run: |
      npm run build
      npm test
```

#### Opciones de un step

| Clave               | Descripción                                                  |
| ------------------- | ------------------------------------------------------------ |
| `name`              | Nombre visible del paso.                                     |
| `id`                | Identificador para referenciar sus outputs.                  |
| `uses`              | Action a utilizar.                                           |
| `run`               | Comando(s) a ejecutar.                                       |
| `with`              | Parámetros de entrada para la action.                        |
| `env`               | Variables de entorno del paso.                               |
| `if`                | Condición para ejecutar el paso.                             |
| `shell`             | Shell a usar (`bash`, `pwsh`, `python`...).                  |
| `working-directory` | Directorio donde se ejecuta `run`.                           |
| `continue-on-error` | Si falla, el job continúa.                                   |
| `timeout-minutes`   | Tiempo máximo del paso.                                      |

---

### 5. Actions

Una **action** es una aplicación **reutilizable** que realiza una tarea común (descargar código, instalar un lenguaje, subir archivos, desplegar...). Se usan con `uses` y se pueden encontrar en el [GitHub Marketplace](https://github.com/marketplace?type=actions).

```yaml
uses: <owner>/<repo>@<versión>
```

| Formato                          | Ejemplo                                   |
| -------------------------------- | ----------------------------------------- |
| Action pública con tag           | `actions/checkout@v4`                     |
| Fijada a un commit (más segura)  | `actions/checkout@<sha-completo>`         |
| Action local del repo            | `./.github/actions/mi-action`             |
| Imagen Docker                    | `docker://alpine:3.20`                    |

#### Tipos de actions que puedes crear

- **JavaScript:** se ejecutan directamente en Node.js. Rápidas.
- **Docker container:** empaquetan su propio entorno.
- **Composite:** combinan varios steps en una sola action reutilizable.

#### Actions oficiales muy usadas

| Action                         | Para qué sirve                              |
| ------------------------------ | ------------------------------------------- |
| `actions/checkout`             | Clona el repositorio en el runner.          |
| `actions/setup-node`           | Instala Node.js.                            |
| `actions/setup-python`         | Instala Python.                             |
| `actions/cache`                | Cachea dependencias entre ejecuciones.      |
| `actions/upload-artifact`      | Guarda archivos generados por un job.       |
| `actions/download-artifact`    | Recupera archivos de otro job.              |

---

### 6. Runners

Un **runner** es el **servidor (máquina)** que ejecuta los jobs. Cada job se ejecuta en un runner nuevo.

#### GitHub-hosted runners

Máquinas virtuales gestionadas por GitHub. Se crean limpias para cada job y se destruyen al terminar.

| Etiqueta `runs-on`  | Sistema operativo          |
| ------------------- | -------------------------- |
| `ubuntu-latest`     | Linux (Ubuntu)             |
| `windows-latest`    | Windows Server             |
| `macos-latest`      | macOS                      |

También hay versiones específicas (`ubuntu-24.04`, `windows-2022`...) y **larger runners** con más CPU/RAM (de pago).

#### Self-hosted runners

Máquinas **propias** (servidor, VM, Raspberry Pi, cluster...) donde instalas el agente de runner de GitHub.

```yaml
runs-on: [self-hosted, linux, x64]
```

| Característica    | GitHub-hosted                 | Self-hosted                          |
| ----------------- | ----------------------------- | ------------------------------------ |
| Mantenimiento     | Lo hace GitHub                | Lo haces tú                          |
| Entorno           | Limpio en cada job            | Persistente (hay que limpiarlo)      |
| Coste             | Minutos incluidos según plan  | Gratis en GitHub, pagas tu hardware  |
| Personalización   | Limitada                      | Total (hardware, software, red)      |
| Acceso a red interna | No                         | Sí                                   |

> ⚠️ **Seguridad:** no uses self-hosted runners en repositorios **públicos**, porque cualquier PR podría ejecutar código en tu máquina.

---

## Otros conceptos importantes

### Variables de entorno

```yaml
env:
  APP_ENV: production           # Nivel workflow

jobs:
  build:
    env:
      NODE_ENV: test            # Nivel job
    steps:
      - run: echo $APP_ENV $NODE_ENV
        env:
          DEBUG: true           # Nivel step
```

Las variables definidas en un nivel más específico **sobrescriben** a las del nivel superior.

### Secrets y variables

Se configuran en **Settings → Secrets and variables → Actions**.

```yaml
steps:
  - run: ./deploy.sh
    env:
      API_KEY: ${{ secrets.API_KEY }}      # Valores sensibles (ocultos en logs)
      REGION: ${{ vars.REGION }}           # Valores de configuración no sensibles
```

`secrets.GITHUB_TOKEN` es un token **automático** que GitHub genera en cada ejecución para interactuar con el repositorio.

### Contexts y expresiones

Las expresiones `${{ ... }}` permiten acceder a información de la ejecución:

| Context     | Contiene                                                       |
| ----------- | -------------------------------------------------------------- |
| `github`    | Info del evento, repo, rama, actor (`github.ref`, `github.sha`)|
| `env`       | Variables de entorno.                                          |
| `secrets`   | Secretos.                                                      |
| `vars`      | Variables de configuración.                                    |
| `matrix`    | Valores de la matriz actual.                                   |
| `needs`     | Outputs y resultados de jobs previos.                          |
| `steps`     | Outputs de steps anteriores (por `id`).                        |
| `runner`    | Info del runner (`runner.os`).                                 |
| `inputs`    | Entradas de `workflow_dispatch` / `workflow_call`.             |

Funciones de estado útiles en `if`: `success()`, `failure()`, `always()`, `cancelled()`.

```yaml
- name: Notificar fallo
  if: failure()
  run: echo "Algo salió mal"
```

### Outputs entre steps y jobs

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.ver.outputs.version }}
    steps:
      - id: ver
        run: echo "version=1.2.3" >> "$GITHUB_OUTPUT"

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: echo "Desplegando versión ${{ needs.build.outputs.version }}"
```

### Artifacts y cache

- **Artifacts:** archivos generados (builds, reportes) que se guardan tras la ejecución o se pasan entre jobs.
- **Cache:** reutiliza dependencias (`node_modules`, `~/.m2`...) entre ejecuciones para acelerar.

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: build
    path: dist/
```

### Workflows reutilizables

Un workflow con `on: workflow_call` puede ser llamado desde otros:

```yaml
jobs:
  ci:
    uses: ./.github/workflows/reusable-tests.yml
    with:
      node-version: 20
    secrets: inherit
```

---

## Ejemplo completo

Archivo `.github/workflows/ci.yml`:

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    name: Tests (Node ${{ matrix.node }})
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node: [20, 22]
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
          cache: npm

      - name: Instalar dependencias
        run: npm ci

      - name: Ejecutar tests
        run: npm test

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - run: npm ci && npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  deploy:
    needs: build
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
      - name: Desplegar
        run: echo "Desplegando a producción..."
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```

**Qué hace:**

1. Se dispara con `push` o PR a `main`, o manualmente.
2. `test` corre en paralelo para Node 20 y 22.
3. `build` espera a que pasen los tests y guarda `dist/` como artifact.
4. `deploy` solo corre en push a `main`, descarga el artifact y despliega usando un secreto.

---

## Glosario rápido

| Término      | Definición corta                                                     |
| ------------ | -------------------------------------------------------------------- |
| **Workflow** | Archivo YAML con un proceso automatizado completo.                  |
| **Event**    | Lo que dispara el workflow (`push`, `pull_request`, `schedule`...). |
| **Job**      | Grupo de steps que corre en un mismo runner.                        |
| **Step**     | Tarea individual: un comando (`run`) o una action (`uses`).         |
| **Action**   | Componente reutilizable que realiza una tarea.                      |
| **Runner**   | Máquina que ejecuta los jobs.                                       |
| **Secret**   | Valor sensible cifrado (tokens, contraseñas).                       |
| **Artifact** | Archivo generado que se conserva o comparte entre jobs.             |
| **Matrix**   | Estrategia para correr un job con varias combinaciones.             |

---

## Recursos

- [Documentación oficial de GitHub Actions](https://docs.github.com/es/actions)
- [Sintaxis de workflows](https://docs.github.com/es/actions/writing-workflows/workflow-syntax-for-github-actions)
- [Eventos que disparan workflows](https://docs.github.com/es/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows)
- [GitHub Marketplace – Actions](https://github.com/marketplace?type=actions)
