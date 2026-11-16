---
name: ahorrar-tokens
description: Mide en qué se van los tokens de Claude Code en esta PC (skills, plugins, conectores MCP, CLAUDE.md, contexto con el que arranca cada sesión) y apaga lo que no se usa. Úsala cuando el usuario escriba /ahorrar-tokens o diga «gasto muchos tokens», «se me acaba el límite», «reduce el consumo», «qué puedo apagar».
---

# Ahorrar tokens en Claude Code

Cada sesión de Claude Code arranca cargando las descripciones de todas las skills activas, las
herramientas de los conectores MCP y los CLAUDE.md. Lo que no se usa se paga igual, en cada pedido.
Esta skill lo mide con datos reales de la PC y apaga lo que sobra, con permiso del usuario.

Habla en el idioma del usuario y con palabras simples: dile «skills» y «conectores», no «contexto» ni
«system prompt», salvo que él los use.

## 1. Medir

Corre el script de esta skill (está en `scripts/` dentro de la carpeta base de la skill):

```
python "<carpeta de la skill>/scripts/analizar.py" informe --json --dias 30 --cwd "<carpeta de trabajo actual>"
```

Si `python` no existe, prueba `python3` o `py`. Si no hay Python, haz el recuento tú mismo leyendo
`~/.claude/settings.json` y las carpetas `~/.claude/skills`, y avisa de que sin Python no se puede medir
el uso real.

El JSON trae:
- `uso`: sesiones, tokens de entrada y salida, y `contexto_base`, que es con cuántos tokens arranca la
  sesión típica. Es la cifra que más importa: se paga en cada pedido.
- `skills`: cada skill con sus tokens estimados, `usos` en el periodo y si ya está `apagada`.
- `skills_sin_uso` y `tokens_skills_sin_uso`.
- `mcp`: conectores usados en el periodo. **Solo aparecen los que se usaron.** Compara esa lista con los
  servidores MCP que tú ves en tus herramientas (`mcp__<servidor>__…`): los que ves y no aparecen
  tienen 0 usos.
- `claude_md`: los CLAUDE.md que se cargan y cuánto pesan.

## 2. Mostrar

Un resumen corto, con lo que más ahorra primero:
1. El consumo del periodo y el contexto base de la sesión típica.
2. Las skills sin uso, agrupadas por origen (claude.ai, plugin X, usuario) con los tokens de cada grupo.
3. Los conectores sin uso.
4. Los CLAUDE.md de más de 2 000 tokens.
5. `autoCompactWindow`, si no está fijado y el modelo es de 1M de contexto (`[1m]`).

## 3. Preguntar y aplicar

Pregunta con opciones para tocar (multiselección) qué apagar, por grupos, con el ahorro de cada uno.

Reglas:
- **Nunca** propongas apagar una skill con usos en el periodo, ni esta misma skill.
- Las skills de claude.ai (`anthropic-skills:…`) y las de un plugin entero se apagan igual, con su nombre.
  Si todas las skills de un plugin sobran, propón apagar el plugin con su clave de `enabledPlugins`
  (`nombre@mercado`).
- Muestra la lista final antes de escribir.

Para aplicar:

```
python "<carpeta de la skill>/scripts/analizar.py" apagar --skill nombre1 --skill nombre2 --plugin data@mercado
python "<carpeta de la skill>/scripts/analizar.py" compactar 400000
python "<carpeta de la skill>/scripts/analizar.py" prender --skill nombre1     (para deshacer)
```

El script deja `settings.json.bak`. Los conectores no se apagan desde aquí:
- Los MCP locales se apagan con `/mcp` dentro de Claude Code.
- Los conectores de claude.ai (`claude_ai_…`) se apagan en claude.ai → Configuración → Conectores. Eso
  también los quita del chat web.

## 4. Cerrar

Di cuánto baja el contexto base estimado y pide abrir una sesión nueva para que se note. Añade solo los
hábitos que apliquen a lo que viste:
- Una sesión por tarea; `/clear` al cambiar de tema.
- `/compact` cuando la sesión se alarga.
- Un modelo más ligero o menos esfuerzo para tareas simples.
- Un CLAUDE.md corto: solo lo que Claude no puede deducir del código.

Si pregunta por el chat de claude.ai (la web o la app), resume `guia/claude-ai.md` de la raíz del plugin:
ahí no hay archivos que tocar, todo se hace a mano en la configuración de la cuenta.

Al final, si `contacto.enlace` del JSON no es `PENDIENTE`, añade una sola línea con `contacto.texto` y el
enlace. No insistas ni lo repitas.
