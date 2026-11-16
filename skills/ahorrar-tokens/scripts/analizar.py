r"""Mide en qué se van los tokens de Claude Code en esta PC y apaga lo que no se usa.

    python analizar.py informe [--dias 30] [--json]     qué hay instalado, cuánto pesa y cuánto se usa
    python analizar.py apagar --skill X [--plugin Y]    apaga skills o plugins en ~/.claude/settings.json
    python analizar.py prender --skill X                vuelve a prender una skill apagada
    python analizar.py compactar 500000                 fija autoCompactWindow

Solo usa la librería estándar de Python. Lee ~/.claude (settings, skills, plugins, transcripciones) y
~/.claude.json (servidores MCP); solo escribe en ~/.claude/settings.json, con copia .bak antes.
Los tokens de las descripciones son una estimación (caracteres / 4).
"""
import argparse
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

CLAUDE = Path.home() / ".claude"
SETTINGS = CLAUDE / "settings.json"
CLAUDE_JSON = Path.home() / ".claude.json"
CONTACTO = Path(__file__).resolve().parent.parent / "contacto.json"


def leer_json(f: Path) -> dict:
    try:
        return json.loads(f.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}


def tokens(texto: str) -> int:
    return round(len(texto) / 4)


def frontmatter(f: Path) -> dict:
    try:
        t = f.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    m = re.match(r"---\s*\n(.*?)\n---", t, re.S)
    if not m:
        return {}
    d, clave = {}, None
    for linea in m.group(1).splitlines():
        k = re.match(r"([A-Za-z_-]+):\s*(.*)", linea)
        if k:
            clave = k.group(1)
            d[clave] = k.group(2).strip().strip("\"'")
        elif clave and linea.startswith((" ", "\t")):
            d[clave] += " " + linea.strip()
    return d


# --- inventario -------------------------------------------------------------------------------

def datos_plugin(raiz: Path) -> tuple:
    """(nombre, clave para enabledPlugins) de la carpeta de un plugin."""
    nombre = leer_json(raiz / ".claude-plugin" / "plugin.json").get("name") or raiz.name.split("~")[0]
    meta = leer_json(raiz.with_name(raiz.name + ".meta.json"))
    mercado = meta.get("marketplace_name")
    if not mercado and "cache" in raiz.parts:  # plugins/cache/<marketplace>/<plugin>/<versión>
        partes = raiz.parts[raiz.parts.index("cache") + 1:]
        mercado = partes[0] if partes else None
    return nombre, f"{nombre}@{mercado}" if mercado else nombre


def skills_instaladas(cwd: Path) -> list:
    """(nombre, origen, tokens de la descripción). El nombre es el que se usa en skillOverrides."""
    vistas = {}

    def agregar(f: Path, prefijo: str, origen: str, plugin=None):
        fm = frontmatter(f)
        nombre = prefijo + (fm.get("name") or f.parent.name)
        desc = fm.get("description", "")
        if nombre not in vistas:
            vistas[nombre] = {"nombre": nombre, "origen": origen, "plugin": plugin, "tokens": tokens(nombre + desc)}

    for f in sorted((CLAUDE / "skills").glob("*/SKILL.md")):
        agregar(f, "", "usuario")
    for f in sorted((CLAUDE / "skills" / "synced").glob("*/*/SKILL.md")):
        agregar(f, "anthropic-skills:", "claude.ai")
    for f in sorted((cwd / ".claude" / "skills").glob("*/SKILL.md")):
        agregar(f, "", "proyecto")
    for f in sorted((CLAUDE / "plugins").rglob("skills/*/SKILL.md")):
        if ".staging" in f.parts:
            continue
        nombre, clave = datos_plugin(f.parent.parent.parent)
        agregar(f, f"{nombre}:", f"plugin {nombre}", clave)
    return sorted(vistas.values(), key=lambda s: -s["tokens"])


def servidores_mcp(cwd: Path) -> dict:
    """nombre -> dónde está configurado (solo los locales; los conectores de claude.ai salen del uso)."""
    c = leer_json(CLAUDE_JSON)
    d = {n: "global" for n in c.get("mcpServers", {})}
    for ruta, p in c.get("projects", {}).items():
        for n in p.get("mcpServers", {}):
            d.setdefault(n, f"proyecto {Path(ruta).name}")
    for n in leer_json(cwd / ".mcp.json").get("mcpServers", {}):
        d.setdefault(n, "proyecto (.mcp.json)")
    return d


def claude_md(cwd: Path) -> list:
    archivos = [CLAUDE / "CLAUDE.md"]
    for carpeta in [cwd, *cwd.parents]:
        archivos += [carpeta / "CLAUDE.md", carpeta / ".claude" / "CLAUDE.md"]
    vistos, res = set(), []
    for f in archivos:
        if f.is_file() and f.resolve() not in vistos:
            vistos.add(f.resolve())
            res.append({"archivo": str(f), "tokens": tokens(f.read_text(encoding="utf-8", errors="replace"))})
    return res


# --- uso, desde las transcripciones -----------------------------------------------------------

def uso(dias: int) -> dict:
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    skills, mcp = Counter(), Counter()
    vistas = set()
    sesiones = defaultdict(lambda: {"entrada": 0, "salida": 0, "base": None, "pedidos": 0})
    for f in (CLAUDE / "projects").glob("*/*.jsonl"):
        if datetime.fromtimestamp(f.stat().st_mtime, timezone.utc) < desde:
            continue
        try:
            lineas = f.open(encoding="utf-8", errors="replace")
        except OSError:
            continue
        with lineas:
            for linea in lineas:
                if '"assistant"' not in linea:
                    continue
                try:
                    d = json.loads(linea)
                except ValueError:
                    continue
                m = d.get("message")
                if d.get("type") != "assistant" or not isinstance(m, dict):
                    continue
                try:
                    if datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")) < desde:
                        continue
                except (KeyError, ValueError):
                    pass
                for b in m.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        nombre = b.get("name", "")
                        if nombre == "Skill":
                            skills[(b.get("input") or {}).get("skill", "?")] += 1
                        elif nombre.startswith("mcp__"):
                            mcp[nombre.split("__")[1]] += 1
                clave = d.get("requestId") or m.get("id")
                u = m.get("usage")
                if not u or clave in vistas:
                    continue
                vistas.add(clave)
                s = sesiones[d.get("sessionId", f.stem)]
                entrada = (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                           + u.get("cache_read_input_tokens", 0))
                s["entrada"] += entrada
                s["salida"] += u.get("output_tokens", 0)
                s["pedidos"] += 1
                if s["base"] is None and not d.get("isSidechain"):
                    s["base"] = entrada
    bases = sorted(s["base"] for s in sesiones.values() if s["base"])
    return {
        "dias": dias,
        "sesiones": len(sesiones),
        "pedidos": sum(s["pedidos"] for s in sesiones.values()),
        "entrada": sum(s["entrada"] for s in sesiones.values()),
        "salida": sum(s["salida"] for s in sesiones.values()),
        "contexto_base": bases[len(bases) // 2] if bases else None,
        "skills": dict(skills),
        "mcp": dict(mcp),
    }


# --- informe ----------------------------------------------------------------------------------

def informe(dias: int, cwd: Path) -> dict:
    s = leer_json(SETTINGS)
    apagadas = {k for k, v in s.get("skillOverrides", {}).items() if v == "off"}
    plugins_off = {k for k, v in s.get("enabledPlugins", {}).items() if v is False}
    u = uso(dias)
    skills = skills_instaladas(cwd)
    for sk in skills:
        corto = sk["nombre"].split(":")[-1]
        sk["apagada"] = bool({sk["nombre"], corto} & apagadas) or bool(
            sk["plugin"] and sk["plugin"].split("@")[0] in {p.split("@")[0] for p in plugins_off})
        sk["usos"] = u["skills"].get(sk["nombre"], 0) + (u["skills"].get(corto, 0) if corto != sk["nombre"] else 0)
    sin_uso = [sk for sk in skills if not sk["apagada"] and not sk["usos"]]
    locales = servidores_mcp(cwd)
    mcp = [{"nombre": n, "donde": locales.get(n, "conector de claude.ai" if n.startswith("claude_ai_") else "plugin o integrado"),
            "usos": u["mcp"].get(n, 0)} for n in sorted(set(locales) | set(u["mcp"]))]
    return {
        "uso": u,
        "ajustes": {"model": s.get("model"), "autoCompactWindow": s.get("autoCompactWindow"),
                    "plugins_apagados": sorted(plugins_off)},
        "skills": skills,
        "skills_sin_uso": [sk["nombre"] for sk in sin_uso],
        "tokens_skills_sin_uso": sum(sk["tokens"] for sk in sin_uso),
        "mcp": mcp,
        "claude_md": claude_md(cwd),
        "contacto": leer_json(CONTACTO),
    }


def miles(n):
    return "—" if n is None else f"{n:,}".replace(",", " ")


def imprimir(r: dict):
    u = r["uso"]
    print(f"== Consumo de los últimos {u['dias']} días ==")
    print(f"  sesiones {u['sesiones']}, pedidos al modelo {miles(u['pedidos'])}")
    print(f"  tokens de entrada {miles(u['entrada'])}   de salida {miles(u['salida'])}")
    print(f"  contexto con el que arranca cada sesión (mediana): {miles(u['contexto_base'])} tokens")
    a = r["ajustes"]
    print("\n== Ajustes ==")
    print(f"  modelo {a['model'] or '(el de la cuenta)'}   autoCompactWindow {a['autoCompactWindow'] or '(sin fijar)'}")
    print(f"  plugins apagados: {', '.join(a['plugins_apagados']) or 'ninguno'}")
    print("\n== Skills (las descripciones van en cada sesión) ==")
    for sk in r["skills"]:
        estado = "apagada" if sk["apagada"] else (f"{sk['usos']} usos" if sk["usos"] else "SIN USO")
        print(f"  {sk['tokens']:>5} tok  {estado:>9}  {sk['nombre']}  [{sk['origen']}]")
    print(f"\n  {len(r['skills_sin_uso'])} skills sin uso en {u['dias']} días; apagarlas ahorra ~{miles(r['tokens_skills_sin_uso'])} tokens por sesión")
    print("\n== Servidores MCP y conectores ==")
    for m in r["mcp"]:
        print(f"  {m['usos']:>5} usos  {m['nombre']}  [{m['donde']}]")
    print("\n== CLAUDE.md (van completos en cada sesión) ==")
    for c in r["claude_md"] or [{"archivo": "(ninguno)", "tokens": 0}]:
        print(f"  {c['tokens']:>5} tok  {c['archivo']}")
    c = r["contacto"]
    if c.get("enlace") and c["enlace"] != "PENDIENTE":
        print(f"\n{c['texto']}\n  {c['enlace']}")


# --- cambios ----------------------------------------------------------------------------------

def guardar_settings(s: dict):
    if SETTINGS.exists():
        shutil.copy2(SETTINGS, SETTINGS.with_name("settings.json.bak"))
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="accion", required=True)
    i = sub.add_parser("informe")
    i.add_argument("--dias", type=int, default=30)
    i.add_argument("--json", action="store_true")
    i.add_argument("--cwd", default=".")
    for nombre in ("apagar", "prender"):
        p = sub.add_parser(nombre)
        p.add_argument("--skill", action="append", default=[])
        p.add_argument("--plugin", action="append", default=[])
    c = sub.add_parser("compactar")
    c.add_argument("tokens", type=int)
    a = ap.parse_args()

    if a.accion == "informe":
        r = informe(a.dias, Path(a.cwd).resolve())
        print(json.dumps(r, indent=2, ensure_ascii=False)) if a.json else imprimir(r)
        return
    s = leer_json(SETTINGS)
    if a.accion == "compactar":
        s["autoCompactWindow"] = a.tokens
    else:
        apagar = a.accion == "apagar"
        for sk in a.skill:
            if apagar:
                s.setdefault("skillOverrides", {})[sk] = "off"
            else:
                s.get("skillOverrides", {}).pop(sk, None)
        for p in a.plugin:
            s.setdefault("enabledPlugins", {})[p] = not apagar
    guardar_settings(s)
    print(f"Guardado en {SETTINGS} (copia en settings.json.bak). Abre una sesión nueva de Claude Code.")


if __name__ == "__main__":
    main()
