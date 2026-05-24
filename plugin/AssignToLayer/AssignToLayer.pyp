# -*- coding: utf-8 -*-
"""
AssignToLayer — v1.5.1
Cinema 4D Command Plugin (.pyp) — kompatibilní s C4D 2024+ / 2026

Autor konceptu / zadání: Ondřej Bahula
Kódování / implementace: ChatGPT (OpenAI)


v1.5.1:
- Opravena šířka sloupce v seznamu vrstev.
- Odstraněno horizontální šoupátko pod seznamem vrstev.
- Pozadí řádku se kreslí pouze do reálné šířky sloupce, aby seznam nebyl širší než okno.

v1.5.0:
- Sloučena česká a anglická verze do jednoho pluginu.
- Oficiální Maxon Plugin ID: 1068663.
- Jazyk GUI se automaticky volí podle jazykového nastavení Cinema 4D.
- Pokud není jazyk rozpoznán jako čeština, plugin použije angličtinu.
- Zachována migrace posledních nastavení ze starých CS/EN testovacích ID.

v1.4.3:
- Opravena šířka vykreslovaného sloupce v TreeView seznamu vrstev.
- Pozadí vybraného i střídavých řádků nyní dobíhá až k pravému okraji seznamu.
- Zachováno pamatování poslední vrstvy a volby přepisu z v1.4.2.

v1.4.2:
- Plugin si pamatuje poslední cílovou vrstvu a stav volby „přepsat existující vrstvy“.
- Při dalším spuštění automaticky předvybere naposledy použitou vrstvu, pokud ve scéně stále existuje.
- Pole „Nová vrstva“ zůstává záměrně prázdné, aby nová vrstva omylem nepřebila ruční výběr.

v1.4.1:
- Opravena černá plocha za názvy vrstev v TreeView seznamu.
- Pozadí řádků seznamu se kreslí přes celou dostupnou šířku.
- Zúžené a kompaktnější dialogové okno.

v1.4.0:
- ComboBox s emoji značkami nahrazen skutečným vlastním seznamem vrstev přes TreeViewCustomGui.
- Každá vrstva se vykresluje s reálným barevným čtvercem podle barvy vrstvy v Layer Manageru.
- Kompaktnější layout dialogu s nižšími řádky.
- Přidán fallback na původní ComboBox, pokud by TreeViewCustomGui v konkrétní instalaci C4D selhal.

v1.3.4:
- Opravena detekce barvy vrstvy v C4D 2024.1+: GetLayerData() vrací slovník s klíčem "color".
- Zachován kompaktní dialog; zmenšená výška na 220 px.

v1.3.3:
- Zobrazení barev vrstev v rozbalovacím seznamu pomocí barevné značky před názvem vrstvy.
- Zmenšené a kompaktnější dialogové okno.
- Menší výšky řádků a menší okraje dialogu.

v1.3.2:
- Upřesněna a zpevněna kompatibilita dialogu pro Cinema 4D 2024.1.
- Dialog používá kompaktní pevné výšky prvků, aby se neztratila tlačítka OK / Zrušit.

v1.3.1:
- Opravena výška dialogu a pevné výšky polí, aby se ve starších i novějších verzích C4D neztratila tlačítka OK / Zrušit.

v1.3.0:
- Přidána volba v dialogu: přepsat / nepřepsat existující vrstvu objektu.
- Pokud je přepis vypnutý, objekty s již přiřazenou vrstvou se přeskočí.
- Přidáno závěrečné hlášení s počtem přiřazených a přeskočených objektů.
- Opravena chyba v závěrečném print() řádku z balíčku v1.2.2.
- Opraven název složky balíčku na AssignToLayer_CS.

v1.2.2:
- Samostatná česká jazyková mutace.

v1.5.0 je první sjednocený oficiální build. Staré CS/EN buildy je vhodné z pluginů odstranit.

Poznámka:
Cinema 4D Python ComboBox neumí kreslit vlastní barevné čtverce v položkách seznamu.
Proto v1.4.0 používá TreeViewCustomGui + vlastní DrawCell(), kde se barva kreslí ručně.
"""

import os
import locale
import c4d
from c4d import gui, plugins, bitmaps

PLUGIN_ID = 1068663
PLUGIN_VERSION = "1.5.1"
LEGACY_PLUGIN_IDS = (10698781, 10698782)

# Interní ID pro uložené preference pluginu.
# Ukládá se přes c4d.plugins.GetWorldPluginData / SetWorldPluginData.
PREF_SELECTED_LAYER_PATH = 10001
PREF_OVERWRITE_EXISTING = 10002

TXT = {
    "en": {
        "cmd_name": "AssignToLayer",
        "help": "Assign selected branch to a Layer.",
        "dlg_title": "AssignToLayer v{ver}",
        "tip": "Tip: New layer has priority. Selecting a child takes its parent branch.",
        "existing": "Existing layer:",
        "new": "New layer (priority):",
        "overwrite_existing": "Overwrite existing layer on objects that already have a layer",
        "ok": "OK",
        "cancel": "Cancel",
        "msg_select_one": "Select at least one object in the Object Manager.",
        "msg_no_layerroot": "Layer Root not found.",
        "msg_no_target": "No layer selected or created.",
        "msg_no_objects": "No objects to assign.",
        "msg_done": "Done.\nAssigned: {assigned}\nSkipped: {skipped}"
    },
    "cs": {
        "cmd_name": "AssignToLayer",
        "help": "Přiřadí vybranou větev objektů do vrstvy.",
        "dlg_title": "AssignToLayer v{ver}",
        "tip": "Tip: Nová vrstva má přednost. Výběr dítěte vezme větev nejbližšího rodiče.",
        "existing": "Existující vrstva:",
        "new": "Nová vrstva (priorita):",
        "overwrite_existing": "Přepsat existující vrstvu u objektů, které už nějakou vrstvu mají",
        "ok": "OK",
        "cancel": "Zrušit",
        "msg_select_one": "Vyber alespoň jeden objekt v Object Manageru.",
        "msg_no_layerroot": "Nebyl nalezen Layer Root.",
        "msg_no_target": "Nevybral jsi vrstvu ani nevytvořil novou.",
        "msg_no_objects": "Nebyl nalezen žádný objekt k přiřazení.",
        "msg_done": "Hotovo.\nPřiřazeno: {assigned}\nPřeskočeno: {skipped}"
    }
}


def _normalize_language_token(raw):
    """Vrátí interní jazykový kód pluginu podle textu z C4D / systému."""
    if not raw:
        return None
    s = str(raw).lower()

    # Cinema 4D většinou vrací extensions jako en-US, de-DE, cs-CZ apod.
    # Pro tento plugin cíleně podporujeme CS a EN. Vše ostatní padá do EN.
    if "cs" in s or "cz" in s or "czech" in s or "češt" in s or "cesk" in s:
        return "cs"
    if "en" in s or "english" in s:
        return "en"
    return None


def _lang_from_c4d():
    """Pokusí se zjistit jazyk přímo z Cinema 4D přes c4d.GeGetLanguage()."""
    try:
        index = 0
        while True:
            lang = c4d.GeGetLanguage(index)
            if lang is None:
                break

            try:
                is_default = bool(lang.get("default_language", False))
            except Exception:
                try:
                    is_default = bool(lang["default_language"])
                except Exception:
                    is_default = False

            if is_default:
                parts = []
                for key in ("extensions", "name"):
                    try:
                        value = lang.get(key, "")
                    except Exception:
                        try:
                            value = lang[key]
                        except Exception:
                            value = ""
                    if value:
                        parts.append(str(value))

                detected = _normalize_language_token(" ".join(parts))
                return detected or "en"

            index += 1
    except Exception:
        return None

    return None


def _lang_from_locale():
    """Fallback podle OS / Python locale, pokud C4D jazyk nejde zjistit."""
    candidates = []
    for k in ("LC_ALL", "LANG", "LC_MESSAGES"):
        v = os.environ.get(k)
        if v:
            candidates.append(v)
    try:
        loc = locale.getdefaultlocale()[0]
        if loc:
            candidates.append(loc)
    except Exception:
        pass
    try:
        loc2 = locale.getlocale()[0]
        if loc2:
            candidates.append(loc2)
    except Exception:
        pass

    detected = _normalize_language_token(" ".join([c for c in candidates if c]))
    return detected or "en"


def _detect_language():
    """CS, když je C4D česky; jinak EN."""
    return _lang_from_c4d() or _lang_from_locale() or "en"


_LANG = _detect_language()


def T(key):
    return TXT.get(_LANG, TXT["en"]).get(key, TXT["en"].get(key, ""))


def _plugin_dir():
    return os.path.dirname(__file__)


def _load_icon():
    base = _plugin_dir()
    p = os.path.join(base, "res", "icons", "AssignToLayer.tif")
    bmp = bitmaps.BaseBitmap()
    res, _ = bmp.InitWith(p)
    if res == c4d.IMAGERESULT_OK:
        return bmp
    return None


def _iter_layers_recursive(layer_root):
    layers = []
    if not layer_root:
        return layers

    def walk(l):
        for ch in l.GetChildren():
            layers.append(ch)
            walk(ch)

    walk(layer_root)
    return layers


def _layer_depth(layer, layer_root):
    """Vrátí zanoření vrstvy vůči Layer Rootu pro odsazení v seznamu."""
    if layer is None or layer_root is None:
        return 0
    depth = 0
    try:
        parent = layer.GetUp()
        while parent is not None and parent != layer_root:
            depth += 1
            parent = parent.GetUp()
    except Exception:
        depth = 0
    return max(0, depth)


def _layer_path(layer, layer_root):
    """Vrátí jednoduchou cestu vrstvy v hierarchii, např. GEO/Konstrukce."""
    if layer is None:
        return ""

    names = []
    cur = layer
    try:
        while cur is not None and cur != layer_root:
            names.append(cur.GetName())
            cur = cur.GetUp()
    except Exception:
        try:
            return layer.GetName()
        except Exception:
            return ""

    names.reverse()
    return "/".join(names)


def _find_layer_by_path(layers, layer_root, path):
    if not path:
        return None
    for layer in layers:
        if _layer_path(layer, layer_root) == path:
            return layer
    return None


def _find_layer_by_name(layers, name):
    for l in layers:
        if l.GetName() == name:
            return l
    return None


def _layer_color_vector(layer, doc):
    """Vrátí barvu vrstvy jako c4d.Vector v rozsahu 0..1, nebo None."""
    if layer is None or doc is None:
        return None

    data = None
    try:
        data = layer.GetLayerData(doc, True)
    except TypeError:
        try:
            data = layer.GetLayerData(doc)
        except Exception:
            data = None
    except Exception:
        data = None

    if not data:
        return None

    col = None

    try:
        if isinstance(data, dict):
            col = data.get("color", None)
    except Exception:
        col = None

    if col is None:
        try:
            col = data["color"]
        except Exception:
            col = None

    if col is None:
        key = getattr(c4d, "ID_LAYER_COLOR", None)
        if key is not None:
            try:
                col = data[key]
            except Exception:
                try:
                    col = data.GetVector(key)
                except Exception:
                    col = None

    if col is None:
        return None

    try:
        return c4d.Vector(float(col.x), float(col.y), float(col.z))
    except Exception:
        pass

    try:
        return c4d.Vector(float(col[0]), float(col[1]), float(col[2]))
    except Exception:
        return None


def _clamp01(v):
    try:
        return max(0.0, min(1.0, float(v)))
    except Exception:
        return 0.0


def _safe_color(col):
    if col is None:
        return c4d.Vector(0.45, 0.45, 0.45)
    return c4d.Vector(_clamp01(col.x), _clamp01(col.y), _clamp01(col.z))


def _lighten(col, amount=0.18):
    col = _safe_color(col)
    return c4d.Vector(
        _clamp01(col.x + (1.0 - col.x) * amount),
        _clamp01(col.y + (1.0 - col.y) * amount),
        _clamp01(col.z + (1.0 - col.z) * amount)
    )


def _darken(col, amount=0.28):
    col = _safe_color(col)
    return c4d.Vector(
        _clamp01(col.x * (1.0 - amount)),
        _clamp01(col.y * (1.0 - amount)),
        _clamp01(col.z * (1.0 - amount))
    )


def _color_marker(name_cs, name_en):
    return "[{0}]".format(name_cs if _LANG == "cs" else name_en)


def _rgb_to_layer_marker(col):
    """Fallback pro ComboBox, pokud by TreeView v konkrétní instalaci C4D selhal."""
    if col is None:
        return _color_marker("barva", "color")

    r = _clamp01(col.x)
    g = _clamp01(col.y)
    b = _clamp01(col.z)

    mx = max(r, g, b)
    mn = min(r, g, b)
    delta = mx - mn

    if mx < 0.18:
        return _color_marker("černá", "black")
    if delta < 0.10:
        if mx > 0.78:
            return _color_marker("bílá", "white")
        return _color_marker("šedá", "gray")

    if mx == r:
        h = (60.0 * ((g - b) / delta) + 360.0) % 360.0
    elif mx == g:
        h = 60.0 * ((b - r) / delta) + 120.0
    else:
        h = 60.0 * ((r - g) / delta) + 240.0

    if 15.0 <= h < 45.0 and mx < 0.65:
        return _color_marker("hnědá", "brown")
    if h < 15.0 or h >= 330.0:
        return _color_marker("červená", "red")
    if h < 45.0:
        return _color_marker("oranžová", "orange")
    if h < 75.0:
        return _color_marker("žlutá", "yellow")
    if h < 165.0:
        return _color_marker("zelená", "green")
    if h < 255.0:
        return _color_marker("modrá", "blue")
    if h < 330.0:
        return _color_marker("fialová", "purple")
    return _color_marker("barva", "color")


def _layer_display_name(layer, doc):
    marker = _rgb_to_layer_marker(_layer_color_vector(layer, doc))
    try:
        name = layer.GetName()
    except Exception:
        name = "Vrstva"
    return "{0}  {1}".format(marker, name)


def _get_object_layer(obj, doc):
    """Vrátí aktuálně přiřazenou vrstvu objektu, nebo None."""
    if obj is None:
        return None
    try:
        return obj.GetLayerObject(doc)
    except TypeError:
        try:
            return obj.GetLayerObject()
        except Exception:
            return None
    except Exception:
        return None


def _collect_descendants(op, out, seen):
    ch = op.GetDown()
    while ch:
        cid = id(ch)
        if cid not in seen:
            seen.add(cid)
            out.append(ch)
            _collect_descendants(ch, out, seen)
        ch = ch.GetNext()


def _collect_subtree(root, out, seen):
    rid = id(root)
    if rid not in seen:
        seen.add(rid)
        out.append(root)
    _collect_descendants(root, out, seen)


def _build_assignment_list(selected_ops):
    out = []
    seen = set()
    for op in selected_ops:
        if not op:
            continue
        parent = op.GetUp()
        has_children = (op.GetDown() is not None)
        root = op if (has_children or parent is None) else parent
        _collect_subtree(root, out, seen)
    return out


def _bc_set_int(bc, key, value):
    """Kompatibilní nastavení int hodnoty do BaseContaineru napříč verzemi C4D."""
    try:
        bc.SetInt32(key, int(value))
    except AttributeError:
        bc.SetLong(key, int(value))


def _bc_set_bool(bc, key, value):
    try:
        bc.SetBool(key, bool(value))
    except AttributeError:
        bc.SetInt32(key, 1 if value else 0)


def _bc_set_string(bc, key, value):
    try:
        bc.SetString(key, str(value or ""))
    except AttributeError:
        bc[key] = str(value or "")


def _bc_has_key(bc, key):
    if bc is None:
        return False
    try:
        return int(bc.FindIndex(key)) >= 0
    except Exception:
        pass
    try:
        value = bc[key]
        return value is not None
    except Exception:
        return False


def _bc_get_string(bc, key, default=""):
    if bc is None or not _bc_has_key(bc, key):
        return default
    try:
        return bc.GetString(key) or default
    except Exception:
        try:
            value = bc[key]
            return str(value) if value is not None else default
        except Exception:
            return default


def _bc_get_bool(bc, key, default=False):
    if bc is None or not _bc_has_key(bc, key):
        return bool(default)
    try:
        return bool(bc.GetBool(key))
    except Exception:
        try:
            value = bc[key]
            return bool(value)
        except Exception:
            return bool(default)


def _load_plugin_settings():
    """Načte poslední volby pluginu z preferencí C4D.

    v1.5.0: nejdřív čte oficiální Plugin ID 1068663.
    Pokud nic nenajde, pokusí se převzít nastavení ze starých testovacích CS/EN ID.
    """
    settings = {
        "selected_layer_path": "",
        "overwrite_existing": True
    }

    ids_to_try = [PLUGIN_ID]
    try:
        ids_to_try.extend(list(LEGACY_PLUGIN_IDS))
    except Exception:
        pass

    for pid in ids_to_try:
        bc = None
        try:
            bc = plugins.GetWorldPluginData(pid)
        except Exception:
            bc = None

        if bc is None:
            continue

        has_layer = _bc_has_key(bc, PREF_SELECTED_LAYER_PATH)
        has_overwrite = _bc_has_key(bc, PREF_OVERWRITE_EXISTING)
        if not has_layer and not has_overwrite:
            continue

        settings["selected_layer_path"] = _bc_get_string(bc, PREF_SELECTED_LAYER_PATH, "")
        settings["overwrite_existing"] = _bc_get_bool(bc, PREF_OVERWRITE_EXISTING, True)
        break

    return settings


def _save_plugin_settings(target_layer, layer_root, overwrite_existing):
    """Uloží poslední cílovou vrstvu a checkbox přepisu pro další spuštění."""
    bc = c4d.BaseContainer()
    _bc_set_string(bc, PREF_SELECTED_LAYER_PATH, _layer_path(target_layer, layer_root))
    _bc_set_bool(bc, PREF_OVERWRITE_EXISTING, bool(overwrite_existing))

    try:
        plugins.SetWorldPluginData(PLUGIN_ID, bc, False)
    except TypeError:
        try:
            plugins.SetWorldPluginData(PLUGIN_ID, bc)
        except Exception:
            pass
    except Exception:
        pass


class LayerItem(object):
    def __init__(self, layer, doc, layer_root=None, depth=0):
        self.layer = layer
        self.depth = int(depth)
        self.color = _safe_color(_layer_color_vector(layer, doc))
        self.path = _layer_path(layer, layer_root)
        try:
            self.name = layer.GetName()
        except Exception:
            self.name = "Vrstva"


class LayerTreeFunctions(gui.TreeViewFunctions):
    """Vlastní kreslení seznamu vrstev s reálnými barevnými čtverci."""

    COL_LAYER = 1

    def __init__(self, owner):
        super(LayerTreeFunctions, self).__init__()
        self.owner = owner

    def GetFirst(self, root, userdata):
        return root[0] if root else None

    def GetNext(self, root, userdata, obj):
        try:
            i = root.index(obj)
            return root[i + 1]
        except Exception:
            return None

    def GetPred(self, root, userdata, obj):
        try:
            i = root.index(obj)
            return root[i - 1] if i > 0 else None
        except Exception:
            return None

    def GetDown(self, root, userdata, obj):
        return None

    def GetName(self, root, userdata, obj):
        return obj.name if obj else ""

    def IsOpened(self, root, userdata, obj):
        return True

    def Open(self, root, userdata, obj, onoff):
        return True

    def IsSelectable(self, root, userdata, obj):
        return True

    def IsSelected(self, root, userdata, obj):
        return obj is not None and obj == self.owner.selected_item

    def Select(self, root, userdata, obj, mode):
        if obj is None:
            return
        if mode in (c4d.SELECTION_NEW, c4d.SELECTION_ADD):
            self.owner.selected_item = obj
        elif mode == c4d.SELECTION_SUB and self.owner.selected_item == obj:
            self.owner.selected_item = None

    def SelectionChanged(self, root, userdata):
        return

    def GetLineHeight(self, root, userdata, obj, col, area):
        return 18

    def GetColumnWidth(self, root, userdata, obj, col, area):
        # v1.5.1:
        # Původní hodnota 2000 px vyřešila krátké pozadí řádku, ale v C4D 2024
        # zapnula horizontální scrollbar. Teď držíme sloupec přibližně ve viditelné
        # šířce seznamu pro kompaktní dialog 430 px.
        # Pokud se v budoucnu změní šířka dialogu, upravit hlavně tuto hodnotu.
        return 400

    def GetColors(self, root, userdata, obj, pNormal, pSelected):
        return (c4d.Vector(0.86, 0.86, 0.86), c4d.Vector(1.0, 1.0, 1.0))

    def DrawCell(self, root, userdata, obj, col, drawinfo, bgcolor):
        if obj is None:
            return bgcolor

        ua = drawinfo.get("frame", None)
        if ua is None:
            return bgcolor

        x = int(drawinfo.get("xpos", 0))
        y = int(drawinfo.get("ypos", 0))
        w = int(drawinfo.get("width", 300))
        h = int(drawinfo.get("height", 18))
        selected = (obj == self.owner.selected_item)

        # Vlastní pozadí řádku.
        # v1.5.1: nekreslíme už extrémně širokou plochu, protože ta v C4D 2024
        # vyvolá horizontální scrollbar. Šířku drží GetColumnWidth().
        if selected:
            row_bg = c4d.Vector(0.26, 0.36, 0.55)
        else:
            # jemně střídavé řádky
            try:
                line = int(drawinfo.get("line", 0))
            except Exception:
                line = 0
            shade = 0.155 if line % 2 == 0 else 0.125
            row_bg = c4d.Vector(shade, shade, shade)
        ua.DrawSetPen(row_bg)
        ua.DrawRectangle(x, y, x + w, y + h)

        indent = 8 + (obj.depth * 14)
        sw = 12
        sy = y + max(3, int((h - sw) * 0.5))
        sx = x + indent

        # Jemný tmavý rámeček swatche.
        ua.DrawSetPen(_darken(obj.color, 0.45))
        ua.DrawRectangle(sx - 1, sy - 1, sx + sw, sy + sw)

        # Skutečná barva vrstvy.
        ua.DrawSetPen(_lighten(obj.color, 0.04))
        ua.DrawRectangle(sx, sy, sx + sw - 1, sy + sw - 1)

        # Malý světlý horní okraj pro čitelnost u tmavých barev.
        ua.DrawSetPen(_lighten(obj.color, 0.32))
        ua.DrawLine(sx, sy, sx + sw - 1, sy)

        # Název vrstvy.
        try:
            ua.DrawSetFont(c4d.FONT_DEFAULT)
        except Exception:
            pass

        if selected:
            txt_col = c4d.Vector(1.0, 1.0, 1.0)
        else:
            txt_col = c4d.Vector(0.84, 0.84, 0.84)

        try:
            ua.DrawSetTextCol(txt_col, row_bg)
        except Exception:
            ua.DrawSetPen(txt_col)

        try:
            fh = int(ua.DrawGetFontHeight())
        except Exception:
            fh = 12

        text_x = sx + sw + 9
        text_y = y + max(1, int((h - fh) * 0.5))
        ua.DrawText(obj.name, text_x, text_y)
        return bgcolor


class AssignDialog(gui.GeDialog):
    IDC_LAYER_TREE = 1000
    IDC_DROPDOWN  = 1001
    IDC_NEWINPUT  = 1002
    IDC_OK        = 1003
    IDC_CANCEL    = 1004
    IDC_TIP       = 1005
    IDC_OVERWRITE = 1006

    def __init__(self, layers, doc=None, layer_root=None, settings=None):
        super(AssignDialog, self).__init__()
        self.layers = layers
        self.doc = doc
        self.layer_root = layer_root
        self.settings = settings or {}
        self.layer_items = [LayerItem(layer, doc, layer_root, _layer_depth(layer, layer_root)) for layer in layers]
        self.selected_item = None
        self.selected_layer = None
        self.new_layer_name = ""
        self.overwrite_existing = bool(self.settings.get("overwrite_existing", True))
        self.initial_combo_index = 0
        self.tree_gui = None
        self.tree_funcs = None
        self.using_tree = False

        preferred_path = self.settings.get("selected_layer_path", "")
        if preferred_path:
            for i, item in enumerate(self.layer_items):
                if item.path == preferred_path:
                    self.selected_item = item
                    self.initial_combo_index = i
                    break

        if self.selected_item is None and self.layer_items:
            self.selected_item = self.layer_items[0]
            self.initial_combo_index = 0

    def _create_tree_view(self):
        settings = c4d.BaseContainer()
        _bc_set_int(settings, c4d.TREEVIEW_BORDER, c4d.BORDER_THIN_IN)
        _bc_set_bool(settings, c4d.TREEVIEW_HIDE_LINES, True)
        _bc_set_bool(settings, c4d.TREEVIEW_NO_MULTISELECT, True)
        _bc_set_bool(settings, c4d.TREEVIEW_FIXED_LAYOUT, True)
        _bc_set_bool(settings, c4d.TREEVIEW_NO_BACK_DELETE, True)
        _bc_set_bool(settings, c4d.TREEVIEW_NO_DELETE, True)
        if hasattr(c4d, "TREEVIEW_VERTICAL_SPACE"):
            _bc_set_int(settings, c4d.TREEVIEW_VERTICAL_SPACE, 0)

        self.tree_gui = self.AddCustomGui(
            self.IDC_LAYER_TREE,
            c4d.CUSTOMGUI_TREEVIEW,
            "",
            c4d.BFH_SCALEFIT | c4d.BFV_TOP,
            0,
            68,
            settings
        )
        if not self.tree_gui:
            return False

        self.tree_funcs = LayerTreeFunctions(self)
        layout = c4d.BaseContainer()
        _bc_set_int(layout, LayerTreeFunctions.COL_LAYER, c4d.LV_USERTREE)
        try:
            self.tree_gui.SetLayout(1, layout)
            self.tree_gui.SetRoot(self.layer_items, self.tree_funcs, None)
            self.tree_gui.Refresh()
            self.using_tree = True
            return True
        except Exception:
            self.using_tree = False
            return False

    def _create_combo_fallback(self):
        self.AddComboBox(self.IDC_DROPDOWN, c4d.BFH_SCALEFIT | c4d.BFV_TOP, initw=0, inith=20)
        for i, layer in enumerate(self.layers):
            self.AddChild(self.IDC_DROPDOWN, i, _layer_display_name(layer, self.doc))
        if self.layers:
            self.SetInt32(self.IDC_DROPDOWN, self.initial_combo_index)
        else:
            self.Enable(self.IDC_DROPDOWN, False)

    def CreateLayout(self):
        self.SetTitle(T("dlg_title").format(ver=PLUGIN_VERSION))

        # v1.4.0: kompaktní layout + skutečný barevný seznam přes TreeViewCustomGui.
        self.GroupBorderSpace(8, 6, 8, 8)
        self.GroupSpace(3, 3)

        tip = T("tip")
        if tip:
            self.AddStaticText(self.IDC_TIP, c4d.BFH_SCALEFIT | c4d.BFV_TOP, initw=0, inith=13, name=tip)

        self.AddStaticText(2000, c4d.BFH_LEFT | c4d.BFV_TOP, initw=0, inith=13, name=T("existing"))

        if self.layer_items:
            if not self._create_tree_view():
                self._create_combo_fallback()
        else:
            self._create_combo_fallback()

        self.AddStaticText(2001, c4d.BFH_LEFT | c4d.BFV_TOP, initw=0, inith=13, name=T("new"))
        self.AddEditText(self.IDC_NEWINPUT, c4d.BFH_SCALEFIT | c4d.BFV_TOP, initw=0, inith=20)

        self.AddCheckbox(self.IDC_OVERWRITE, c4d.BFH_SCALEFIT | c4d.BFV_TOP, initw=0, inith=17, name=T("overwrite_existing"))
        self.SetBool(self.IDC_OVERWRITE, self.overwrite_existing)

        self.AddSeparatorH(0, c4d.BFH_SCALEFIT)

        self.GroupBegin(3000, c4d.BFH_CENTER | c4d.BFV_TOP, 2, 1)
        self.GroupSpace(8, 0)
        self.AddButton(self.IDC_OK, c4d.BFH_LEFT | c4d.BFV_TOP, initw=74, inith=22, name=T("ok"))
        self.AddButton(self.IDC_CANCEL, c4d.BFH_LEFT | c4d.BFV_TOP, initw=74, inith=22, name=T("cancel"))
        self.GroupEnd()
        return True

    def Command(self, _id, _msg):
        if _id == self.IDC_OK:
            if self.using_tree:
                self.selected_layer = self.selected_item.layer if self.selected_item else None
            else:
                idx = self.GetInt32(self.IDC_DROPDOWN)
                self.selected_layer = self.layers[idx] if (self.layers and 0 <= idx < len(self.layers)) else None

            self.new_layer_name = (self.GetString(self.IDC_NEWINPUT) or "").strip()
            self.overwrite_existing = self.GetBool(self.IDC_OVERWRITE)
            self.Close(True)
        elif _id == self.IDC_CANCEL:
            self.Close(False)
        return True


class AssignToLayerCommand(plugins.CommandData):
    def Execute(self, doc):
        if doc is None:
            return False

        sel = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_0)
        if not sel:
            gui.MessageDialog(T("msg_select_one"))
            return True

        layer_root = doc.GetLayerObjectRoot()
        layers = _iter_layers_recursive(layer_root)
        settings = _load_plugin_settings()

        dlg = AssignDialog(layers, doc, layer_root, settings)
        if not dlg.Open(c4d.DLG_TYPE_MODAL, defaultw=430, defaulth=235):
            return True

        target_layer = None
        assigned_count = 0
        skipped_count = 0

        doc.StartUndo()
        try:
            if dlg.new_layer_name:
                existing = _find_layer_by_name(layers, dlg.new_layer_name)
                if existing:
                    target_layer = existing
                else:
                    if not layer_root:
                        gui.MessageDialog(T("msg_no_layerroot"))
                        return True
                    new_layer = c4d.documents.LayerObject()
                    new_layer.SetName(dlg.new_layer_name)
                    new_layer.InsertUnderLast(layer_root)
                    doc.AddUndo(c4d.UNDOTYPE_NEW, new_layer)
                    target_layer = new_layer
            else:
                target_layer = dlg.selected_layer

            if not target_layer:
                gui.MessageDialog(T("msg_no_target"))
                return True

            to_assign = _build_assignment_list(sel)
            if not to_assign:
                gui.MessageDialog(T("msg_no_objects"))
                return True

            for obj in to_assign:
                if not dlg.overwrite_existing:
                    current_layer = _get_object_layer(obj, doc)
                    if current_layer is not None:
                        skipped_count += 1
                        continue

                doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                obj.SetLayerObject(target_layer)
                assigned_count += 1

            _save_plugin_settings(target_layer, layer_root, dlg.overwrite_existing)

        finally:
            doc.EndUndo()

        c4d.EventAdd()
        gui.MessageDialog(T("msg_done").format(assigned=assigned_count, skipped=skipped_count))
        return True


if __name__ == "__main__":
    print("[AssignToLayer] loaded (v{ver}, lang={lang}, id={pid})".format(ver=PLUGIN_VERSION, lang=_LANG, pid=PLUGIN_ID))

    icon = _load_icon()
    plugins.RegisterCommandPlugin(
        id=PLUGIN_ID,
        str=T("cmd_name"),
        info=0,
        icon=icon,
        help=T("help"),
        dat=AssignToLayerCommand()
    )
