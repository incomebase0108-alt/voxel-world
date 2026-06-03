# -*- coding: utf-8 -*-
# VOXEL WORLD - アセット一覧インデックス生成（Blender不要・GLBのJSONチャンクを直接パース）
#   実行: python tools/gen_asset_index.py
#   出力: models/ASSETS.json（機械可読）/ models/ASSETS.md（人間可読の表）
#   各 models/*.glb から ファイル名 / 容量 / アニメクリップ名 / mesh数 / node数 を抽出。
#   1号機(エンジン)・3号機が「どのファイルが何のクリップを持つか」を一目で参照するための索引。

import os, json, struct, glob

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS = os.path.join(REPO, "models")

def parse_glb(path):
    """GLBのJSONチャンクを読み、animation名/mesh数/node数を返す。"""
    with open(path, "rb") as f:
        data = f.read()
    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67:  # 'glTF'
        return {"error": "not a glb"}
    off = 12
    gltf = None
    while off < length:
        clen, ctype = struct.unpack_from("<II", data, off)
        off += 8
        chunk = data[off:off+clen]
        off += clen
        if ctype == 0x4E4F534A:  # 'JSON'
            gltf = json.loads(chunk.decode("utf-8"))
            break
    if gltf is None:
        return {"error": "no json chunk"}
    anims = [a.get("name", "?") for a in gltf.get("animations", [])]
    return {
        "clips": anims,
        "meshes": len(gltf.get("meshes", [])),
        "nodes": len(gltf.get("nodes", [])),
        "materials": len(gltf.get("materials", [])),
    }

def category(name):
    if name.startswith("player"): return ("プレイヤー", 0)
    if name.startswith("mob_"):   return ("モブ", 1)
    if name.startswith("npc_"):   return ("NPC", 2)
    if name.startswith("struct_"):return ("構造物", 3)
    if name.startswith("ore_") or name.startswith("cave_"): return ("洞窟・鉱石", 6)
    if name.startswith("castle"): return ("王国城（ランドマーク）", 7)
    if name.startswith("shrine"): return ("祠・聖域", 8)
    if name.startswith("fort_"): return ("砦・城塞", 7)
    if name.startswith("ship_"): return ("船", 8)
    if name.startswith("prop_"): return ("町小物", 25)
    if name.startswith("fx_"):    return ("演出（ボス出現FX）", 10)
    if name.startswith("item_") and name in EQUIP: return ("装備・道具", 5)
    if name.startswith("item_"):  return ("アイテム", 4)
    return ("その他", 9)

EQUIP = {"item_sword","item_pickaxe","item_axe","item_bow","item_shield","item_armor"}

rows = []
for path in sorted(glob.glob(os.path.join(MODELS, "*.glb"))):
    name = os.path.splitext(os.path.basename(path))[0]
    size = os.path.getsize(path)
    info = parse_glb(path)
    cat, order = category(name)
    rows.append({
        "file": name + ".glb",
        "name": name,
        "category": cat,
        "_order": order,
        "size_bytes": size,
        "size_mb": round(size / 1048576, 4),
        "clips": info.get("clips", []),
        "meshes": info.get("meshes"),
        "nodes": info.get("nodes"),
        "materials": info.get("materials"),
        "error": info.get("error"),
    })

rows.sort(key=lambda r: (r["_order"], r["name"]))
total_bytes = sum(r["size_bytes"] for r in rows)

# ---- JSON 出力 ----
meta = {
    "convention": {
        "up": "Y-up",
        "front": "glTF -Z (Blenderでは+Y面で造形)",
        "scale": "1ブロック≒1m",
        "origin": {
            "player/mob/npc/struct": "足元中心 z=0",
            "item_(消費)": "形状中心",
            "item_(装備:sword/pickaxe/axe)": "握り（拳が巻く点。2026-06-04に柄基部から移動）",
            "item_bow": "握り中央",
            "item_(装備:shield/armor)": "形状中心",
            "fx_(ボス出現FX)": "footprint中心・接地 z=0",
        },
        "clip_naming": "idle / walk（敵性=+attack, ボス=+heavy）。構造物は idle ＋ 固有(chest:open 等)。FX=loop。",
        "draco": "不使用（ゲーム側GLTFLoaderが未対応のため）",
    },
    "totals": {"count": len(rows), "size_bytes": total_bytes, "size_mb": round(total_bytes/1048576, 3)},
    "assets": [{k: v for k, v in r.items() if k != "_order"} for r in rows],
}
with open(os.path.join(MODELS, "ASSETS.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

# ---- Markdown 出力 ----
lines = []
lines.append("# VOXEL WORLD アセット一覧（自動生成）\n")
lines.append("`python tools/gen_asset_index.py` で再生成。models/ASSETS.json が機械可読版。\n")
lines.append("**規約**: Y-up / 正面 glTF -Z / 1ブロック≒1m / Draco不使用。")
lines.append("クリップ名は **idle / walk**（敵性=+`attack`、ボス=+`heavy`）。構造物は `idle` ＋ 固有クリップ。\n")
lines.append("**原点**: プレイヤー/モブ/NPC/構造物=足元中心 z=0 ／ 消費アイテム=形状中心 ／ "
             "装備 剣・ピッケル・斧=柄基部・弓=握り中央・盾/防具=中心。\n")
lines.append(f"**合計**: {len(rows)} ファイル / {total_bytes/1048576:.2f} MB\n")

cur = None
for r in rows:
    if r["category"] != cur:
        cur = r["category"]
        lines.append(f"\n## {cur}\n")
        lines.append("| ファイル | 容量(MB) | クリップ | mesh/node |")
        lines.append("|---|---|---|---|")
    clips = ", ".join(f"`{c}`" for c in r["clips"]) if r["clips"] else "—（静物）"
    lines.append(f"| `{r['file']}` | {r['size_mb']:.4f} | {clips} | {r['meshes']}/{r['nodes']} |")

with open(os.path.join(MODELS, "ASSETS.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ---- コンソール最終点検 ----
print("[voxel] === アセット最終点検 ===")
for r in rows:
    flag = ""
    if r["error"]: flag = "  !! " + r["error"]
    # 命名・クリップの異常検知
    if r["category"] in ("プレイヤー","モブ") and "idle" not in r["clips"]:
        flag += "  !! idleクリップ無し"
    if r["size_mb"] > 2.0:
        flag += "  !! 2MB超過"
    print("[voxel] %-22s %7.3fMB  clips=[%s]%s" % (r["file"], r["size_mb"], ",".join(r["clips"]), flag))
print("[voxel] 合計 %d files / %.2f MB" % (len(rows), total_bytes/1048576))
print("[voxel] -> models/ASSETS.json, models/ASSETS.md")
