# サウンド実装一覧（`sound.js` / 2号機・音響担当）

WebAudio による合成音。本体コードと疎結合で、コアは `window.playSFX(name, opts)` や `window.on*` の口を呼ぶだけ。`sound.js` 未読込でも本体は壊れません。素材は仮の合成音で、後から音声ファイル再生に差し替え可能です。

## バス構成
`各音源 → (sfxBus | bgmBus) → master → 出力`
- `master` … 全体音量（ミュート時は0）
- `sfxBus` … 効果音
- `bgmBus` … BGM
- さらに **個別SE倍率**（`gains`）が各効果音に乗る（後述）

---

## 効果音（SFX）一覧
`window.playSFX('name', opts)` で再生。`opts.block` は材質、`opts.type` はモブ種、座標 `opts.x/y/z` 指定で3D化。

| name | 内容 | opts | コア呼出（index.html）/ 状態 |
|---|---|---|---|
| `jump` | ジャンプ | — | 配線済 |
| `land` | 着地（落下量で強弱） | `{fall}` | 1号機へ依頼中 |
| `footstep` | 足音（材質別） | `{block}` | 1号機へ依頼中 |
| `break` | ブロック破壊（材質別） | `{block}` | 配線済（`{block}`追加は任意） |
| `place` | ブロック設置（材質別） | `{block}` | 配線済（`{block}`追加は任意） |
| `eat` | 食べる | — | 配線済 |
| `pickup` | アイテム取得 | — | 配線済 |
| `craft` | クラフト | — | 1号機へ依頼中 |
| `splash` | 入水 | — | 1号機へ依頼中 |
| `swim` | 水中移動 | — | 1号機へ依頼中 |
| `attack` | 攻撃の振り | — | 配線済 |
| `hit` | 命中（矢など） | — | 配線済 |
| `hurt` | 被ダメージ | — | `onPlayerHurt` 経由・配線済 |
| `thunder` | 雷 | — | `onThunderSound` 経由・配線済 |
| `mob` | モブ鳴き声 | `{type, x, y, z, vol}` | 座標あれば3D。環境鳴きは③が自動生成 |
| `whiff` | 攻撃の空振り | — | `onAttackWhiff` 経由 |
| `charge_start` | 溜め開始 | — | `onAttackCharge('start')` |
| `charge_full` | 溜め完了 | — | `onAttackCharge('full')` |

- 材質 `block`: `grass / dirt / sand / stone / stonebrick / planks / glass / water`（未知は default）
- モブ `type`: `cow / sheep / chicken / pig / horse / villager / slime / zombie / skeleton / golem`

---

## BGM（②）
`window.setMusicScene('day'|'night'|'combat'|'water')` でシーン切替（1.8sクロスフェード）。初回ユーザー操作で `day` を自動開始。`window.startMusic()` / `window.stopMusic()` で明示制御も可。

| シーン | 雰囲気 | テンポ | 備考 |
|---|---|---|---|
| `day` | 明るめ | 104 | 既定 |
| `night` | 静か | 76 | |
| `combat` | 疾走 | 148 | キックドラムあり |
| `water` | 浮遊（水中だと分かる程度に） | 72 | |

各シーンは `level`（音量バランス）を持ち、water は静かめ。陸地に出れば day/night のはっきりしたBGMに切り替わります。

### 診断
コンソールで `window.getSoundDiag()` を実行すると `{audioContext, bgmOn, bgmScene, bgmBusGain, sfxBusGain, masterGain, muted, vol, musicSceneCalledByCore}` が返ります。「BGMが聞こえない」時はまず `bgmScene` を確認（`water` なら水中BGMが鳴っているだけ）。

各シーンは「持続pad＋確率メロディ（combatはドラム）」のレイヤー構成。

---

## 3D空間音響（③）
コアの読み取り口があれば自動有効化（無ければ黙って無効）。
- `window.getMobPositions()` → `[{x, y, z, type, hostile}, ...]`
- `window.getPlayerPose()` → `{x, y, z, yaw, pitch}`

周囲モブ（半径36m）の鳴き声を距離・方向で減衰（PannerNode）。`playSFX('mob', {type, x, y, z})` の push 型3Dにも対応。

---

## 攻撃アクション連携
1号機が以下を呼ぶだけ（未呼出なら無音待機）。
- `window.onAttackHit(weapon, isCrit)` … `weapon`=`sword`(斬撃+金属) / `axe`(重い打撃) / `bow`(命中) / `fist`(パンチ)。`isCrit=true` でクリティカル強調音
- `window.onAttackWhiff()` … 空振り
- `window.onAttackCharge('start'|'full')` … 溜め開始 / 完了

---

## 音量・バランス調整（④）
全体音量・個別SE倍率はいつでも変更でき、`localStorage`（`vw_sound_v1`）に永続化されます。変更時に `window` へ `soundsettingschange` イベントを発火。

### 全体音量（0..1）
```js
window.setMasterVolume(0.8);  window.getMasterVolume();
window.setSfxVolume(0.7);     window.getSfxVolume();
window.setBgmVolume(0.4);     window.getBgmVolume();
window.setMuted(true);        window.isMuted();
// まとめて
window.SoundSettings.get();           // {master, sfx, bgm, muted, gains}
window.SoundSettings.set('sfx', 0.6);
```

### 個別SE倍率（0..4、既定1.0）── 「足音うるさい」を即修正
```js
window.setSfxGain('footstep', 0.5);   // 足音を半分に
window.setSfxGain('thunder', 1.5);    // 雷を強調
window.getSfxGain('footstep');        // 現在の倍率
window.SoundSettings.getGains();       // 全倍率の一覧
```
対象 name は上の効果音一覧と同じ（`footstep / jump / land / break / place / eat / pickup / craft / splash / swim / attack / hit / hurt / thunder / mob / whiff / charge_start / charge_full`）。

> 体感後に「この音だけ大きい/小さい」が出たら、上記 `setSfxGain` で1行調整 → そのまま保存されます。

---

## 3号機UI（設定画面）との連携
`UI_INTEGRATION.md` の希望IFに整合済み。設定スライダーは `setMasterVolume / setSfxVolume / setBgmVolume / setMuted`（＋個別は `setSfxGain`）に直結できます。値は `SoundSettings.get()` で取得、`soundsettingschange` で同期可能。
