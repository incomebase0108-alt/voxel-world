# VOXEL WORLD ボス出現演出パーツ（fx_*）— 1号機向け統合ガイド

ボスのスポーン（`bossSpawn`）に重ねる3Dの出現演出。地面に置いて使う。生成は `tools/build_fx_boss.py`。
見本：`tools/hero_fx_magic_circle_3q.png` / `hero_fx_miasma_3q.png` / `hero_fx_collapse_3q.png`。

## パーツ一覧

| ファイル | 役割 | 直径/高さ | 容量 | クリップ | 発光色 |
|---|---|---|---|---|---|
| `fx_magic_circle.glb` | 召喚魔法陣（地面の陣） | φ≒3.6m / H0.2m | 0.38MB | `loop` | 深紅輪＋紫六芒星＋中央グロウ |
| `fx_miasma.glb` | 瘴気（毒の霧・立ち昇る） | φ≒2.0m / H2.5m | 0.30MB | `loop` | 病的な毒緑（紫＝深部の陰） |
| `fx_collapse.glb` | 地面崩壊（割れ岩盤＋裂け目） | φ≒3.0m / H1.0m | 0.07MB | `loop` | 岩＋橙の発光裂け目 |

## 規約（全パーツ共通）

- **Y-up / 正面 -Z / 1ブロック≒1m**（装備と同じ。EQUIP_HOLD §0 参照）。
- **原点＝footprint中心・接地 z=0**。ボスの立ち位置(x,z)に置けば地面に乗る。
- **アニメは単一クリップ `loop`**（96f / 24fps＝4秒・継ぎ目なし）。1号機は再生しっぱなしでOK。
  - 魔法陣：外輪=右回り／内星=左回り（逆回転）／中央=拍動。
  - 瘴気：3層が別速で旋回＋上下うねり。
  - 崩壊：裂け目=脈動／岩盤=隆起うねり／瓦礫=浮揺れ＋回転。
- 発光は **Emission**。実機で bloom/トーンマップがあると映える（プレビューは素のEEVEEなので控えめ）。

## 推奨の使い方（bossSpawn 演出シーケンス）

地面が割れ→陣が浮かび→瘴気が噴き出し→ボス本体、の順が映える。例：

```js
GAME.on('bossSpawn', ({ pos, type }) => {           // pos=ボスの足元(x,y,z)
  const collapse = spawnFx('fx_collapse',    pos, { play:'loop' });   // t=0   地割れ
  const circle   = spawnFx('fx_magic_circle',pos, { play:'loop', t:0.2, fadeIn:0.3 });
  const miasma   = spawnFx('fx_miasma',      pos, { play:'loop', t:0.6, fadeIn:0.5 });
  // ボス本体は t≒1.0 で出現（別途）。陣/瘴気は数秒残し、崩壊は隆起後にフェードアウト。
  fadeOut(collapse, { at:3.0, dur:1.0 });
  fadeOut(circle,   { at:5.0, dur:1.5 });
  fadeOut(miasma,   { at:6.0, dur:2.0 });
});
```

- **スケールイン**：各パーツを `scale 0→1`（0.3〜0.5s）で出すと「召喚」感が出る。原点が接地中心なので地面から湧くように見える。
- **設置数**：ドラゴン/スケルトンキング/デーモン等のボス共通で流用可。サイズはボスに合わせて全体スケール（魔法陣はボスの足元径に合わせると自然）。
- **常設（祭壇・封印）用途**にも `fx_magic_circle` を弱発光で置けば流用できる。

## 調整できる軸（要望あれば4号機で即対応）

- 色味（魔法陣の深紅→金/青、瘴気の緑→紫毒、崩壊の橙→蒼炎 など）
- 直径・高さ・密度、回転速度（loopのフレーム長）、発光強度（Emission Strength）
- パーツ追加（落雷・封印鎖・吸い込み渦・破片の一方向噴出 など）

次の指示を待ちます。
