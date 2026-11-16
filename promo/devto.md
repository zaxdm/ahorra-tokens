---
title: Mi Claude Code cargaba 65 000 tokens antes de que yo escribiera nada
published: false
tags: claude, ai, productivity, spanish
cover_image:
---

Cada vez que le escribes a Claude Code, antes de leer tu mensaje carga todo lo que tienes instalado: la
descripción de cada skill, las herramientas de cada conector MCP y tus CLAUDE.md. Lo carga aunque no lo
uses, y lo paga cada pedido. Yo no tenía idea de cuánto era hasta que lo medí.

## Cómo lo medí

Claude Code guarda cada sesión en `~/.claude/projects/<carpeta>/<sesión>.jsonl`. Ahí hay dos cosas que
sirven:

1. **El consumo real de cada respuesta.** Cada mensaje del asistente trae `usage` con `input_tokens`,
   `cache_creation_input_tokens` y `cache_read_input_tokens`. La suma del primer pedido de una sesión es
   con cuánto contexto arranca, antes de hacer nada.
2. **Qué se usó.** Los bloques `tool_use` dicen qué skill se llamó (`Skill` con `input.skill`) y qué
   conector (`mcp__<servidor>__<herramienta>`). Y los adjuntos `deferred_tools_delta` dicen qué
   herramientas cargó la sesión, se usaran o no.

Cruzando lo cargado con lo usado en 30 días, en mi PC salió esto:

- 126 sesiones, unos 1 300 millones de tokens de entrada.
- La sesión típica arrancaba con **unos 65 000 tokens**.
- **46 skills** que no usé ni una vez en 30 días (unos 6 500 tokens por sesión).
- **14 conectores** cargados sin uso. El que más pesaba tenía 45 herramientas.
- Un plugin que yo había apagado en `settings.json` y cuyos conectores **seguían cargando**.

## La trampa: skills que no llamas, pero se usan

Mi primer intento proponía apagar un humanizador que nunca llamé con `/`. Error: otra skill que uso
todos los días lo lee por dentro, y el historial no lo registra. Ahora el script revisa si una skill en
uso nombra a otra en sus archivos (en cadena) y no propone apagar esas.

## Lo convertí en un plugin

[ahorra-tokens](https://github.com/zaxdm/ahorra-tokens) hace esa medición con tus datos y te pregunta qué
apagar. No apaga nada sin preguntar y deja `settings.json.bak`. Es gratis (MIT), en español, solo usa la
librería estándar de Python y no se conecta a internet. El plugin mismo pesa unos 170 tokens por sesión.

```
/plugin marketplace add zaxdm/ahorra-tokens
/plugin install ahorra-tokens@ahorra-tokens
```

Abre una sesión nueva y escribe `/ahorra-tokens:ahorrar-tokens`.

## Lo que más ahorra, con o sin plugin

- **Apaga skills sin uso** con `skillOverrides` en `~/.claude/settings.json`:
  `"skillOverrides": { "nombre-de-la-skill": "off" }`.
- **Desinstala, no solo apagues**, los plugins que no usas: apagados pueden seguir cargando sus conectores.
- **Quita conectores que no usas.** Los de claude.ai se van en claude.ai → Configuración → Conectores;
  ojo, también desaparecen del chat web.
- **CLAUDE.md corto**: solo lo que Claude no puede deducir del código. Se carga completo en cada sesión.
- **Una sesión por tarea** y `/clear` al cambiar de tema: cada mensaje arrastra todo lo anterior.
- Con un modelo de 1M de contexto, `autoCompactWindow` en `settings.json` hace que resuma antes.

En mi caso, entre skills y conectores, el arranque baja unos 11 000 tokens (cerca del 17 %) en cada
sesión, sin perder nada de lo que uso.

Si lo pruebas, cuéntame cuánto te salió. Y si prefieres que alguien te lo deje configurado (Claude Code y
la cuenta de claude.ai, para ti o tu equipo), escríbeme: stebandioses@gmail.com.
