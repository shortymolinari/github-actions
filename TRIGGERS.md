# Explicación de `triggers.yml`

Este documento explica el workflow [`.github/workflows/triggers.yml`](.github/workflows/triggers.yml).

Su objetivo es practicar **las distintas formas de disparar un workflow** (los *triggers*) y elegir qué job se ejecuta según el evento.

## Contenido

- [Vista general](#vista-general)
- [Nombre del workflow](#nombre-del-workflow)
- [Los triggers (`on`)](#los-triggers-on)
- [Los jobs](#los-jobs)
- [Ejemplos: qué pasa si...](#ejemplos-qué-pasa-si)
- [Cómo probarlo](#cómo-probarlo)

---

## Vista general

```text
push a main ───────────────────┐
pull_request (cambia un .py) ──┤
issues (se agrega etiqueta) ───┼──► job "hello-world"        ──► hello_world.py
schedule (22:15 UTC) ──────────┘

workflow_dispatch (manual) ────────► job "hello-world-manual" ──► hello_language.py
```

Basta con que ocurra **uno** de los eventos para que el workflow se dispare. En cada ejecución corre **un solo job**; el otro aparece como *skipped* (omitido).

---

## Nombre del workflow

```yaml
name: Triggers
run-name: I'm learning to use different triggers!
```

- **`name`**: nombre del workflow en la pestaña **Actions**.
- **`run-name`**: título de cada ejecución.

---

## Los triggers (`on`)

La clave `on` define qué eventos disparan el workflow.

### `push`

```yaml
push:
  branches:
    - main
```

Se dispara al hacer push a `main`. Un push a cualquier otra rama no lo activa por este evento. Un merge a `main` también cuenta como push.

### `pull_request`

```yaml
pull_request:
  types: [opened, synchronize, reopened]
  paths:
    - '**.py'
```

Deben cumplirse **las dos condiciones**:

1. Que ocurra una de estas actividades:
   - `opened`: se abre el PR.
   - `synchronize`: se suben nuevos commits al PR.
   - `reopened`: se reabre un PR cerrado.
2. Que el PR cambie **al menos un archivo `.py`**, en cualquier carpeta.

Un PR que solo cambia `README.md`, por ejemplo, no lo dispara.

### `issues`

```yaml
issues:
  types:
    - labeled
```

Se dispara cuando se **agrega una etiqueta** a un issue. Si agregas dos etiquetas, hay dos ejecuciones. Crear o cerrar un issue no lo activa, y etiquetar un PR tampoco.

### `workflow_dispatch`

```yaml
workflow_dispatch:
  inputs:
    favorite_language:
      description: 'Favorite language'
      default: Python
      required: true
      type: choice
      options:
        - Python
        - JavaScript
        - Go
    name:
      description: 'Edwin'
      required: true
      default: Juan
      type: string
```

Permite lanzarlo **manualmente** y muestra un formulario con estos campos:

| Input               | Tipo     | Valor por defecto | Qué es                                            |
| ------------------- | -------- | ----------------- | ------------------------------------------------- |
| `favorite_language` | `choice` | `Python`          | Lista desplegable: `Python`, `JavaScript` o `Go`. |
| `name`              | `string` | `Juan`            | Texto libre.                                      |

- **`description`** es la etiqueta que se ve en el formulario. En `name` dice `Edwin`; algo como `Your name` sería más claro.
- **`required: true`** hace que el campo sea obligatorio.
- Los valores se leen con `${{ inputs.<nombre> }}`.

### `schedule`

```yaml
schedule:
  - cron: '15 22 * * *'
```

Se dispara **todos los días a las 22:15 UTC**. El cron se lee así:

| Campo            | Valor | Significado |
| ---------------- | ----- | ----------- |
| Minuto           | `15`  | Minuto 15   |
| Hora             | `22`  | 22 h (UTC)  |
| Día del mes      | `*`   | Todos       |
| Mes              | `*`   | Todos       |
| Día de la semana | `*`   | Todos       |

La hora es UTC. En una zona UTC-5, por ejemplo, son las 17:15. GitHub puede retrasar la ejecución si tiene mucha carga.

> ⚠️ `schedule` e `issues` solo funcionan si el archivo está en la rama por defecto (`main`). Lo mismo ocurre con el botón manual de `workflow_dispatch`.

---

## Los jobs

Cada job tiene un `if` que revisa `github.event_name`, es decir, **qué evento disparó el workflow**. Las condiciones son opuestas, por eso nunca corren los dos.

| Job                  | Condición                                   | Script              |
| -------------------- | ------------------------------------------- | ------------------- |
| `hello-world-manual` | `github.event_name == 'workflow_dispatch'`  | `hello_language.py` |
| `hello-world`        | `github.event_name != 'workflow_dispatch'`  | `hello_world.py`    |

Ambos usan `runs-on: ubuntu-latest`, una máquina Linux nueva que proporciona GitHub.

### Job `hello-world-manual`

```yaml
hello-world-manual:
  if: ${{ github.event_name == 'workflow_dispatch' }}
  runs-on: ubuntu-latest
  steps:
    - name: Checkout
      uses: actions/checkout@v7
    - name: Set name
      env:
        INPUT_NAME: ${{ inputs.name }}
      run: echo "USERNAME=$INPUT_NAME" >> "$GITHUB_ENV"
    - name: Set language
      env:
        INPUT_LANGUAGE: ${{ inputs.favorite_language }}
      run: echo "LANGUAGE=$INPUT_LANGUAGE" >> "$GITHUB_ENV"
    - name: Run script
      run: python hello_language.py
```

1. **Checkout**: descarga el código del repositorio en el runner. Sin este paso, el script no existiría en la máquina.
2. **Set name**: guarda el nombre del formulario en la variable `USERNAME`.
3. **Set language**: guarda el lenguaje elegido en la variable `LANGUAGE`.
4. **Run script**: ejecuta `hello_language.py`, que lee ambas variables.

Resultado con los valores por defecto:

```text
Hello, Juan from GitHub! Your favorite language is Python.
```

#### ¿Qué es `$GITHUB_ENV`?

Cada paso `run` se ejecuta en un proceso distinto, así que una variable normal de shell se pierde al terminar el paso. Al escribir `NOMBRE=valor` en el archivo `$GITHUB_ENV`, la variable queda disponible en **los pasos siguientes del mismo job**, pero no en el paso que la escribe.

#### ¿Por qué se usa `env` con los inputs?

GitHub reemplaza `${{ ... }}` por su valor **antes** de ejecutar el script. Si el input se pusiera directamente en `run`, alguien podría escribir comandos en el formulario y se ejecutarían:

```yaml
# Inseguro: el texto pasa a ser parte del script
run: echo "USERNAME=${{ inputs.name }}" >> $GITHUB_ENV

# Seguro: el texto llega como una variable
env:
  INPUT_NAME: ${{ inputs.name }}
run: echo "USERNAME=$INPUT_NAME" >> "$GITHUB_ENV"
```

### Job `hello-world`

```yaml
hello-world:
  if: ${{ github.event_name != 'workflow_dispatch' }}
  runs-on: ubuntu-latest
  steps:
    - name: Checkout
      uses: actions/checkout@v7
    - name: Set variable
      run: echo "USERNAME=${{ github.actor }}" >> $GITHUB_ENV
    - name: Run script
      run: python hello_world.py
```

1. **Checkout**: descarga el código.
2. **Set variable**: guarda en `USERNAME` el valor de `github.actor`, el usuario de GitHub asociado a la ejecución. Aquí no se usan inputs porque solo existen en la ejecución manual.
3. **Run script**: ejecuta `hello_world.py`.

Resultado si el usuario es `octocat`:

```text
Hello, octocat from GitHub!
```

---

## Ejemplos: qué pasa si...

| Acción                                        | ¿Se dispara? | Job que corre        |
| --------------------------------------------- | ------------ | -------------------- |
| Haces push a `main`                           | Sí           | `hello-world`        |
| Haces push a otra rama sin PR abierto         | No           | Ninguno              |
| Abres un PR que cambia `hello_world.py`       | Sí           | `hello-world`        |
| Abres un PR que solo cambia `README.md`       | No           | Ninguno              |
| Subes commits a un PR que cambia un `.py`     | Sí           | `hello-world`        |
| Agregas una etiqueta a un issue               | Sí           | `hello-world`        |
| Creas un issue sin etiquetas                  | No           | Ninguno              |
| Llegan las 22:15 UTC                          | Sí           | `hello-world`        |
| Lo lanzas con **Run workflow**                | Sí           | `hello-world-manual` |

---

## Cómo probarlo

**Desde la web:**

1. Asegúrate de que `triggers.yml` y los dos scripts estén en `main`.
2. Abre la pestaña **Actions** y elige **Triggers**.
3. Pulsa **Run workflow**, completa los campos y confirma.

**Desde la terminal, con GitHub CLI:**

```bash
gh workflow run triggers.yml -f name=Juan -f favorite_language=Go
gh run list --workflow=triggers.yml
```
