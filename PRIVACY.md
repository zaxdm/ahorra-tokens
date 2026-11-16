# Privacidad / Privacy

## Español

ahorra-tokens funciona solo en tu computadora.

- **Qué lee:** los archivos de `~/.claude`, que son tu `settings.json`, las carpetas de skills y plugins, los
  `CLAUDE.md` y el historial de sesiones (`~/.claude/projects/*.jsonl`). Del historial solo cuenta qué skills
  y conectores se usaron, cuántos tokens consumió cada pedido y qué herramientas cargó cada sesión. No
  lee archivos que guardan tokens o claves.
- **Qué escribe:** solo `~/.claude/settings.json`, cuando tú apruebas apagar o prender algo, y deja antes
  una copia `settings.json.bak`.
- **Qué envía:** nada. El script no se conecta a internet ni envía datos a ningún servicio. El resumen que ves
  lo muestra Claude Code en tu sesión, como cualquier otra respuesta.
- **Qué guarda:** nada fuera de tu PC. No hay servidor, cuentas ni analítica.

Contacto: stebandioses@gmail.com

## English

ahorra-tokens runs only on your computer.

- **Reads:** files under `~/.claude` (your `settings.json`, skill and plugin folders, `CLAUDE.md` files and session
  history `~/.claude/projects/*.jsonl`). From the history it only counts which skills and connectors were used,
  the tokens of each request and the tools each session loaded. It does not read files that store tokens or keys.
- **Writes:** only `~/.claude/settings.json`, when you approve turning something off or on, after saving a
  `settings.json.bak` copy.
- **Sends:** nothing. The script makes no network connections and sends no data to any service.
- **Stores:** nothing outside your computer. No server, accounts or analytics.

Contact: stebandioses@gmail.com
