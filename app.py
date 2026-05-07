import json
import math
import os
import random
from copy import deepcopy
from datetime import datetime

import streamlit as st

SAVE_FILE = "save_barco_maldito.json"
GAME_VERSION = "1.0.0"

RARITIES = {
    "comun": {"label": "Común", "weight": 58, "mult": 1.00, "icon": "○", "color": "#9ca3af"},
    "poco_comun": {"label": "Poco común", "weight": 25, "mult": 1.25, "icon": "◇", "color": "#22c55e"},
    "raro": {"label": "Raro", "weight": 12, "mult": 1.65, "icon": "◆", "color": "#3b82f6"},
    "epico": {"label": "Épico", "weight": 4, "mult": 2.25, "icon": "✦", "color": "#a855f7"},
    "legendario": {"label": "Legendario", "weight": 1, "mult": 3.25, "icon": "✹", "color": "#f97316"},
}

RESOURCE_INFO = {
    "oro": {"label": "Oro", "rarity": "comun"},
    "madera": {"label": "Madera", "rarity": "comun"},
    "metal": {"label": "Metal", "rarity": "poco_comun"},
    "cristales": {"label": "Cristales", "rarity": "raro"},
    "combustible": {"label": "Combustible", "rarity": "poco_comun"},
    "reputacion": {"label": "Reputación", "rarity": "raro"},
    "fragmentos_antiguos": {"label": "Fragmentos antiguos", "rarity": "epico"},
    "perlas_negras": {"label": "Perlas negras", "rarity": "legendario"},
}

BASE_RESOURCES = {
    "oro": 120,
    "madera": 40,
    "metal": 15,
    "cristales": 0,
    "combustible": 12,
    "reputacion": 0,
    "fragmentos_antiguos": 0,
    "perlas_negras": 0,
}

BASE_SHIP = {
    "name": "La Gaviota Negra",
    "level": 1,
    "xp": 0,
    "max_hp": 100,
    "damage": 14,
    "defense": 4,
    "speed": 9,
    "radar": 3,
    "luck": 2,
    "crit": 6,
    "cargo": 30,
    "morale": 70,
    "communication": 2,
}

PORTS = {
    "puerto_bruma": {
        "name": "Puerto Bruma",
        "subtitle": "Zona inicial",
        "desc": "Aguas grises, piratas débiles y ruinas menores. Ideal para farmear oro y madera.",
        "difficulty": 1.0,
        "length": 8,
        "unlock": {"reputacion": 0},
        "affinity": ["oro", "madera", "combustible"],
        "boss": "Capitán Soga Mojada",
        "map_style": "Costa rota",
        "room_bias": {"combate": 28, "evento": 18, "tesoro": 12, "tienda": 10, "santuario": 7, "tormenta": 8, "ruinas": 6, "npc": 5, "descanso": 4, "trampa": 2},
    },
    "bahia_escama": {
        "name": "Bahía Escama",
        "subtitle": "Monstruos marinos",
        "desc": "Mar lleno de bestias. Más metal, más daño recibido y mejores reliquias defensivas.",
        "difficulty": 1.35,
        "length": 10,
        "unlock": {"reputacion": 8},
        "affinity": ["metal", "cristales", "madera"],
        "boss": "Leviatán Joven",
        "map_style": "Arrecifes vivos",
        "room_bias": {"combate": 30, "elite": 8, "evento": 14, "tesoro": 10, "tienda": 8, "santuario": 6, "tormenta": 9, "ruinas": 7, "npc": 4, "descanso": 3, "trampa": 1},
    },
    "islas_neblina": {
        "name": "Islas de Neblina",
        "subtitle": "Eventos raros",
        "desc": "Rutas engañosas con NPC, trampas y secretos. Buen lugar para fragmentos antiguos.",
        "difficulty": 1.75,
        "length": 12,
        "unlock": {"reputacion": 22},
        "affinity": ["cristales", "fragmentos_antiguos", "reputacion"],
        "boss": "Oráculo Ahogado",
        "map_style": "Archipiélago invisible",
        "room_bias": {"combate": 24, "elite": 10, "evento": 20, "tesoro": 9, "tienda": 7, "santuario": 8, "tormenta": 8, "ruinas": 8, "npc": 3, "descanso": 2, "trampa": 1},
    },
    "mar_eclipse": {
        "name": "Mar del Eclipse",
        "subtitle": "Zona final",
        "desc": "Enemigos duros, mercado negro más frecuente y botín de alta rareza.",
        "difficulty": 2.35,
        "length": 14,
        "unlock": {"reputacion": 45, "fragmentos_antiguos": 5},
        "affinity": ["perlas_negras", "fragmentos_antiguos", "cristales"],
        "boss": "El Barco Sin Sol",
        "map_style": "Océano maldito",
        "room_bias": {"combate": 26, "elite": 14, "evento": 14, "tesoro": 9, "tienda": 6, "santuario": 6, "tormenta": 10, "ruinas": 8, "npc": 2, "descanso": 2, "trampa": 3},
    },
}

ENEMIES = {
    "puerto_bruma": [
        {"name": "Pirata Novato", "hp": 42, "damage": 8, "defense": 1, "speed": 5, "crit": 3, "xp": 8, "gold": 18},
        {"name": "Lancha Saqueadora", "hp": 36, "damage": 10, "defense": 0, "speed": 8, "crit": 5, "xp": 9, "gold": 20},
        {"name": "Cangrejo de Cubierta", "hp": 55, "damage": 7, "defense": 3, "speed": 3, "crit": 2, "xp": 10, "gold": 15},
        {"name": "Vigía Fantasma", "hp": 38, "damage": 11, "defense": 1, "speed": 9, "crit": 8, "xp": 11, "gold": 25},
    ],
    "bahia_escama": [
        {"name": "Sirena Hostil", "hp": 64, "damage": 14, "defense": 2, "speed": 10, "crit": 8, "xp": 16, "gold": 34},
        {"name": "Tiburón Blindado", "hp": 88, "damage": 13, "defense": 5, "speed": 6, "crit": 5, "xp": 18, "gold": 38},
        {"name": "Corsario de Escamas", "hp": 74, "damage": 16, "defense": 3, "speed": 8, "crit": 9, "xp": 19, "gold": 42},
        {"name": "Tótem Marino", "hp": 95, "damage": 11, "defense": 7, "speed": 2, "crit": 2, "xp": 17, "gold": 36},
    ],
    "islas_neblina": [
        {"name": "Nave de Espejos", "hp": 94, "damage": 18, "defense": 4, "speed": 12, "crit": 12, "xp": 26, "gold": 55},
        {"name": "Brujo del Faro", "hp": 82, "damage": 22, "defense": 2, "speed": 9, "crit": 10, "xp": 28, "gold": 62},
        {"name": "Bestia de Bruma", "hp": 125, "damage": 17, "defense": 6, "speed": 7, "crit": 7, "xp": 30, "gold": 58},
        {"name": "Tripulación Perdida", "hp": 110, "damage": 19, "defense": 5, "speed": 8, "crit": 8, "xp": 27, "gold": 60},
    ],
    "mar_eclipse": [
        {"name": "Fragata del Eclipse", "hp": 145, "damage": 26, "defense": 7, "speed": 11, "crit": 13, "xp": 42, "gold": 90},
        {"name": "Leviatán Negro", "hp": 180, "damage": 24, "defense": 9, "speed": 8, "crit": 10, "xp": 48, "gold": 100},
        {"name": "Capitán sin Rostro", "hp": 132, "damage": 31, "defense": 5, "speed": 13, "crit": 16, "xp": 45, "gold": 110},
        {"name": "Cañón Abisal", "hp": 210, "damage": 21, "defense": 12, "speed": 3, "crit": 6, "xp": 44, "gold": 88},
    ],
}

BOSSES = {
    "puerto_bruma": {"name": "Capitán Soga Mojada", "hp": 120, "damage": 17, "defense": 4, "speed": 7, "crit": 8, "xp": 45, "gold": 90},
    "bahia_escama": {"name": "Leviatán Joven", "hp": 190, "damage": 23, "defense": 7, "speed": 8, "crit": 10, "xp": 85, "gold": 150},
    "islas_neblina": {"name": "Oráculo Ahogado", "hp": 250, "damage": 30, "defense": 8, "speed": 12, "crit": 14, "xp": 140, "gold": 230},
    "mar_eclipse": {"name": "El Barco Sin Sol", "hp": 360, "damage": 39, "defense": 12, "speed": 11, "crit": 18, "xp": 240, "gold": 390},
}

UPGRADES = [
    {"id": "casco_reforzado", "name": "Casco reforzado", "rarity": "comun", "max": 20, "desc": "+12 vida máxima por nivel", "cost": {"madera": 22, "oro": 35}, "stat": "max_hp", "amount": 12},
    {"id": "canones_dobles", "name": "Cañones dobles", "rarity": "comun", "max": 20, "desc": "+3 daño por nivel", "cost": {"metal": 8, "oro": 45}, "stat": "damage", "amount": 3},
    {"id": "blindaje_lateral", "name": "Blindaje lateral", "rarity": "poco_comun", "max": 15, "desc": "+2 defensa por nivel", "cost": {"metal": 12, "madera": 15, "oro": 65}, "stat": "defense", "amount": 2},
    {"id": "motor_mejorado", "name": "Motor mejorado", "rarity": "poco_comun", "max": 15, "desc": "+2 velocidad por nivel", "cost": {"metal": 10, "combustible": 3, "oro": 60}, "stat": "speed", "amount": 2},
    {"id": "radar_avanzado", "name": "Radar avanzado", "rarity": "raro", "max": 12, "desc": "+2 radar y mejores eventos", "cost": {"cristales": 2, "metal": 18, "oro": 90}, "stat": "radar", "amount": 2},
    {"id": "antena_largo_alcance", "name": "Antena de largo alcance", "rarity": "raro", "max": 12, "desc": "+2 comunicación por nivel", "cost": {"cristales": 2, "oro": 85}, "stat": "communication", "amount": 2},
    {"id": "tripulacion_experta", "name": "Tripulación experta", "rarity": "raro", "max": 12, "desc": "+4 moral y +1 suerte por nivel", "cost": {"reputacion": 2, "oro": 100}, "stat": "morale", "amount": 4, "extra": {"luck": 1}},
    {"id": "brujula_negra_perm", "name": "Brújula negra permanente", "rarity": "epico", "max": 8, "desc": "+2 suerte y +1 crítico por nivel", "cost": {"fragmentos_antiguos": 1, "cristales": 5, "oro": 160}, "stat": "luck", "amount": 2, "extra": {"crit": 1}},
    {"id": "bodega_ampliada", "name": "Bodega ampliada", "rarity": "comun", "max": 15, "desc": "+5 carga por nivel", "cost": {"madera": 18, "oro": 50}, "stat": "cargo", "amount": 5},
    {"id": "polvora_fina", "name": "Pólvora fina", "rarity": "epico", "max": 10, "desc": "+2 crítico y +1 daño por nivel", "cost": {"perlas_negras": 1, "fragmentos_antiguos": 1, "oro": 220}, "stat": "crit", "amount": 2, "extra": {"damage": 1}},
    {"id": "contrabandista", "name": "Contacto contrabandista", "rarity": "legendario", "max": 6, "desc": "Más probabilidad de mercado negro", "cost": {"perlas_negras": 2, "reputacion": 4, "oro": 300}, "stat": "black_market", "amount": 3},
]

RELICS = [
    {"id": "brujula_negra", "name": "Brújula negra", "rarity": "raro", "type": "relic", "desc": "+5 suerte durante la expedición.", "effects": {"luck": 5}},
    {"id": "ancla_maldita", "name": "Ancla maldita", "rarity": "epico", "type": "relic", "desc": "+8 defensa, pero -3 velocidad.", "effects": {"defense": 8, "speed": -3}},
    {"id": "campana_antigua", "name": "Campana antigua", "rarity": "legendario", "type": "relic", "desc": "Revive una vez por expedición con 35% de vida.", "effects": {"revive": 1}},
    {"id": "ojo_del_faro", "name": "Ojo del faro", "rarity": "raro", "type": "relic", "desc": "+4 radar. Mejora decisiones de eventos.", "effects": {"radar": 4}},
    {"id": "moneda_pirata", "name": "Moneda pirata", "rarity": "epico", "type": "relic", "desc": "Tiendas 15% más baratas.", "effects": {"shop_discount": 15}},
    {"id": "motor_fantasma", "name": "Motor fantasma", "rarity": "epico", "type": "relic", "desc": "+18% probabilidad de escapar.", "effects": {"flee": 18}},
    {"id": "cristal_marea", "name": "Cristal de marea", "rarity": "legendario", "type": "relic", "desc": "Cura 6% de vida al entrar a una sala.", "effects": {"room_heal_pct": 6}},
    {"id": "diente_leviatan", "name": "Diente de leviatán", "rarity": "legendario", "type": "relic", "desc": "+10 daño y +5 crítico.", "effects": {"damage": 10, "crit": 5}},
    {"id": "farol_abisal", "name": "Farol abisal", "rarity": "epico", "type": "relic", "desc": "Más probabilidad de eventos raros.", "effects": {"rare_event": 8}},
    {"id": "barrera_sal", "name": "Barrera de sal", "rarity": "poco_comun", "type": "relic", "desc": "+4 defensa contra combates normales.", "effects": {"defense": 4}},
]

CONSUMABLES = [
    {"id": "ron_curativo", "name": "Ron curativo", "rarity": "comun", "type": "consumable", "desc": "Cura 30 de vida.", "price": 35, "stack": True, "heal": 30},
    {"id": "parche_reforzado", "name": "Parche reforzado", "rarity": "poco_comun", "type": "consumable", "desc": "Cura 55 de vida.", "price": 70, "stack": True, "heal": 55},
    {"id": "bengala_roja", "name": "Bengala roja", "rarity": "raro", "type": "consumable", "desc": "+12 crítico por 2 turnos.", "price": 90, "stack": True, "buff": {"crit": 12, "turns": 2}},
    {"id": "bomba_humo", "name": "Bomba de humo", "rarity": "poco_comun", "type": "consumable", "desc": "Aumenta la probabilidad de escapar en combate.", "price": 65, "stack": True, "flee_bonus": 35},
    {"id": "kit_emergencia", "name": "Kit de emergencia", "rarity": "epico", "type": "consumable", "desc": "Cura 90 de vida y limpia un debuff.", "price": 140, "stack": True, "heal": 90, "cleanse": True},
]

NPCS = [
    {"name": "Cartógrafa Lina", "kind": "npc", "desc": "Ofrece revelar una ruta y mejorar el radar por una expedición."},
    {"name": "Mecánico Tobías", "kind": "npc", "desc": "Puede reparar el barco o vender piezas viejas."},
    {"name": "Contrabandista Nox", "kind": "npc", "desc": "Cambia perlas negras por reliquias extrañas."},
    {"name": "Monje del Faro", "kind": "npc", "desc": "Bendice la tripulación o retira una maldición."},
]

EVENT_POOL = [
    {
        "title": "Señal en la tormenta",
        "rarity": "comun",
        "good": "Encuentras una caja flotando entre las olas.",
        "bad": "La señal era una trampa. El casco recibe daño.",
        "stat": "radar",
        "reward": {"oro": (18, 45), "madera": (8, 18)},
        "damage": (8, 18),
    },
    {
        "title": "Isla con luces azules",
        "rarity": "raro",
        "good": "La isla tenía cristales vivos y un mapa viejo.",
        "bad": "La tripulación se asusta y pierde moral.",
        "stat": "communication",
        "reward": {"cristales": (1, 4), "reputacion": (1, 2)},
        "morale_loss": (6, 14),
    },
    {
        "title": "Ruinas bajo la marea",
        "rarity": "epico",
        "good": "Recuperas fragmentos antiguos de una cámara sellada.",
        "bad": "Una maldición reduce tu defensa durante la expedición.",
        "stat": "luck",
        "reward": {"fragmentos_antiguos": (1, 2), "oro": (60, 130)},
        "debuff": {"name": "Maldición salada", "defense": -3, "rooms": 3},
    },
    {
        "title": "Barco mercante abandonado",
        "rarity": "poco_comun",
        "good": "La bodega estaba llena de provisiones.",
        "bad": "Había ratas enfermas. Pierdes vida y moral.",
        "stat": "speed",
        "reward": {"combustible": (2, 5), "oro": (25, 65), "metal": (3, 8)},
        "damage": (10, 24),
        "morale_loss": (2, 7),
    },
    {
        "title": "Pozo de perlas negras",
        "rarity": "legendario",
        "good": "Consigues una perla negra intacta.",
        "bad": "El mar cobra precio. Pierdes mucha vida.",
        "stat": "luck",
        "reward": {"perlas_negras": (1, 1), "fragmentos_antiguos": (1, 2)},
        "damage": (24, 48),
    },
]

ROOM_LABELS = {
    "combate": "Combate",
    "elite": "Élite",
    "jefe": "Jefe",
    "tesoro": "Tesoro",
    "evento": "Evento",
    "tienda": "Tienda",
    "mercado_negro": "Mercado negro",
    "santuario": "Santuario",
    "tormenta": "Tormenta",
    "ruinas": "Ruinas",
    "npc": "NPC",
    "descanso": "Descanso",
    "trampa": "Trampa",
}


def clamp(value, low, high):
    return max(low, min(high, value))


def weighted_choice(weight_map):
    keys = list(weight_map.keys())
    weights = list(weight_map.values())
    return random.choices(keys, weights=weights, k=1)[0]


def roll_rarity(luck=0, rare_bonus=0):
    weights = {}
    for key, data in RARITIES.items():
        w = data["weight"]
        if key == "poco_comun":
            w += luck * 0.35
        elif key == "raro":
            w += luck * 0.25 + rare_bonus
        elif key == "epico":
            w += luck * 0.12 + rare_bonus * 0.45
        elif key == "legendario":
            w += luck * 0.04 + rare_bonus * 0.12
        weights[key] = max(1, w)
    return weighted_choice(weights)


def rarity_badge(rarity):
    r = RARITIES.get(rarity, RARITIES["comun"])
    return f"{r['icon']} {r['label']}"


def format_resource(key, qty):
    label = RESOURCE_INFO.get(key, {}).get("label", key)
    return f"{label}: {qty}"


def add_log(game, text):
    game.setdefault("log", [])
    stamp = datetime.now().strftime("%H:%M")
    game["log"].insert(0, f"[{stamp}] {text}")
    game["log"] = game["log"][:80]


def default_game():
    return {
        "version": GAME_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "resources": deepcopy(BASE_RESOURCES),
        "ship": deepcopy(BASE_SHIP),
        "inventory_slots": 12,
        "inventory": [
            {"id": "ron_curativo", "name": "Ron curativo", "rarity": "comun", "type": "consumable", "qty": 2, "desc": "Cura 30 de vida."},
            {"id": "brujula_negra", "name": "Brújula negra", "rarity": "raro", "type": "relic", "qty": 1, "desc": "+5 suerte durante la expedición."},
        ],
        "upgrades": {u["id"]: 0 for u in UPGRADES},
        "crew": {
            "capitan": {"name": "Capitán", "level": 1, "bonus": "+2 moral inicial"},
            "artillero": {"name": "Artillero", "level": 1, "bonus": "+2 daño"},
            "mecanico": {"name": "Mecánico", "level": 1, "bonus": "+5 reparación"},
            "vigia": {"name": "Vigía", "level": 1, "bonus": "+1 radar"},
        },
        "unlocked_ports": ["puerto_bruma"],
        "selected_port": "puerto_bruma",
        "run": None,
        "combat": None,
        "shop": None,
        "view": "Puerto",
        "stats": {
            "runs": 0,
            "wins": 0,
            "deaths": 0,
            "rooms_completed": 0,
            "enemies_defeated": 0,
            "bosses_defeated": 0,
            "gold_earned": 0,
            "best_depth": 0,
        },
        "log": ["Partida creada. Tu barco espera en Puerto Bruma."],
    }


def save_game(game):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(game, f, ensure_ascii=False, indent=2)
        return True
    except Exception as exc:
        st.error(f"No se pudo guardar la partida: {exc}")
        return False


def load_game():
    if not os.path.exists(SAVE_FILE):
        return default_game()
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        game = default_game()
        game.update(data)
        for key in BASE_RESOURCES:
            game["resources"].setdefault(key, 0)
        for u in UPGRADES:
            game["upgrades"].setdefault(u["id"], 0)
        game.setdefault("unlocked_ports", ["puerto_bruma"])
        game.setdefault("inventory_slots", 12)
        game.setdefault("inventory", [])
        game.setdefault("log", [])
        game.setdefault("stats", default_game()["stats"])
        return game
    except Exception:
        return default_game()


def reset_game():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)
    st.session_state.game = default_game()
    save_game(st.session_state.game)


def init_state():
    if "game" not in st.session_state:
        st.session_state.game = load_game()
    if "last_action" not in st.session_state:
        st.session_state.last_action = ""


def resource_has(game, cost):
    return all(game["resources"].get(k, 0) >= v for k, v in cost.items())


def spend_resources(game, cost):
    if not resource_has(game, cost):
        return False
    for key, val in cost.items():
        game["resources"][key] -= val
    return True


def add_resources(game, reward):
    for key, val in reward.items():
        game["resources"][key] = game["resources"].get(key, 0) + int(val)
        if key == "oro":
            game["stats"]["gold_earned"] += int(val)


def scale_cost(base_cost, level):
    scaled = {}
    for key, val in base_cost.items():
        scaled[key] = int(math.ceil(val * (1.35 ** level)))
    return scaled


def find_item_template(item_id):
    for item in CONSUMABLES + RELICS:
        if item["id"] == item_id:
            return deepcopy(item)
    return None


def inventory_count(game):
    return sum(1 for item in game["inventory"] if item.get("qty", 1) > 0)


def add_item(game, item, qty=1):
    item = deepcopy(item)
    if item.get("stack") or item.get("type") == "consumable":
        for inv in game["inventory"]:
            if inv["id"] == item["id"]:
                inv["qty"] = inv.get("qty", 1) + qty
                return True
    if inventory_count(game) >= game["inventory_slots"]:
        add_log(game, f"No había espacio para guardar {item['name']}.")
        return False
    item["qty"] = qty
    game["inventory"].append(item)
    return True


def remove_item(game, item_id, qty=1):
    for item in list(game["inventory"]):
        if item["id"] == item_id:
            item["qty"] = item.get("qty", 1) - qty
            if item["qty"] <= 0:
                game["inventory"].remove(item)
            return True
    return False


def relic_effects(game):
    effects = {}
    for inv in game.get("inventory", []):
        if inv.get("type") == "relic":
            template = find_item_template(inv["id"])
            if template:
                for k, v in template.get("effects", {}).items():
                    effects[k] = effects.get(k, 0) + v
    return effects


def calc_ship_stats(game, include_run=True):
    stats = deepcopy(game["ship"])
    for crew_key, crew in game.get("crew", {}).items():
        level = crew.get("level", 1)
        if crew_key == "capitan":
            stats["morale"] += 2 * level
        elif crew_key == "artillero":
            stats["damage"] += 2 * level
        elif crew_key == "mecanico":
            stats["defense"] += 1 * level
        elif crew_key == "vigia":
            stats["radar"] += 1 * level

    for up in UPGRADES:
        lvl = game["upgrades"].get(up["id"], 0)
        if lvl <= 0:
            continue
        stat = up["stat"]
        stats[stat] = stats.get(stat, 0) + up["amount"] * lvl
        for ek, ev in up.get("extra", {}).items():
            stats[ek] = stats.get(ek, 0) + ev * lvl

    for k, v in relic_effects(game).items():
        if k in stats:
            stats[k] += v

    if include_run and game.get("run"):
        run = game["run"]
        for buff in run.get("buffs", []):
            for k, v in buff.get("stats", {}).items():
                stats[k] = stats.get(k, 0) + v
        for debuff in run.get("debuffs", []):
            for k, v in debuff.get("stats", {}).items():
                stats[k] = stats.get(k, 0) + v

    stats["crit"] = clamp(stats.get("crit", 0), 0, 75)
    stats["luck"] = max(0, stats.get("luck", 0))
    stats["morale"] = clamp(stats.get("morale", 0), 0, 120)
    return stats


def get_discount(game):
    return relic_effects(game).get("shop_discount", 0)


def maybe_unlock_ports(game):
    changed = False
    for port_id, port in PORTS.items():
        if port_id in game["unlocked_ports"]:
            continue
        ok = True
        for res, need in port["unlock"].items():
            if game["resources"].get(res, 0) < need:
                ok = False
                break
        if ok:
            game["unlocked_ports"].append(port_id)
            add_log(game, f"Nuevo puerto desbloqueado: {port['name']}.")
            changed = True
    return changed


def generate_room(port_id, depth, max_depth, forced=None):
    port = PORTS[port_id]
    if depth == max_depth:
        room_type = "jefe"
    elif forced:
        room_type = forced
    else:
        room_type = weighted_choice(port["room_bias"])
        if random.random() < 0.025:
            room_type = "mercado_negro"
    rarity = roll_rarity()
    title = ROOM_LABELS.get(room_type, room_type)
    return {
        "type": room_type,
        "rarity": rarity,
        "title": title,
        "completed": False,
        "seen": False,
        "depth": depth,
    }


def generate_map(port_id):
    port = PORTS[port_id]
    max_depth = port["length"]
    rooms = []
    for depth in range(1, max_depth + 1):
        forced = None
        if depth in [4, 8, 12] and depth < max_depth and random.random() < 0.65:
            forced = "tienda"
        if depth in [3, 7, 11] and depth < max_depth and random.random() < 0.35:
            forced = "descanso"
        rooms.append(generate_room(port_id, depth, max_depth, forced))
    return rooms


def start_run(game, port_id):
    stats = calc_ship_stats(game, include_run=False)
    port = PORTS[port_id]
    fuel_cost = max(2, int(2 + port["difficulty"] * 2))
    if game["resources"].get("combustible", 0) < fuel_cost:
        add_log(game, "No tienes suficiente combustible para iniciar la expedición.")
        return False
    game["resources"]["combustible"] -= fuel_cost
    rooms = generate_map(port_id)
    game["run"] = {
        "active": True,
        "port": port_id,
        "depth": 1,
        "max_depth": len(rooms),
        "rooms": rooms,
        "hp": stats["max_hp"],
        "max_hp": stats["max_hp"],
        "morale": stats["morale"],
        "cargo_used": 0,
        "loot": deepcopy({k: 0 for k in BASE_RESOURCES}),
        "buffs": [],
        "debuffs": [],
        "temp_flee_bonus": 0,
        "used_revive": False,
        "score": 0,
    }
    game["combat"] = None
    game["shop"] = None
    game["stats"]["runs"] += 1
    add_log(game, f"Expedición iniciada desde {port['name']}.")
    return True


def end_run(game, won=False, died=False):
    run = game.get("run")
    if not run:
        return
    loot = run.get("loot", {})
    if died:
        kept = {}
        for key, val in loot.items():
            if key in ["reputacion", "fragmentos_antiguos", "perlas_negras"]:
                kept[key] = int(val * 0.5)
            else:
                kept[key] = int(val * 0.35)
        add_resources(game, kept)
        game["stats"]["deaths"] += 1
        add_log(game, "La expedición terminó en derrota. Conservaste una parte del botín.")
    else:
        add_resources(game, loot)
        add_log(game, "Expedición finalizada. Todo el botín fue enviado al puerto.")
    if won:
        game["stats"]["wins"] += 1
        game["stats"]["bosses_defeated"] += 1
        add_log(game, "Victoria. La tripulación celebra en el puerto.")
    game["stats"]["best_depth"] = max(game["stats"].get("best_depth", 0), run.get("depth", 1))
    game["run"] = None
    game["combat"] = None
    game["shop"] = None
    maybe_unlock_ports(game)


def abandon_run(game):
    end_run(game, won=False, died=False)


def add_run_loot(game, reward):
    run = game.get("run")
    if not run:
        add_resources(game, reward)
        return
    for k, v in reward.items():
        run["loot"][k] = run["loot"].get(k, 0) + int(v)
        if k == "oro":
            game["stats"]["gold_earned"] += int(v)


def complete_room(game):
    run = game.get("run")
    if not run:
        return
    idx = run["depth"] - 1
    if 0 <= idx < len(run["rooms"]):
        run["rooms"][idx]["completed"] = True
    game["stats"]["rooms_completed"] += 1
    decay_temporary_effects(game)
    room_heal = relic_effects(game).get("room_heal_pct", 0)
    if room_heal:
        heal = max(1, int(run["max_hp"] * room_heal / 100))
        run["hp"] = min(run["max_hp"], run["hp"] + heal)
        add_log(game, f"Cristal de marea cura {heal} de vida.")
    if run["depth"] >= run["max_depth"]:
        end_run(game, won=True, died=False)
    else:
        run["depth"] += 1


def decay_temporary_effects(game):
    run = game.get("run")
    if not run:
        return
    new_buffs = []
    for buff in run.get("buffs", []):
        buff["rooms"] = buff.get("rooms", 1) - 1
        if buff["rooms"] > 0:
            new_buffs.append(buff)
        else:
            add_log(game, f"El buff terminó: {buff['name']}.")
    run["buffs"] = new_buffs

    new_debuffs = []
    for debuff in run.get("debuffs", []):
        debuff["rooms"] = debuff.get("rooms", 1) - 1
        if debuff["rooms"] > 0:
            new_debuffs.append(debuff)
        else:
            add_log(game, f"El debuff terminó: {debuff['name']}.")
    run["debuffs"] = new_debuffs


def enemy_scaled(enemy, port_id, room_type, depth):
    port = PORTS[port_id]
    diff = port["difficulty"] * (1 + (depth - 1) * 0.055)
    if room_type == "elite":
        diff *= 1.35
    elif room_type == "jefe":
        diff *= 1.15
    scaled = deepcopy(enemy)
    for key in ["hp", "damage", "defense", "speed", "xp", "gold"]:
        scaled[key] = int(math.ceil(enemy[key] * diff))
    if room_type == "elite":
        scaled["name"] = "Élite: " + scaled["name"]
        scaled["crit"] += 5
    return scaled


def start_combat(game, room_type="combate"):
    run = game["run"]
    port_id = run["port"]
    if room_type == "jefe":
        enemy = enemy_scaled(BOSSES[port_id], port_id, room_type, run["depth"])
    else:
        enemy = enemy_scaled(random.choice(ENEMIES[port_id]), port_id, room_type, run["depth"])
    game["combat"] = {
        "enemy": enemy,
        "enemy_hp": enemy["hp"],
        "turn": 1,
        "defending": False,
        "player_buffs": [],
        "message": f"Aparece {enemy['name']}.",
        "room_type": room_type,
    }


def damage_roll(base_damage, crit_chance, attacker_luck=0):
    variance = random.uniform(0.82, 1.18)
    dmg = base_damage * variance
    crit = random.random() * 100 < crit_chance
    if crit:
        dmg *= random.uniform(1.65, 2.25 + attacker_luck * 0.015)
    return max(1, int(round(dmg))), crit


def player_attack(game, mode):
    combat = game.get("combat")
    run = game.get("run")
    if not combat or not run:
        return
    stats = calc_ship_stats(game)
    enemy = combat["enemy"]
    combat["defending"] = False

    if mode == "cañonazo":
        base = stats["damage"]
        accuracy = 88 + stats["radar"] * 0.5
        crit_bonus = 0
        label = "Cañonazo"
    elif mode == "andanada":
        base = stats["damage"] * 1.55
        accuracy = 68 + stats["radar"] * 0.45
        crit_bonus = 7
        label = "Andanada pesada"
    elif mode == "tiro_preciso":
        base = stats["damage"] * 0.85
        accuracy = 96
        crit_bonus = 20 + stats["radar"] * 0.5
        label = "Tiro preciso"
    else:
        base = stats["damage"]
        accuracy = 85
        crit_bonus = 0
        label = "Ataque"

    hit = random.random() * 100 < accuracy
    if not hit:
        combat["message"] = f"{label}: fallaste el ataque."
        enemy_turn(game)
        return

    dmg, crit = damage_roll(base, stats["crit"] + crit_bonus, stats["luck"])
    dmg = max(1, dmg - int(enemy["defense"] * 0.75))
    combat["enemy_hp"] -= dmg
    if crit:
        combat["message"] = f"{label}: crítico por {dmg} de daño."
    else:
        combat["message"] = f"{label}: hiciste {dmg} de daño."

    if combat["enemy_hp"] <= 0:
        win_combat(game)
    else:
        enemy_turn(game)


def enemy_turn(game):
    combat = game.get("combat")
    run = game.get("run")
    if not combat or not run:
        return
    stats = calc_ship_stats(game)
    enemy = combat["enemy"]
    hit_chance = clamp(82 + enemy["speed"] * 0.35 - stats["speed"] * 0.45, 52, 94)
    if random.random() * 100 > hit_chance:
        combat["message"] += f" {enemy['name']} falló su ataque."
        combat["turn"] += 1
        tick_combat_buffs(game)
        return
    dmg, crit = damage_roll(enemy["damage"], enemy["crit"], 0)
    mitigation = stats["defense"]
    if combat.get("defending"):
        mitigation += 8 + int(stats["defense"] * 0.55)
    dmg = max(1, dmg - int(mitigation * 0.65))
    run["hp"] -= dmg
    if crit:
        combat["message"] += f" {enemy['name']} respondió con crítico de {dmg}."
    else:
        combat["message"] += f" {enemy['name']} hizo {dmg} de daño."
    combat["turn"] += 1
    tick_combat_buffs(game)
    if run["hp"] <= 0:
        handle_death(game)


def defend(game):
    combat = game.get("combat")
    if not combat:
        return
    combat["defending"] = True
    combat["message"] = "Te preparas para defender. El siguiente daño recibido será menor."
    enemy_turn(game)


def repair_action(game):
    run = game.get("run")
    combat = game.get("combat")
    if not run or not combat:
        return
    stats = calc_ship_stats(game)
    heal = random.randint(14, 26) + stats["defense"] + game["crew"].get("mecanico", {}).get("level", 1) * 5
    run["hp"] = min(run["max_hp"], run["hp"] + heal)
    combat["message"] = f"El mecánico repara {heal} de vida."
    enemy_turn(game)


def flee_action(game):
    run = game.get("run")
    combat = game.get("combat")
    if not run or not combat:
        return
    stats = calc_ship_stats(game)
    base = 35 + stats["speed"] * 1.2 + relic_effects(game).get("flee", 0) + run.get("temp_flee_bonus", 0)
    base -= combat["enemy"].get("speed", 0) * 0.8
    chance = clamp(base, 12, 88)
    run["temp_flee_bonus"] = 0
    if random.random() * 100 < chance:
        combat["message"] = "Lograste escapar, pero perdiste parte del botín de la sala."
        game["combat"] = None
        complete_room(game)
    else:
        combat["message"] = "Intentaste escapar, pero el enemigo te bloqueó."
        enemy_turn(game)


def tick_combat_buffs(game):
    combat = game.get("combat")
    if not combat:
        return
    new_buffs = []
    for buff in combat.get("player_buffs", []):
        buff["turns"] -= 1
        if buff["turns"] > 0:
            new_buffs.append(buff)
    combat["player_buffs"] = new_buffs


def win_combat(game):
    combat = game.get("combat")
    run = game.get("run")
    if not combat or not run:
        return
    enemy = combat["enemy"]
    reward = {"oro": enemy.get("gold", 0)}
    port = PORTS[run["port"]]
    affinity = random.choice(port["affinity"])
    amount = random.randint(2, 7)
    if combat.get("room_type") == "elite":
        amount *= 2
        reward["reputacion"] = random.randint(1, 2)
    if combat.get("room_type") == "jefe":
        amount *= 3
        reward["reputacion"] = random.randint(3, 6)
        reward["fragmentos_antiguos"] = random.randint(1, 3)
        if random.random() < 0.35:
            reward["perlas_negras"] = 1
    reward[affinity] = reward.get(affinity, 0) + amount
    add_run_loot(game, reward)
    game["stats"]["enemies_defeated"] += 1
    gain_xp(game, enemy.get("xp", 0))

    luck = calc_ship_stats(game).get("luck", 0)
    rare_bonus = relic_effects(game).get("rare_event", 0)
    if random.random() * 100 < 18 + luck * 0.6:
        relic = random_relic(luck, rare_bonus)
        if add_item(game, relic):
            add_log(game, f"Botín de combate: {relic['name']} ({rarity_badge(relic['rarity'])}).")

    add_log(game, f"Derrotaste a {enemy['name']}. Recompensa: {', '.join(format_resource(k, v) for k, v in reward.items())}.")
    game["combat"] = None
    complete_room(game)


def gain_xp(game, xp):
    ship = game["ship"]
    ship["xp"] += xp
    needed = 80 + ship["level"] * 35
    while ship["xp"] >= needed:
        ship["xp"] -= needed
        ship["level"] += 1
        ship["max_hp"] += 5
        ship["damage"] += 1
        add_log(game, f"El barco subió a nivel {ship['level']}.")
        needed = 80 + ship["level"] * 35


def handle_death(game):
    run = game.get("run")
    if not run:
        return
    effects = relic_effects(game)
    if effects.get("revive", 0) and not run.get("used_revive"):
        run["used_revive"] = True
        run["hp"] = max(1, int(run["max_hp"] * 0.35))
        game["combat"]["message"] += " La Campana antigua te revive una vez."
        add_log(game, "La Campana antigua evitó la derrota.")
        return
    end_run(game, won=False, died=True)


def random_relic(luck=0, rare_bonus=0):
    rarity = roll_rarity(luck, rare_bonus)
    candidates = [r for r in RELICS if r["rarity"] == rarity]
    if not candidates:
        candidates = RELICS
    return deepcopy(random.choice(candidates))


def random_consumable():
    return deepcopy(random.choice(CONSUMABLES))


def make_loot(port_id, rarity, luck=0):
    port = PORTS[port_id]
    mult = RARITIES[rarity]["mult"]
    reward = {}
    reward["oro"] = int(random.randint(20, 70) * mult)
    for res in port["affinity"]:
        base = random.randint(1, 5)
        if res == "perlas_negras":
            reward[res] = 1 if random.random() < 0.15 * mult + luck * 0.002 else 0
        elif res == "fragmentos_antiguos":
            reward[res] = max(0, int(random.randint(0, 2) * mult))
        elif res == "cristales":
            reward[res] = max(1, int(random.randint(1, 3) * mult))
        else:
            reward[res] = int(base * mult)
    return {k: v for k, v in reward.items() if v > 0}


def resolve_treasure(game):
    run = game["run"]
    stats = calc_ship_stats(game)
    room = current_room(game)
    reward = make_loot(run["port"], room["rarity"], stats["luck"])
    add_run_loot(game, reward)
    if random.random() * 100 < 20 + stats["luck"] * 0.7:
        item = random_relic(stats["luck"], relic_effects(game).get("rare_event", 0))
        add_item(game, item)
        add_log(game, f"Encontraste reliquia: {item['name']}.")
    add_log(game, f"Tesoro abierto: {', '.join(format_resource(k, v) for k, v in reward.items())}.")
    complete_room(game)


def resolve_sanctuary(game, choice):
    run = game["run"]
    if choice == "bendicion_casco":
        run["buffs"].append({"name": "Bendición del casco", "stats": {"defense": 6}, "rooms": 4})
        run["hp"] = min(run["max_hp"], run["hp"] + 35)
        add_log(game, "El santuario reforzó el casco por varias salas.")
    elif choice == "bendicion_canones":
        run["buffs"].append({"name": "Bendición de pólvora", "stats": {"damage": 8, "crit": 8}, "rooms": 4})
        add_log(game, "Los cañones brillan con pólvora bendita.")
    elif choice == "purgar":
        run["debuffs"] = []
        add_log(game, "El santuario retiró todas las maldiciones activas.")
    complete_room(game)


def resolve_rest(game, choice):
    run = game["run"]
    if choice == "reparar":
        heal = int(run["max_hp"] * 0.34)
        run["hp"] = min(run["max_hp"], run["hp"] + heal)
        add_log(game, f"Descanso: reparaste {heal} de vida.")
    elif choice == "moral":
        run["morale"] = min(120, run["morale"] + 18)
        run["buffs"].append({"name": "Tripulación animada", "stats": {"luck": 3}, "rooms": 3})
        add_log(game, "La tripulación recuperó moral y suerte temporal.")
    elif choice == "saquear":
        reward = {"oro": random.randint(20, 60), "madera": random.randint(4, 12)}
        add_run_loot(game, reward)
        add_log(game, "El descanso se usó para saquear restos cercanos.")
    complete_room(game)


def resolve_trap(game, choice):
    run = game["run"]
    stats = calc_ship_stats(game)
    if choice == "desactivar":
        chance = 45 + stats["radar"] * 2 + stats["luck"]
        if random.random() * 100 < chance:
            reward = {"metal": random.randint(4, 12), "oro": random.randint(20, 45)}
            add_run_loot(game, reward)
            add_log(game, "Desactivaste la trampa y recuperaste piezas.")
        else:
            dmg = random.randint(12, 30)
            run["hp"] -= dmg
            add_log(game, f"Fallaste desactivando la trampa. Daño recibido: {dmg}.")
    elif choice == "atravesar":
        dmg = random.randint(8, 22)
        run["hp"] -= dmg
        add_log(game, f"Atravesaste la trampa rápido. Daño recibido: {dmg}.")
    elif choice == "rodear":
        run["morale"] = max(0, run["morale"] - 4)
        add_log(game, "Rodeaste la trampa. Pierdes algo de moral por el retraso.")
    if run["hp"] <= 0:
        handle_death(game)
    else:
        complete_room(game)


def resolve_storm(game, choice):
    run = game["run"]
    stats = calc_ship_stats(game)
    if choice == "cruzar":
        chance = 45 + stats["speed"] * 1.4 + stats["radar"] * 0.8
        if random.random() * 100 < chance:
            reward = {"reputacion": 1, "combustible": random.randint(1, 3)}
            add_run_loot(game, reward)
            add_log(game, "Cruzaste la tormenta y ganaste reputación.")
        else:
            dmg = random.randint(18, 42)
            run["hp"] -= dmg
            run["debuffs"].append({"name": "Velas dañadas", "stats": {"speed": -4}, "rooms": 3})
            add_log(game, f"La tormenta golpeó fuerte. Daño: {dmg}. Velocidad reducida.")
    elif choice == "esperar":
        run["morale"] = max(0, run["morale"] - 8)
        heal = random.randint(6, 18)
        run["hp"] = min(run["max_hp"], run["hp"] + heal)
        add_log(game, f"Esperaste a que bajara la tormenta. Moral -8, reparación +{heal}.")
    elif choice == "usar_radar":
        chance = 55 + stats["radar"] * 2.4
        if random.random() * 100 < chance:
            reward = {"cristales": random.randint(1, 3), "oro": random.randint(25, 70)}
            add_run_loot(game, reward)
            add_log(game, "El radar encontró un paso seguro con botín oculto.")
        else:
            dmg = random.randint(10, 26)
            run["hp"] -= dmg
            add_log(game, f"El radar no fue suficiente. Daño: {dmg}.")
    if run and run.get("hp", 1) <= 0:
        handle_death(game)
    else:
        complete_room(game)


def resolve_event(game, choice):
    run = game["run"]
    stats = calc_ship_stats(game)
    event = run.get("current_event")
    if not event:
        event = choose_event(stats)
        run["current_event"] = event
    if choice == "ignorar":
        add_log(game, "Ignoraste el evento y continuaste la ruta.")
        run.pop("current_event", None)
        complete_room(game)
        return
    stat_val = stats.get(event.get("stat", "luck"), 0)
    chance = 42 + stat_val * 2.2 + stats.get("luck", 0) * 0.6
    if choice == "arriesgar":
        chance -= 10
    elif choice == "cuidadoso":
        chance += 12
    success = random.random() * 100 < clamp(chance, 12, 92)
    if success:
        reward = {}
        for k, rng in event.get("reward", {}).items():
            reward[k] = random.randint(rng[0], rng[1])
        add_run_loot(game, reward)
        add_log(game, f"{event['title']}: {event['good']} Recompensa: {', '.join(format_resource(k, v) for k, v in reward.items())}.")
    else:
        add_log(game, f"{event['title']}: {event['bad']}")
        if "damage" in event:
            dmg = random.randint(*event["damage"])
            run["hp"] -= dmg
            add_log(game, f"Daño recibido: {dmg}.")
        if "morale_loss" in event:
            loss = random.randint(*event["morale_loss"])
            run["morale"] = max(0, run["morale"] - loss)
            add_log(game, f"Moral perdida: {loss}.")
        if "debuff" in event:
            d = event["debuff"]
            stats_debuff = {k: v for k, v in d.items() if k not in ["name", "rooms"]}
            run["debuffs"].append({"name": d["name"], "stats": stats_debuff, "rooms": d["rooms"]})
    run.pop("current_event", None)
    if run["hp"] <= 0:
        handle_death(game)
    else:
        complete_room(game)


def choose_event(stats):
    rare_bonus = relic_effects(st.session_state.game).get("rare_event", 0) if "game" in st.session_state else 0
    rarity = roll_rarity(stats.get("luck", 0), rare_bonus)
    candidates = [e for e in EVENT_POOL if e["rarity"] == rarity]
    if not candidates:
        candidates = EVENT_POOL
    return deepcopy(random.choice(candidates))


def resolve_ruins(game, choice):
    run = game["run"]
    stats = calc_ship_stats(game)
    if choice == "explorar":
        chance = 38 + stats["radar"] * 1.8 + stats["luck"]
        if random.random() * 100 < chance:
            reward = {"fragmentos_antiguos": random.randint(1, 2), "cristales": random.randint(1, 4)}
            add_run_loot(game, reward)
            add_log(game, "Exploraste las ruinas y recuperaste artefactos.")
        else:
            run["debuffs"].append({"name": "Eco antiguo", "stats": {"crit": -5, "luck": -2}, "rooms": 3})
            add_log(game, "Las ruinas activaron un eco antiguo. Pierdes crítico y suerte temporal.")
    elif choice == "dinamita":
        reward = {"metal": random.randint(6, 16), "oro": random.randint(30, 80)}
        dmg = random.randint(8, 20)
        run["hp"] -= dmg
        add_run_loot(game, reward)
        add_log(game, f"Abriste las ruinas a la fuerza. Botín conseguido, daño recibido: {dmg}.")
    elif choice == "marcar":
        run["buffs"].append({"name": "Ruta marcada", "stats": {"radar": 4, "luck": 2}, "rooms": 4})
        add_log(game, "Marcaste las ruinas para evitar riesgos. Radar y suerte temporal.")
    if run["hp"] <= 0:
        handle_death(game)
    else:
        complete_room(game)


def resolve_npc(game, choice):
    npc = random.choice(NPCS)
    run = game["run"]
    if choice == "ayudar":
        reward = {"reputacion": random.randint(1, 3), "oro": random.randint(20, 70)}
        add_run_loot(game, reward)
        add_log(game, f"Ayudaste a {npc['name']}. Ganas reputación y oro.")
    elif choice == "comprar_info":
        cost = 30
        if run["loot"].get("oro", 0) >= cost:
            run["loot"]["oro"] -= cost
            run["buffs"].append({"name": "Información de ruta", "stats": {"radar": 6, "luck": 2}, "rooms": 5})
            add_log(game, f"{npc['name']} te vendió información útil.")
        else:
            add_log(game, "No tenías oro suficiente en la expedición. El NPC se fue.")
    elif choice == "robar":
        chance = 30 + calc_ship_stats(game)["luck"]
        if random.random() * 100 < chance:
            item = random_consumable()
            add_item(game, item)
            add_log(game, f"Robaste {item['name']}, aunque la tripulación no está orgullosa.")
            run["morale"] = max(0, run["morale"] - 8)
        else:
            run["hp"] -= random.randint(10, 28)
            run["morale"] = max(0, run["morale"] - 15)
            add_log(game, "El robo salió mal. Pierdes vida y moral.")
    if run and run.get("hp", 1) <= 0:
        handle_death(game)
    else:
        complete_room(game)


def current_room(game):
    run = game.get("run")
    if not run:
        return None
    idx = run["depth"] - 1
    if idx < 0 or idx >= len(run["rooms"]):
        return None
    return run["rooms"][idx]


def generate_shop(game, black=False):
    discount = get_discount(game)
    items = []
    count = 5 if not black else 6
    for _ in range(count):
        if black:
            item = random_relic(calc_ship_stats(game).get("luck", 0), 12)
            price = int((220 * RARITIES[item["rarity"]]["mult"]) * (1 - discount / 100))
            currency = "perlas_negras" if item["rarity"] in ["epico", "legendario"] and random.random() < 0.45 else "oro"
            if currency == "perlas_negras":
                price = max(1, int(RARITIES[item["rarity"]]["mult"]))
        else:
            item = random_consumable() if random.random() < 0.68 else random_relic(calc_ship_stats(game).get("luck", 0), 0)
            base = item.get("price", 130 * RARITIES[item["rarity"]]["mult"])
            price = int(base * (1 - discount / 100))
            currency = "oro"
        items.append({"item": item, "price": max(1, price), "currency": currency})
    game["shop"] = {"black": black, "items": items}


def buy_shop_item(game, index):
    shop = game.get("shop")
    if not shop:
        return
    if index < 0 or index >= len(shop["items"]):
        return
    offer = shop["items"][index]
    currency = offer["currency"]
    price = offer["price"]
    if game["resources"].get(currency, 0) < price:
        add_log(game, f"No tienes suficiente {RESOURCE_INFO[currency]['label']}.")
        return
    if inventory_count(game) >= game["inventory_slots"] and not offer["item"].get("stack"):
        add_log(game, "Inventario lleno. Amplía tu bodega o usa objetos.")
        return
    game["resources"][currency] -= price
    add_item(game, offer["item"])
    add_log(game, f"Compraste {offer['item']['name']}.")
    shop["items"].pop(index)


def leave_shop(game):
    game["shop"] = None
    complete_room(game)


def use_consumable(game, item_id):
    item = find_item_template(item_id)
    run = game.get("run")
    if not item or item.get("type") != "consumable":
        return
    if not run:
        add_log(game, "Los consumibles solo se pueden usar durante una expedición.")
        return
    if item.get("heal"):
        run["hp"] = min(run["max_hp"], run["hp"] + item["heal"])
        add_log(game, f"Usaste {item['name']} y curaste {item['heal']} de vida.")
    if item.get("buff") and game.get("combat"):
        buff = item["buff"]
        game["combat"].setdefault("player_buffs", []).append({"name": item["name"], "turns": buff.get("turns", 2), "stats": {"crit": buff.get("crit", 0)}})
        run["buffs"].append({"name": item["name"], "rooms": 1, "stats": {"crit": buff.get("crit", 0)}})
        add_log(game, f"Usaste {item['name']}: crítico temporal aumentado.")
    if item.get("flee_bonus") and run:
        run["temp_flee_bonus"] = run.get("temp_flee_bonus", 0) + item["flee_bonus"]
        add_log(game, f"Usaste {item['name']}: escapar será más fácil en este combate.")
    if item.get("cleanse") and run and run.get("debuffs"):
        removed = run["debuffs"].pop(0)
        add_log(game, f"Se limpió el debuff: {removed['name']}.")
    remove_item(game, item_id, 1)


def upgrade_inventory(game):
    current = game["inventory_slots"]
    level = max(0, (current - 12) // 3)
    cost = {"oro": 120 + level * 90, "madera": 25 + level * 15}
    if level >= 20:
        add_log(game, "La bodega ya está al máximo.")
        return
    if spend_resources(game, cost):
        game["inventory_slots"] += 3
        add_log(game, f"Inventario ampliado a {game['inventory_slots']} espacios.")
    else:
        add_log(game, "No tienes recursos suficientes para ampliar inventario.")


def upgrade_permanent(game, upgrade_id):
    up = next((u for u in UPGRADES if u["id"] == upgrade_id), None)
    if not up:
        return
    lvl = game["upgrades"].get(upgrade_id, 0)
    if lvl >= up["max"]:
        add_log(game, "Esta mejora ya está al máximo.")
        return
    cost = scale_cost(up["cost"], lvl)
    if spend_resources(game, cost):
        game["upgrades"][upgrade_id] = lvl + 1
        add_log(game, f"Mejora comprada: {up['name']} nivel {lvl + 1}.")
    else:
        add_log(game, "No tienes recursos suficientes para esta mejora.")


def crew_upgrade_cost(level):
    return {"oro": int(90 * (1.4 ** (level - 1))), "reputacion": max(1, level // 2)}


def upgrade_crew(game, crew_id):
    crew = game["crew"].get(crew_id)
    if not crew:
        return
    if crew["level"] >= 12:
        add_log(game, "Ese personaje ya está al máximo.")
        return
    cost = crew_upgrade_cost(crew["level"])
    if spend_resources(game, cost):
        crew["level"] += 1
        add_log(game, f"{crew['name']} subió a nivel {crew['level']}.")
    else:
        add_log(game, "No tienes recursos suficientes para entrenar a este personaje.")


def css():
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(180deg, #07111f 0%, #0b1728 55%, #101827 100%); color: #e5e7eb; }
        [data-testid="stSidebar"] { background: #08111f; }
        h1, h2, h3 { color: #f8fafc; }
        .card { background: rgba(15, 23, 42, 0.92); border: 1px solid rgba(148, 163, 184, 0.22); border-radius: 18px; padding: 18px; margin: 10px 0; box-shadow: 0 10px 30px rgba(0,0,0,0.18); }
        .soft { background: rgba(30, 41, 59, 0.68); border-radius: 14px; padding: 14px; margin: 8px 0; }
        .tiny { color: #cbd5e1; font-size: 0.92rem; }
        .good { color: #86efac; }
        .bad { color: #fca5a5; }
        .warn { color: #fdba74; }
        .muted { color: #94a3b8; }
        .big-number { font-size: 1.7rem; font-weight: 800; color: #f8fafc; }
        .map-room { padding: 10px 12px; border-radius: 14px; margin: 6px 0; border: 1px solid rgba(148,163,184,.22); background: rgba(15,23,42,.6); }
        .current-room { border: 1px solid #f97316; background: rgba(249,115,22,.12); }
        .done-room { opacity: .55; }
        .hpbar {height: 16px; border-radius: 999px; background: #1f2937; overflow: hidden; border: 1px solid rgba(255,255,255,.12);}
        .hpfill {height: 100%; background: linear-gradient(90deg, #ef4444, #f97316);}
        .enemyfill {height: 100%; background: linear-gradient(90deg, #7c3aed, #ef4444);}
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label, value, note=""):
    st.markdown(f"<div class='card'><div class='tiny'>{label}</div><div class='big-number'>{value}</div><div class='muted'>{note}</div></div>", unsafe_allow_html=True)


def hp_bar(current, maximum, enemy=False):
    pct = 0 if maximum <= 0 else clamp(current / maximum * 100, 0, 100)
    klass = "enemyfill" if enemy else "hpfill"
    st.markdown(f"<div class='hpbar'><div class='{klass}' style='width:{pct:.0f}%'></div></div>", unsafe_allow_html=True)


def sidebar(game):
    st.sidebar.title("Barco Maldito")
    st.sidebar.caption("Roguelike de expediciones")
    views = ["Puerto", "Expedición", "Inventario", "Mejoras", "Tripulación", "Estadísticas", "Ayuda"]
    for view in views:
        if st.sidebar.button(view, use_container_width=True):
            game["view"] = view
            save_game(game)
            st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Recursos")
    for key, info in RESOURCE_INFO.items():
        qty = game["resources"].get(key, 0)
        st.sidebar.write(f"{info['label']}: **{qty}**")

    st.sidebar.divider()
    stats = calc_ship_stats(game)
    st.sidebar.subheader("Barco")
    st.sidebar.write(f"Nivel **{game['ship']['level']}**")
    st.sidebar.write(f"Vida **{stats['max_hp']}** | Daño **{stats['damage']}**")
    st.sidebar.write(f"Defensa **{stats['defense']}** | Crítico **{stats['crit']}%**")

    st.sidebar.divider()
    if st.sidebar.button("Guardar partida", use_container_width=True):
        save_game(game)
        st.sidebar.success("Guardado")
    if st.sidebar.button("Reiniciar partida", use_container_width=True):
        reset_game()
        st.rerun()


def render_header(game):
    st.title("Barco Maldito: Roguelike de Expediciones")
    run = game.get("run")
    if run:
        port = PORTS[run["port"]]
        st.caption(f"Expedición activa en {port['name']} | Sala {run['depth']} de {run['max_depth']}")
    else:
        st.caption("Puerto seguro | Mejora tu barco, compra equipo y prepara la siguiente expedición")


def view_port(game):
    render_header(game)
    maybe_unlock_ports(game)
    cols = st.columns(4)
    stats = calc_ship_stats(game, include_run=False)
    with cols[0]: metric_card("Vida máxima", stats["max_hp"], "Casco total")
    with cols[1]: metric_card("Daño", stats["damage"], "Cañones")
    with cols[2]: metric_card("Defensa", stats["defense"], "Mitigación")
    with cols[3]: metric_card("Suerte", stats["luck"], "Mejor botín")

    st.subheader("Puertos")
    for port_id, port in PORTS.items():
        unlocked = port_id in game["unlocked_ports"]
        with st.container():
            st.markdown(f"<div class='card'><h3>{port['name']} <span class='muted'>({port['subtitle']})</span></h3><p>{port['desc']}</p><p class='tiny'>Mapa: {port['map_style']} | Salas: {port['length']} | Jefe: {port['boss']}</p></div>", unsafe_allow_html=True)
            if not unlocked:
                req = ", ".join(format_resource(k, v) for k, v in port["unlock"].items())
                st.warning(f"Bloqueado. Requiere: {req}")
            else:
                c1, c2 = st.columns([1, 2])
                with c1:
                    if st.button(f"Seleccionar {port['name']}", key=f"select_{port_id}", use_container_width=True):
                        game["selected_port"] = port_id
                        add_log(game, f"Puerto seleccionado: {port['name']}.")
                        save_game(game)
                        st.rerun()
                with c2:
                    selected = "Seleccionado" if game.get("selected_port") == port_id else "Disponible"
                    st.write(selected)

    st.divider()
    selected = game.get("selected_port", "puerto_bruma")
    if game.get("run"):
        st.info("Ya tienes una expedición activa. Entra a Expedición para continuar.")
        if st.button("Ir a expedición", use_container_width=True):
            game["view"] = "Expedición"
            save_game(game)
            st.rerun()
    else:
        port = PORTS[selected]
        fuel_cost = max(2, int(2 + port["difficulty"] * 2))
        st.markdown(f"### Iniciar desde {port['name']}")
        st.write(f"Costo de combustible: **{fuel_cost}**")
        if st.button("Iniciar expedición", type="primary", use_container_width=True):
            if start_run(game, selected):
                game["view"] = "Expedición"
            save_game(game)
            st.rerun()

    render_log(game)


def render_map(game):
    run = game.get("run")
    if not run:
        return
    st.subheader("Mapa de ruta")
    for i, room in enumerate(run["rooms"], start=1):
        cls = "map-room"
        if i == run["depth"]:
            cls += " current-room"
        if room.get("completed"):
            cls += " done-room"
        label = ROOM_LABELS.get(room["type"], room["type"])
        st.markdown(f"<div class='{cls}'><b>{i}. {label}</b> <span class='muted'>{rarity_badge(room['rarity'])}</span></div>", unsafe_allow_html=True)


def view_expedition(game):
    render_header(game)
    run = game.get("run")
    if not run:
        st.info("No tienes una expedición activa.")
        if st.button("Volver al puerto", use_container_width=True):
            game["view"] = "Puerto"
            save_game(game)
            st.rerun()
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Vida", f"{run['hp']} / {run['max_hp']}")
    with c2: metric_card("Moral", run["morale"])
    with c3: metric_card("Sala", f"{run['depth']} / {run['max_depth']}")
    with c4: metric_card("Botín oro", run["loot"].get("oro", 0))
    hp_bar(run["hp"], run["max_hp"])

    left, right = st.columns([2, 1])
    with right:
        render_map(game)
        if st.button("Regresar al puerto con el botín", use_container_width=True):
            abandon_run(game)
            save_game(game)
            st.rerun()

    with left:
        if game.get("combat"):
            render_combat(game)
        elif game.get("shop"):
            render_shop(game)
        else:
            room = current_room(game)
            if room:
                render_room(game, room)
    render_log(game)


def render_room(game, room):
    run = game["run"]
    label = ROOM_LABELS.get(room["type"], room["type"])
    st.markdown(f"<div class='card'><h2>{label}</h2><p class='tiny'>Rareza de sala: {rarity_badge(room['rarity'])}</p></div>", unsafe_allow_html=True)

    room_type = room["type"]
    if room_type in ["combate", "elite", "jefe"]:
        if room_type == "jefe":
            st.warning(f"El jefe de esta zona te espera: {PORTS[run['port']]['boss']}.")
        elif room_type == "elite":
            st.warning("Un enemigo élite bloquea la ruta. Mayor riesgo, mejor recompensa.")
        else:
            st.write("Un enemigo aparece entre las olas.")
        if st.button("Entrar en combate", type="primary", use_container_width=True):
            start_combat(game, room_type)
            save_game(game)
            st.rerun()

    elif room_type == "tesoro":
        st.write("Encuentras un cofre sellado con sal y cadenas oxidadas.")
        if st.button("Abrir tesoro", type="primary", use_container_width=True):
            resolve_treasure(game)
            save_game(game)
            st.rerun()

    elif room_type == "santuario":
        st.write("Un santuario marino ofrece una bendición.")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Bendecir casco", use_container_width=True):
                resolve_sanctuary(game, "bendicion_casco"); save_game(game); st.rerun()
        with c2:
            if st.button("Bendecir cañones", use_container_width=True):
                resolve_sanctuary(game, "bendicion_canones"); save_game(game); st.rerun()
        with c3:
            if st.button("Purgar maldición", use_container_width=True):
                resolve_sanctuary(game, "purgar"); save_game(game); st.rerun()

    elif room_type == "descanso":
        st.write("La marea está tranquila. Puedes recuperar fuerzas o buscar recursos.")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Reparar barco", use_container_width=True):
                resolve_rest(game, "reparar"); save_game(game); st.rerun()
        with c2:
            if st.button("Subir moral", use_container_width=True):
                resolve_rest(game, "moral"); save_game(game); st.rerun()
        with c3:
            if st.button("Saquear restos", use_container_width=True):
                resolve_rest(game, "saquear"); save_game(game); st.rerun()

    elif room_type == "tormenta":
        st.write("Una tormenta negra corta el camino.")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Cruzar", use_container_width=True):
                resolve_storm(game, "cruzar"); save_game(game); st.rerun()
        with c2:
            if st.button("Esperar", use_container_width=True):
                resolve_storm(game, "esperar"); save_game(game); st.rerun()
        with c3:
            if st.button("Usar radar", use_container_width=True):
                resolve_storm(game, "usar_radar"); save_game(game); st.rerun()

    elif room_type == "evento":
        stats = calc_ship_stats(game)
        if not run.get("current_event"):
            run["current_event"] = choose_event(stats)
        event = run["current_event"]
        st.write(f"**{event['title']}**")
        st.caption(f"Evento {rarity_badge(event['rarity'])}. La estadística útil aquí es: {event.get('stat', 'luck')}.")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Actuar con cuidado", use_container_width=True):
                resolve_event(game, "cuidadoso"); save_game(game); st.rerun()
        with c2:
            if st.button("Arriesgarse", use_container_width=True):
                resolve_event(game, "arriesgar"); save_game(game); st.rerun()
        with c3:
            if st.button("Ignorar", use_container_width=True):
                resolve_event(game, "ignorar"); save_game(game); st.rerun()

    elif room_type == "ruinas":
        st.write("Ruinas antiguas emergen del agua. Hay símbolos que nadie entiende.")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Explorar", use_container_width=True):
                resolve_ruins(game, "explorar"); save_game(game); st.rerun()
        with c2:
            if st.button("Usar dinamita", use_container_width=True):
                resolve_ruins(game, "dinamita"); save_game(game); st.rerun()
        with c3:
            if st.button("Marcar ruta", use_container_width=True):
                resolve_ruins(game, "marcar"); save_game(game); st.rerun()

    elif room_type == "trampa":
        st.write("Cadenas y minas flotantes cubren el paso.")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Desactivar", use_container_width=True):
                resolve_trap(game, "desactivar"); save_game(game); st.rerun()
        with c2:
            if st.button("Atravesar", use_container_width=True):
                resolve_trap(game, "atravesar"); save_game(game); st.rerun()
        with c3:
            if st.button("Rodear", use_container_width=True):
                resolve_trap(game, "rodear"); save_game(game); st.rerun()

    elif room_type == "npc":
        npc = random.choice(NPCS)
        st.write(f"Te encuentras con **{npc['name']}**.")
        st.caption(npc["desc"])
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Ayudar", use_container_width=True):
                resolve_npc(game, "ayudar"); save_game(game); st.rerun()
        with c2:
            if st.button("Comprar información", use_container_width=True):
                resolve_npc(game, "comprar_info"); save_game(game); st.rerun()
        with c3:
            if st.button("Robar", use_container_width=True):
                resolve_npc(game, "robar"); save_game(game); st.rerun()

    elif room_type in ["tienda", "mercado_negro"]:
        black = room_type == "mercado_negro"
        if not game.get("shop"):
            generate_shop(game, black=black)
        st.rerun()


def render_combat(game):
    combat = game["combat"]
    run = game["run"]
    enemy = combat["enemy"]
    st.markdown(f"<div class='card'><h2>Combate: {enemy['name']}</h2><p>{combat.get('message','')}</p></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.write("Tu barco")
        st.write(f"Vida: **{run['hp']} / {run['max_hp']}**")
        hp_bar(run["hp"], run["max_hp"])
        stats = calc_ship_stats(game)
        st.caption(f"Daño {stats['damage']} | Defensa {stats['defense']} | Crítico {stats['crit']}% | Velocidad {stats['speed']}")
    with c2:
        st.write(enemy["name"])
        st.write(f"Vida: **{max(0, combat['enemy_hp'])} / {enemy['hp']}**")
        hp_bar(max(0, combat["enemy_hp"]), enemy["hp"], enemy=True)
        st.caption(f"Daño {enemy['damage']} | Defensa {enemy['defense']} | Crítico {enemy['crit']}% | Velocidad {enemy['speed']}")

    st.subheader("Acciones")
    a, b, c = st.columns(3)
    with a:
        if st.button("Cañonazo", use_container_width=True):
            player_attack(game, "cañonazo"); save_game(game); st.rerun()
        if st.button("Defender", use_container_width=True):
            defend(game); save_game(game); st.rerun()
    with b:
        if st.button("Andanada pesada", use_container_width=True):
            player_attack(game, "andanada"); save_game(game); st.rerun()
        if st.button("Reparar", use_container_width=True):
            repair_action(game); save_game(game); st.rerun()
    with c:
        if st.button("Tiro preciso", use_container_width=True):
            player_attack(game, "tiro_preciso"); save_game(game); st.rerun()
        if st.button("Escapar", use_container_width=True):
            flee_action(game); save_game(game); st.rerun()

    st.subheader("Objetos rápidos")
    consumables = [i for i in game["inventory"] if i.get("type") == "consumable"]
    if not consumables:
        st.caption("No tienes consumibles.")
    else:
        cols = st.columns(min(4, len(consumables)))
        for idx, item in enumerate(consumables):
            with cols[idx % len(cols)]:
                if st.button(f"Usar {item['name']} x{item.get('qty',1)}", key=f"combat_use_{item['id']}_{idx}", use_container_width=True):
                    use_consumable(game, item["id"]); save_game(game); st.rerun()


def render_shop(game):
    shop = game["shop"]
    title = "Mercado negro" if shop.get("black") else "Tienda del puerto temporal"
    st.markdown(f"<div class='card'><h2>{title}</h2><p class='tiny'>Compra objetos, reliquias o consumibles. El mercado negro puede pedir perlas negras.</p></div>", unsafe_allow_html=True)
    for i, offer in enumerate(list(shop["items"])):
        item = offer["item"]
        price = offer["price"]
        currency = RESOURCE_INFO[offer["currency"]]["label"]
        with st.container():
            st.markdown(f"<div class='soft'><b>{item['name']}</b> <span class='muted'>{rarity_badge(item['rarity'])}</span><br><span class='tiny'>{item.get('desc','')}</span><br>Precio: <b>{price} {currency}</b></div>", unsafe_allow_html=True)
            if st.button(f"Comprar {item['name']}", key=f"buy_{i}", use_container_width=True):
                buy_shop_item(game, i)
                save_game(game)
                st.rerun()
    if st.button("Salir de la tienda", type="primary", use_container_width=True):
        leave_shop(game)
        save_game(game)
        st.rerun()


def view_inventory(game):
    render_header(game)
    st.subheader("Inventario")
    used = inventory_count(game)
    st.write(f"Espacios usados: **{used} / {game['inventory_slots']}**")
    c1, c2 = st.columns([1, 2])
    with c1:
        level = max(0, (game["inventory_slots"] - 12) // 3)
        cost = {"oro": 120 + level * 90, "madera": 25 + level * 15}
        st.write("Ampliar inventario: +3 espacios")
        st.caption("Costo: " + ", ".join(format_resource(k, v) for k, v in cost.items()))
        if st.button("Ampliar inventario", use_container_width=True):
            upgrade_inventory(game); save_game(game); st.rerun()
    with c2:
        st.info("Las reliquias en inventario dan efectos pasivos. Los consumibles se pueden usar en expedición o combate.")

    if not game["inventory"]:
        st.warning("Inventario vacío.")
        return
    for idx, item in enumerate(list(game["inventory"])):
        with st.container():
            st.markdown(f"<div class='card'><h3>{item['name']} x{item.get('qty',1)}</h3><p class='tiny'>{rarity_badge(item.get('rarity','comun'))} | {item.get('type','objeto')}</p><p>{item.get('desc','Sin descripción')}</p></div>", unsafe_allow_html=True)
            cols = st.columns(3)
            if item.get("type") == "consumable":
                with cols[0]:
                    if st.button("Usar", key=f"use_inv_{idx}", use_container_width=True):
                        use_consumable(game, item["id"]); save_game(game); st.rerun()
            with cols[1]:
                if st.button("Descartar", key=f"drop_{idx}", use_container_width=True):
                    remove_item(game, item["id"], 1); add_log(game, f"Descartaste {item['name']}."); save_game(game); st.rerun()
    render_log(game)


def view_upgrades(game):
    render_header(game)
    st.subheader("Mejoras permanentes")
    st.caption("Estas mejoras se quedan aunque pierdas una expedición.")
    for up in UPGRADES:
        lvl = game["upgrades"].get(up["id"], 0)
        cost = scale_cost(up["cost"], lvl)
        with st.container():
            st.markdown(f"<div class='card'><h3>{up['name']} <span class='muted'>Nivel {lvl}/{up['max']}</span></h3><p>{up['desc']}</p><p class='tiny'>{rarity_badge(up['rarity'])}</p></div>", unsafe_allow_html=True)
            if lvl >= up["max"]:
                st.success("Máximo")
            else:
                st.caption("Costo: " + ", ".join(format_resource(k, v) for k, v in cost.items()))
                if st.button(f"Mejorar {up['name']}", key=f"up_{up['id']}", use_container_width=True):
                    upgrade_permanent(game, up["id"]); save_game(game); st.rerun()
    render_log(game)


def view_crew(game):
    render_header(game)
    st.subheader("Personajes y tripulación")
    st.caption("Cada personaje suma estadísticas al barco.")
    for crew_id, crew in game["crew"].items():
        level = crew.get("level", 1)
        cost = crew_upgrade_cost(level)
        with st.container():
            st.markdown(f"<div class='card'><h3>{crew['name']} <span class='muted'>Nivel {level}/12</span></h3><p>{crew['bonus']}</p></div>", unsafe_allow_html=True)
            if level >= 12:
                st.success("Máximo")
            else:
                st.caption("Entrenar cuesta: " + ", ".join(format_resource(k, v) for k, v in cost.items()))
                if st.button(f"Entrenar {crew['name']}", key=f"crew_{crew_id}", use_container_width=True):
                    upgrade_crew(game, crew_id); save_game(game); st.rerun()
    render_log(game)


def view_stats(game):
    render_header(game)
    st.subheader("Estadísticas")
    stats = calc_ship_stats(game)
    cols = st.columns(4)
    keys = [("Vida", stats["max_hp"]), ("Daño", stats["damage"]), ("Defensa", stats["defense"]), ("Velocidad", stats["speed"]), ("Radar", stats["radar"]), ("Suerte", stats["luck"]), ("Crítico", f"{stats['crit']}%"), ("Moral", stats["morale"])]
    for idx, (label, value) in enumerate(keys):
        with cols[idx % 4]:
            metric_card(label, value)

    st.subheader("Historial")
    s = game["stats"]
    cols2 = st.columns(4)
    history = [("Runs", s.get("runs", 0)), ("Victorias", s.get("wins", 0)), ("Muertes", s.get("deaths", 0)), ("Salas", s.get("rooms_completed", 0)), ("Enemigos", s.get("enemies_defeated", 0)), ("Jefes", s.get("bosses_defeated", 0)), ("Oro ganado", s.get("gold_earned", 0)), ("Mejor profundidad", s.get("best_depth", 0))]
    for idx, (label, value) in enumerate(history):
        with cols2[idx % 4]:
            metric_card(label, value)
    render_log(game)


def view_help(game):
    render_header(game)
    st.markdown(
        """
        ## Cómo se juega

        Entras a una expedición desde un puerto, avanzas sala por sala y decides cuándo regresar.

        Si regresas vivo, conservas todo el botín de la expedición.

        Si mueres, conservas solo una parte.

        ## Ciclo principal

        1. Inicia una expedición.
        2. Supera salas de combate, eventos, tesoros, tormentas y NPC.
        3. Junta oro, madera, metal, cristales, reputación, fragmentos antiguos y perlas negras.
        4. Regresa al puerto.
        5. Compra mejoras permanentes, entrena tripulación y amplía inventario.
        6. Desbloquea nuevos puertos y repite.

        ## Combate

        Cañonazo es balanceado.

        Andanada pesada pega más, pero falla más.

        Tiro preciso pega menos, pero tiene más crítico.

        Defender reduce el daño recibido.

        Reparar consume turno.

        Escapar depende de velocidad, reliquias y objetos.

        ## Rarezas

        Común, poco común, raro, épico y legendario.

        Las rarezas afectan eventos, botín y reliquias.
        """
    )


def render_log(game):
    with st.expander("Registro de viaje", expanded=False):
        for line in game.get("log", [])[:30]:
            st.write(line)


def main():
    st.set_page_config(page_title="Barco Maldito", page_icon="BM", layout="wide")
    css()
    init_state()
    game = st.session_state.game
    maybe_unlock_ports(game)
    sidebar(game)

    view = game.get("view", "Puerto")
    if view == "Puerto":
        view_port(game)
    elif view == "Expedición":
        view_expedition(game)
    elif view == "Inventario":
        view_inventory(game)
    elif view == "Mejoras":
        view_upgrades(game)
    elif view == "Tripulación":
        view_crew(game)
    elif view == "Estadísticas":
        view_stats(game)
    elif view == "Ayuda":
        view_help(game)
    else:
        view_port(game)

    save_game(game)


if __name__ == "__main__":
    main()
