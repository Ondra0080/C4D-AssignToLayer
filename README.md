# C4D–AssignToLayer

**Assign selected object hierarchies to layers in Cinema 4D — fast and safely.**

C4D–AssignToLayer is a lightweight Command Plugin for **Cinema 4D 2024+** that lets you assign selected objects (including their full hierarchy) to an existing or newly created layer in one step.

The plugin is available in **two separate language versions**:
- **AssignToLayer (CS)** – Czech
- **AssignToLayer (EN)** – English

Each language version is a standalone plugin with fixed language (no runtime localization, no .str files).

---

## ✨ Features

- Assign full object hierarchies to a layer
- Select **child → parent branch is automatically detected**
- Assign to an **existing layer** or **create a new one**
- Full **Undo / Redo** support
- Clean dialog UI
- Separate CS / EN plugins for maximum stability
- Works with **Cinema 4D 2024+**

---

## 📦 Installation

1. Download the latest release from **Releases**
2. Unzip the package
3. Copy one or both plugin folders into:

### macOS
```
/Applications/Maxon Cinema 4D 20##/plugins/
```

or user plugins:
```
~/Library/Preferences/Maxon/Maxon Cinema 4D 20##/plugins/
```

### Windows

User plugins (recommended):
```
C:\Users\YOUR_USERNAME\AppData\Roaming\Maxon\Maxon Cinema 4D 20##\plugins\
```

**System-wide plugins:**
```
C:\Program Files\Maxon Cinema 4D 20##\plugins\
```

4. Restart Cinema 4D

![screenshot](doc/01_command_manager.png)

---

## 🚀 Usage

1. Select one or more objects in the **Object Manager**
   - You can select a parent or just a child
2. Run **AssignToLayer (CS)** or **AssignToLayer (EN)**
3. Choose:
   - an existing layer
     ![screenshot](doc/05_assign_existing_layer.png)  
   
   **or**
   - enter a name for a new layer
     ![screenshot](doc/06_assign_new_layer.png)
     
4. Confirm → objects are assigned

Undo is supported via **Cmd/Ctrl + Z**.

---

## 🖼 Screenshots & Video

Put screenshots and a short demo video here:
- `docs/screenshots/`
- `docs/video/`

Suggested screenshot filenames:
- `01_command_manager.png`
- `02_toolbar.png`
- `03_scene_before.png`
- `04_dialog.png`
- `05_assign_existing_layer.png`
- `06_assign_new_layer.png`
- `07_child_selection.png`
- `08_undo.png` *(optional)*

---

## 🧪 Tested on

- Cinema 4D 2024.x

---
 ## ⬇️ Download

Ready-to-use plugin packages are available via **GitHub Releases**.

👉 Go to **Releases** and download one of the following ZIP files:

- **AssignToLayer_CS.zip** – Czech version  
- **AssignToLayer_EN.zip** – English version  

Each ZIP contains a standalone Cinema 4D plugin.  
Simply unzip and copy the plugin folder into your Cinema 4D `plugins` directory.

> Note: The **Code → Download ZIP** button downloads the entire repository  
> (source code + documentation). For end users, always use **Releases**.
 

---

## 📄 License

MIT License  
© Ondřej Bahula

---

## 🙌 Credits

Concept & design: **Ondřej Bahula**  
Implementation: **ChatGPT (OpenAI)**
