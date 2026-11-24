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
   │      ├── Step 1: actions/checkout@v7      (usa una Action)
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

| Clave         | Descripción                                                      |
| ------------- | ---------------------------------------------------------------- |
| `name`        | Nombre del workflow (opcional).                                  |
| `run-name`    | Nombre dinámico de cada ejecución (opcional).                    |
| `on`          | Evento(s) que disparan el workflow. **Obligatorio.**             |
| `env`         | Variables de entorno disponibles para todos los jobs.            |
| `permissions` | Permisos del `GITHUB_TOKEN` (lectura/escritura).                 |
| `concurrency` | Evita ejecuciones simultáneas del mismo grupo.                   |
| `defaults`    | Valores por defecto (por ejemplo `shell` o `working-directory`). |
| `jobs`        | Los trabajos a ejecutar. **Obligatorio.**                        |

---

### 2. Events (eventos)

Un **evento** es una actividad específica que **dispara** un workflow. Se configuran con la clave `on`.

#### Eventos más comunes

| Evento                | Se dispara cuando...                                    |
| --------------------- | ------------------------------------------------------- |
| `push`                | Se hace push a una rama o tag.                          |
| `pull_request`        | Se abre, actualiza o cierra un Pull Request.            |
| `workflow_dispatch`   | Se lanza **manualmente** desde la UI, la CLI o la API.  |
| `schedule`            | En horarios programados con sintaxis **cron** (en UTC). |
| `release`             | Se publica, crea o edita un release.                    |
| `issues`              | Se abre, edita, cierra o etiqueta un issue.             |
| `issue_comment`       | Se comenta en un issue o PR.                            |
| `workflow_call`       | Otro workflow lo invoca (workflows **reutilizables**).  |
| `workflow_run`        | Termina otro workflow.                                  |
| `repository_dispatch` | Un sistema externo lo dispara vía API.                  |

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
      environment:            # Nombre libre del input; se lee con ${{ inputs.environment }}
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

| Clave               | Descripción                                                          |
| ------------------- | -------------------------------------------------------------------- |
| `runs-on`           | Runner donde se ejecuta. **Obligatorio.**                            |
| `needs`             | Jobs de los que depende.                                             |
| `if`                | Condición para ejecutar el job.                                      |
| `steps`             | Lista de pasos.                                                      |
| `env`               | Variables de entorno del job.                                        |
| `strategy.matrix`   | Ejecuta el job con múltiples combinaciones (versiones, SO...).       |
| `timeout-minutes`   | Tiempo máximo de ejecución (por defecto 360).                        |
| `continue-on-error` | Permite que el workflow siga aunque el job falle.                    |
| `environment`       | Entorno de despliegue (con reglas de protección y secretos propios). |
| `outputs`           | Valores que el job expone a otros jobs.                              |
| `container`         | Ejecuta los steps dentro de un contenedor Docker.                    |
| `services`          | Contenedores auxiliares (ej. base de datos para tests).              |
| `uses`              | Llama a un **workflow reutilizable** en lugar de definir steps.      |

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
      - uses: actions/setup-node@v7
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
    uses: actions/checkout@v7

  # Usar una action con parámetros
  - name: Configurar Node
    uses: actions/setup-node@v7
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

| Clave               | Descripción                                 |
| ------------------- | ------------------------------------------- |
| `name`              | Nombre visible del paso.                    |
| `id`                | Identificador para referenciar sus outputs. |
| `uses`              | Action a utilizar.                          |
| `run`               | Comando(s) a ejecutar.                      |
| `with`              | Parámetros de entrada para la action.       |
| `env`               | Variables de entorno del paso.              |
| `if`                | Condición para ejecutar el paso.            |
| `shell`             | Shell a usar (`bash`, `pwsh`, `python`...). |
| `working-directory` | Directorio donde se ejecuta `run`.          |
| `continue-on-error` | Si falla, el job continúa.                  |
| `timeout-minutes`   | Tiempo máximo del paso.                     |

---

### 5. Actions

Una **action** es una aplicación **reutilizable** que realiza una tarea común (descargar código, instalar un lenguaje, subir archivos, desplegar...). Se usan con `uses` y se pueden encontrar en el [GitHub Marketplace](https://github.com/marketplace?type=actions).

```yaml
uses: <owner>/<repo>@<versión>
```

| Formato                         | Ejemplo                           |
| ------------------------------- | --------------------------------- |
| Action pública con tag          | `actions/checkout@v7`             |
| Fijada a un commit (más segura) | `actions/checkout@<sha-completo>` |
| Action local del repo           | `./.github/actions/mi-action`     |
| Imagen Docker                   | `docker://alpine:3.20`            |

#### Tipos de actions que puedes crear

- **JavaScript:** se ejecutan directamente en Node.js. Rápidas.
- **Docker container:** empaquetan su propio entorno.
- **Composite:** combinan varios steps en una sola action reutilizable.

#### Actions oficiales muy usadas

| Action                      | Para qué sirve                         |
| --------------------------- | -------------------------------------- |
| `actions/checkout`          | Clona el repositorio en el runner.     |
| `actions/setup-node`        | Instala Node.js.                       |
| `actions/setup-python`      | Instala Python.                        |
| `actions/cache`             | Cachea dependencias entre ejecuciones. |
| `actions/upload-artifact`   | Guarda archivos generados por un job.  |
| `actions/download-artifact` | Recupera archivos de otro job.         |

---

### 6. Runners

Un **runner** es el **servidor (máquina)** que ejecuta los jobs. Cada job se ejecuta en un runner nuevo.

#### GitHub-hosted runners

Máquinas virtuales gestionadas por GitHub. Se crean limpias para cada job y se destruyen al terminar.

| Etiqueta `runs-on` | Sistema operativo |
| ------------------ | ----------------- |
| `ubuntu-latest`    | Linux (Ubuntu)    |
| `windows-latest`   | Windows Server    |
| `macos-latest`     | macOS             |

También hay versiones específicas (`ubuntu-24.04`, `windows-2022`...) y **larger runners** con más CPU/RAM (de pago).

#### Self-hosted runners

Máquinas **propias** (servidor, VM, Raspberry Pi, cluster...) donde instalas el agente de runner de GitHub.

```yaml
runs-on: [self-hosted, linux, x64]
```

| Característica       | GitHub-hosted                | Self-hosted                         |
| -------------------- | ---------------------------- | ----------------------------------- |
| Mantenimiento        | Lo hace GitHub               | Lo haces tú                         |
| Entorno              | Limpio en cada job           | Persistente (hay que limpiarlo)     |
| Coste                | Minutos incluidos según plan | Gratis en GitHub, pagas tu hardware |
| Personalización      | Limitada                     | Total (hardware, software, red)     |
| Acceso a red interna | No                           | Sí                                  |

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

### Permissions

En cada ejecución GitHub genera automáticamente un token llamado **`GITHUB_TOKEN`**, que las actions usan para interactuar con la API del repositorio (clonar código, comentar en PRs, crear releases...).

La clave `permissions` define **qué puede hacer ese token**.

```yaml
permissions:
  contents: read      # El token solo puede LEER el código
```

**¿Por qué limitarlo?** Por el principio de **mínimo privilegio**: si una action de terceros fuera maliciosa o tuviera una vulnerabilidad, solo podría hacer lo que el token permita.

Valores posibles: `read`, `write` o `none`.

| Permiso         | Para qué sirve                                           |
| --------------- | -------------------------------------------------------- |
| `contents`      | Leer o escribir código, tags y releases.                 |
| `pull-requests` | Comentar o etiquetar Pull Requests.                      |
| `issues`        | Crear o editar issues.                                   |
| `packages`      | Publicar en GitHub Packages.                             |
| `id-token`      | Autenticarse en AWS/GCP/Azure sin guardar claves (OIDC). |
| `actions`       | Gestionar ejecuciones de workflows.                      |

> 💡 En cuanto declaras `permissions`, **todo lo que no listes queda en `none`**.

Se puede declarar a nivel de **workflow** y sobrescribir **por job**, para dar más permisos solo donde se necesitan:

```yaml
permissions:
  contents: read          # Por defecto, todo el workflow solo lee

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write     # Solo este job puede crear releases
    steps:
      - run: echo "Creando release..."
```

### Concurrency

Controla **cuántas ejecuciones de un mismo grupo pueden correr al mismo tiempo**.

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

| Clave                | Descripción                                                                              |
| -------------------- | ---------------------------------------------------------------------------------------- |
| `group`              | Nombre del grupo. Dos ejecuciones con el mismo nombre **no corren en paralelo**.         |
| `cancel-in-progress` | Si es `true`, una nueva ejecución **cancela** la que estaba corriendo en el mismo grupo. |

En el ejemplo, el grupo se construye con:

- `github.workflow` → nombre del workflow (ej. `CI/CD`).
- `github.ref` → rama o PR (ej. `refs/heads/main`, `refs/pull/42/merge`).

Resultado: `CI/CD-refs/heads/main`, es decir, **un grupo por workflow y por rama**. Un push a `feature-x` no cancela lo que corre en `main`.

**Ejemplo práctico:** haces 3 pushes seguidos a tu PR en 1 minuto.

| Sin `concurrency`                          | Con `concurrency` + `cancel-in-progress: true`    |
| ------------------------------------------ | ------------------------------------------------- |
| Corren las 3 ejecuciones completas.        | Se cancelan la 1.ª y la 2.ª; solo termina la 3.ª. |
| Se gastan minutos probando commits viejos. | Solo se prueba el último commit.                  |

#### `cancel-in-progress: false` (valor por defecto)

La nueva ejecución **espera en cola** a que termine la anterior. Es lo ideal para **despliegues**: no quieres cortar un deploy a la mitad, pero tampoco que corran dos a la vez.

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    concurrency:
      group: production
      cancel-in-progress: false   # Los deploys se ejecutan uno detrás de otro
    steps:
      - run: echo "Desplegando..."
```

> ⚠️ Solo puede haber **una** ejecución pendiente por grupo. Si llega una tercera mientras otra espera, la que estaba esperando se cancela.

**En resumen:**

- `permissions` → **seguridad**: qué puede hacer el workflow con tu repositorio.
- `concurrency` → **control de ejecución**: cuántas ejecuciones corren a la vez (ahorra minutos y evita choques).

### Contexts y expresiones

Un **context** (contexto) es un **objeto con información** sobre la ejecución: qué evento la disparó, quién la lanzó, qué inputs recibió, qué secretos hay, etc.

Una **expresión** `${{ ... }}` permite leer esa información, compararla o usar funciones con ella. La forma general es `${{ contexto.propiedad }}`:

```text
${{ github.actor }}
    │      └── propiedad: el usuario asociado a la ejecución
    └── contexto
```

Si la propiedad puede tener guiones o es dinámica, también se puede usar `${{ github['actor'] }}`.

#### Lista de contextos

| Context    | Contiene                                                   | Ejemplo                             |
| ---------- | ---------------------------------------------------------- | ----------------------------------- |
| `github`   | Info del evento, repo, rama, actor.                        | `${{ github.ref }}`                 |
| `env`      | Variables de entorno definidas en el workflow, job o step. | `${{ env.APP_ENV }}`                |
| `secrets`  | Secretos.                                                  | `${{ secrets.API_KEY }}`            |
| `vars`     | Variables de configuración.                                | `${{ vars.REGION }}`                |
| `inputs`   | Entradas de `workflow_dispatch` / `workflow_call`.         | `${{ inputs.name }}`                |
| `matrix`   | Valores de la matriz actual.                               | `${{ matrix.node }}`                |
| `strategy` | Info de la matriz (índice, total de jobs).                 | `${{ strategy.job-index }}`         |
| `needs`    | Outputs y resultados de jobs previos.                      | `${{ needs.build.result }}`         |
| `steps`    | Outputs y resultados de steps anteriores (por `id`).       | `${{ steps.ver.outputs.version }}`  |
| `job`      | Info del job actual.                                       | `${{ job.status }}`                 |
| `runner`   | Info del runner.                                           | `${{ runner.os }}`                  |
| `jobs`     | Outputs de los jobs. Solo en workflows reutilizables.      | `${{ jobs.build.outputs.version }}` |

#### Propiedades más usadas de `github`

| Propiedad           | Qué devuelve                                             | Ejemplo de valor            |
| ------------------- | -------------------------------------------------------- | --------------------------- |
| `github.event_name` | Nombre del evento que disparó el workflow.               | `push`, `schedule`          |
| `github.actor`      | Usuario asociado a la ejecución.                         | `octocat`                   |
| `github.repository` | Dueño y nombre del repositorio.                          | `octocat/hello-world`       |
| `github.ref`        | Referencia completa de la rama, tag o PR.                | `refs/heads/main`           |
| `github.ref_name`   | Nombre corto de la rama o tag.                           | `main`                      |
| `github.sha`        | Commit que disparó el workflow.                          | `1250101...`                |
| `github.workflow`   | Nombre del workflow.                                     | `Triggers`                  |
| `github.run_number` | Número de ejecución del workflow.                        | `15`                        |
| `github.event`      | Datos completos del evento. **Cambian según el evento.** | `github.event.issue.number` |

Por ejemplo, `github.event.pull_request.title` existe en `pull_request`, pero no en `push`.

#### Ejemplo: contextos usados en este repositorio

```yaml
# triggers.yml: decide qué job corre según el evento
if: ${{ github.event_name == 'workflow_dispatch' }}

# triggers.yml: lee un valor del formulario manual
env:
  INPUT_NAME: ${{ inputs.name }}
```

#### Contexto `env` o variable de shell

Son dos formas de leer el mismo valor, en momentos distintos:

```yaml
env:
  APP_ENV: production
steps:
  - run: echo "${{ env.APP_ENV }}"   # GitHub lo reemplaza ANTES de ejecutar el script
  - run: echo "$APP_ENV"             # El shell lo lee MIENTRAS ejecuta el script
```

Dentro de `run` es preferible `$APP_ENV`. El contexto `env` sirve donde no hay shell, como en el `if` de un step o en `with`.

#### Dónde se puede usar cada contexto

No todos los contextos están disponibles en todas partes:

| Lugar                                | Contextos disponibles                                     |
| ------------------------------------ | --------------------------------------------------------- |
| `run-name`, `concurrency` (workflow) | `github`, `inputs`, `vars`                                |
| `env` del workflow                   | `github`, `secrets`, `inputs`, `vars`                     |
| `if` de un **job**                   | `github`, `needs`, `vars`, `inputs`                       |
| `runs-on`                            | `github`, `needs`, `strategy`, `matrix`, `vars`, `inputs` |
| `env` de un job                      | Los de `runs-on` más `secrets`                            |
| `if` de un **step**                  | Todos, menos `secrets` y `jobs`                           |
| `run`, `with` y `env` de un step     | Todos, menos `jobs`                                       |

Para condicionar un step según un secreto, se pasa primero a `env` a nivel de job:

```yaml
jobs:
  notify:
    runs-on: ubuntu-latest
    env:
      API_KEY: ${{ secrets.API_KEY }}
    steps:
      - if: ${{ env.API_KEY != '' }}
        run: echo "El secreto existe"
```

#### Errores comunes

- **Propiedad inexistente:** no da error. Se muestra vacía y, al compararla con un número, vale `0`. Si el input se llama `age` y escribes `inputs.edad`, entonces `inputs.edad < 18` siempre es verdadero.
- **Comillas en las expresiones:** los textos van con comillas **simples**: `github.ref == 'refs/heads/main'`.
- **Inyección de comandos:** no pongas datos que escriben otras personas (títulos de PR, comentarios, inputs) directamente en `run`. Pásalos por `env`:

```yaml
# Inseguro
- run: echo "${{ github.event.pull_request.title }}"

# Seguro
- env:
    TITLE: ${{ github.event.pull_request.title }}
  run: echo "$TITLE"
```

#### Ver el contenido de un contexto

```yaml
- name: Mostrar el contexto github
  env:
    CONTEXT: ${{ toJSON(github) }}
  run: echo "$CONTEXT"
```

#### Funciones de estado

Útiles en `if`: `success()`, `failure()`, `always()`, `cancelled()`.

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
- uses: actions/upload-artifact@v7
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
        uses: actions/checkout@v7

      - name: Setup Node
        uses: actions/setup-node@v7
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
      - uses: actions/checkout@v7
      - uses: actions/setup-node@v7
        with:
          node-version: 22
          cache: npm
      - run: npm ci && npm run build
      - uses: actions/upload-artifact@v7
        with:
          name: dist
          path: dist/

  deploy:
    needs: build
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/download-artifact@v8
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

| Término      | Definición corta                                                    |
| ------------ | ------------------------------------------------------------------- |
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
