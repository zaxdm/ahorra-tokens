# ahorra-tokens

Plugin de Claude Code que mide en qué se van tus tokens y apaga lo que no usas.

Cada sesión de Claude Code arranca cargando las descripciones de todas tus skills, las herramientas de
tus conectores y tus CLAUDE.md, los uses o no. `/ahorrar-tokens` lee tus transcripciones de los últimos
30 días y te dice:

- con cuántos tokens arranca tu sesión típica;
- qué skills, plugins y conectores no usaste, y cuánto pesan;
- qué CLAUDE.md son demasiado largos.

Después te pregunta qué apagar y lo apaga en `~/.claude/settings.json`, dejando una copia `.bak`.

## Instalar

Dentro de Claude Code:

```
/plugin marketplace add <usuario>/ahorra-tokens
/plugin install ahorra-tokens@ahorra-tokens
```

Abre una sesión nueva y escribe `/ahorra-tokens:ahorrar-tokens`, o dile a Claude «gasto muchos tokens». Necesita Python 3.8 o más reciente; solo usa la librería estándar.

## Sin Claude

El script también se puede correr directamente:

```
python skills/ahorrar-tokens/scripts/analizar.py informe --dias 30
python skills/ahorrar-tokens/scripts/analizar.py apagar --skill nombre --plugin nombre@mercado
python skills/ahorrar-tokens/scripts/analizar.py prender --skill nombre
python skills/ahorrar-tokens/scripts/analizar.py compactar 400000
```

## El chat de claude.ai

El chat de claude.ai (la web y la app) no se configura con archivos. Los pasos para hacerlo a mano están
en [guia/claude-ai.md](guia/claude-ai.md).

## ¿Prefieres que lo hagamos por ti?

El plugin es gratis y puedes compartirlo. Si quieres que te lo dejemos configurado, también lo hacemos:

- revisamos tu Claude Code y tu cuenta de claude.ai (conectores, skills, proyectos);
- recortamos tus CLAUDE.md y las instrucciones de tus proyectos sin que pierdan lo importante;
- para equipos y academias, dejamos la misma configuración en todas las PC y cuentas.

Contacto: PENDIENTE

## Privacidad

Todo se hace en tu PC. El script lee `~/.claude` y `~/.claude.json`, solo escribe en
`~/.claude/settings.json` y no se conecta a internet.
