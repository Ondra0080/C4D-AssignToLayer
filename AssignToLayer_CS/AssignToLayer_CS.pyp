"""
AssignToLayer (CS) — v1.2.2-cs
Cinema 4D Command Plugin (.pyp) — kompatibilní s C4D 2024+

Autor konceptu / zadání: Ondřej Bahula
Kódování / implementace: ChatGPT (OpenAI)

v1.2.0:
- Runtime lokalizace CZ / EN / DE.
- Vylepšená detekce jazyka: C4D jazyk + fallback přes OS locale (Mac/Win).
- Konzole: pouze 1 info řádek při načtení (verze).

Poznámka:
Cinema 4D Python Command plugin neumí spolehlivě lok. dialog přes .str,
proto řešíme jazyk runtime v kódu.
"""

import os
import locale
import c4d
from c4d import gui, plugins, bitmaps

PLUGIN_ID = 10698781
PLUGIN_VERSION = "1.2.2-cs"

TXT = {
    "en": {
        "cmd_name": "Assign To Layer",
        "help": "Assign selected branch to a Layer.",
        "dlg_title": "AssignToLayer v{ver}",
        "tip": "Tip: New layer has priority. Selecting a child takes its parent branch.",
        "existing": "Existing layer:",
        "new": "New layer (priority):",
        "ok": "OK",
        "cancel": "Cancel",
        "msg_select_one": "Select at least one object in the Object Manager.",
        "msg_no_layerroot": "Layer Root not found.",
        "msg_no_target": "No layer selected or created.",
        "msg_no_objects": "No objects to assign."
    },
    "cs": {
        "cmd_name": "AssignToLayer (CS)",
        "help": "Přiřadí vybranou větev objektů do vrstvy.",
        "dlg_title": "AssignToLayer (CS) v{ver}",
        "tip": "Tip: Nová vrstva má přednost. Výběr dítěte vezme větev nejbližšího rodiče.",
        "existing": "Existující vrstva:",
        "new": "Nová vrstva (priorita):",
        "ok": "OK",
        "cancel": "Zrušit",
        "msg_select_one": "Vyber alespoň jeden objekt v Object Manageru.",
        "msg_no_layerroot": "Nebyl nalezen Layer Root.",
        "msg_no_target": "Nevybral jsi vrstvu ani nevytvořil novou.",
        "msg_no_objects": "Nebyl nalezen žádný objekt k přiřazení."
    }
}

def _lang_from_locale():
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

    s = " ".join([c for c in candidates if c]).lower()
    if "cs" in s or "czech" in s or "cz" in s:
        return "cs"
    if "de" in s or "german" in s:
        return "de"
    return "en"

def _detect_lang_key():
    try:
        lang = c4d.GeGetLanguage()
    except Exception:
        return _lang_from_locale()

    if isinstance(lang, int):
        cz_vals = set()
        de_vals = set()
        en_vals = set()

        for name in ("LANGUAGE_CZECH", "LANGUAGE_CZECHREPUBLIC", "LANGUAGE_CZECH_REPUBLIC"):
            v = getattr(c4d, name, None)
            if isinstance(v, int):
                cz_vals.add(v)

        for name in ("LANGUAGE_GERMAN", "LANGUAGE_DE", "LANGUAGE_GERMANY"):
            v = getattr(c4d, name, None)
            if isinstance(v, int):
                de_vals.add(v)

        for name in ("LANGUAGE_ENGLISH", "LANGUAGE_ENGLISH_US", "LANGUAGE_US"):
            v = getattr(c4d, name, None)
            if isinstance(v, int):
                en_vals.add(v)

        if lang in cz_vals:
            return "cs"
        if lang in de_vals:
            return "de"
        if lang in en_vals:
            return "en"

        return _lang_from_locale()

    if isinstance(lang, str) and lang:
        s = lang.lower()
        if "cs" in s or "cz" in s:
            return "cs"
        if "de" in s:
            return "de"
        return "en"

    return _lang_from_locale()

_LANG = "cs"  # fixed language build

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

def _find_layer_by_name(layers, name):
    for l in layers:
        if l.GetName() == name:
            return l
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

class AssignDialog(gui.GeDialog):
    IDC_DROPDOWN = 1000
    IDC_NEWINPUT = 1001
    IDC_OK       = 1002
    IDC_CANCEL   = 1003
    IDC_TIP      = 1004

    def __init__(self, layers):
        super(AssignDialog, self).__init__()
        self.layers = layers
        self.selected_layer = None
        self.new_layer_name = ""

    def CreateLayout(self):
        self.SetTitle(T("dlg_title").format(ver=PLUGIN_VERSION))

        tip = T("tip")
        if tip:
            self.AddStaticText(self.IDC_TIP, c4d.BFH_LEFT, name=tip)

        self.AddStaticText(2000, c4d.BFH_LEFT, name=T("existing"))
        self.AddComboBox(self.IDC_DROPDOWN, c4d.BFH_SCALEFIT)

        for i, layer in enumerate(self.layers):
            self.AddChild(self.IDC_DROPDOWN, i, layer.GetName())

        if self.layers:
            self.SetInt32(self.IDC_DROPDOWN, 0)
        else:
            self.Enable(self.IDC_DROPDOWN, False)

        self.AddStaticText(2001, c4d.BFH_LEFT, name=T("new"))
        self.AddEditText(self.IDC_NEWINPUT, c4d.BFH_SCALEFIT)

        self.GroupBegin(3000, c4d.BFH_CENTER, 2, 1)
        self.AddButton(self.IDC_OK, c4d.BFH_LEFT, name=T("ok"))
        self.AddButton(self.IDC_CANCEL, c4d.BFH_LEFT, name=T("cancel"))
        self.GroupEnd()
        return True

    def Command(self, _id, _msg):
        if _id == self.IDC_OK:
            idx = self.GetInt32(self.IDC_DROPDOWN)
            self.selected_layer = self.layers[idx] if (self.layers and 0 <= idx < len(self.layers)) else None
            self.new_layer_name = (self.GetString(self.IDC_NEWINPUT) or "").strip()
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

        dlg = AssignDialog(layers)
        if not dlg.Open(c4d.DLG_TYPE_MODAL, defaultw=480, defaulth=180):
            return True

        target_layer = None

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
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                obj.SetLayerObject(target_layer)

        finally:
            doc.EndUndo()

        c4d.EventAdd()
        return True

if __name__ == "__main__":
    print("[AssignToLayer CS] loaded (v{ver})".format(ver=PLUGIN_VERSION))".format(ver=PLUGIN_VERSION))

    icon = _load_icon()
    plugins.RegisterCommandPlugin(
        id=PLUGIN_ID,
        str=T("cmd_name"),
        info=0,
        icon=icon,
        help=T("help"),
        dat=AssignToLayerCommand()
    )
