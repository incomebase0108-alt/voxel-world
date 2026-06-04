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
| `levelup` | レベルアップ（上昇アルペジオ） | — | 1号機が `playSFX('levelup')` を呼出（配線済） |
| `boss_roar` | ボス出現の威圧音（地響き+咆哮+三全音） | `{type}` | `onBossAppear(type)` 経由・**1号機へ依頼中** |
| `boss_defeat` | ② ボス撃破の勝利ファンファーレ（達成感） | — | `onBossDefeat(type)` 経由・**1号機へ依頼中** |

- 材質 `block`: `grass / dirt / sand / stone / stonebrick / planks / glass / water`（未知は default）
- モブ `type`: `cow / sheep / chicken / pig / horse / villager / slime / zombie / skeleton / golem`
- ボス `type`（`boss_roar`）: `golem`（石の巨像/地響き）/ `dragon`（金切り咆哮+炎ブレス）/ `skeleton_king`（骨カタカタ+不協和な鐘）。未指定でも汎用咆哮として鳴る

---

## BGM（②）
`window.setMusicScene('day'|'night'|'combat'|'water'|'boss')` でシーン切替（1.8sクロスフェード）。初回ユーザー操作で `day` を自動開始。`window.startMusic()` / `window.stopMusic()` で明示制御も可。

| シーン | 雰囲気 | テンポ | 備考 |
|---|---|---|---|
| `day` | 明るめ | 104 | 既定 |
| `night` | 静か | 76 | |
| `combat` | 疾走 | 148 | キックドラムあり |
| `water` | 浮遊（水中だと分かる程度に） | 72 | |
| `boss` | ① ボス戦・**重厚**（低音域+三全音テンション+重いサブベース） | 132 | キックドラム＋鋸波pad。combatより低く・重い |

各シーンは `level`（音量バランス）を持ち、water は静かめ。陸地に出れば day/night のはっきりしたBGMに切り替わります。`boss` は combat より低い音域・重いサブベース・三全音(G#3 vs 根音D)の不協和で威圧感を出しています。

### 診断
コンソールで `window.getSoundDiag()` を実行すると状態一式が返ります。「BGMが聞こえない」時の切り分け順：
1. `bgmScene` … `water` なら水中BGMが鳴っているだけ（陸へ）
2. `activeSceneGain` … `0` なら gain で消えている（フェード/設定の問題）
3. `activeScenePadOscillators` … `0` なら pad が鳴っていない
4. `schedulerRunning` … `false` ならノート生成ループが止まっている
5. `lastNoteAgoSec` … 大きすぎ（数十秒）ならノートが出ていない
6. `audioContext`(running) / `bgmBusGain` / `masterGain` / `muted` … 基本条件

各シーンは「持続pad＋確率メロディ（combatはドラム）」のレイヤー構成。

---

## 3D空間音響（③）
コアの読み取り口があれば自動有効化（無ければ黙って無効）。
- `window.getMobPositions()` → `[{x, y, z, type, hostile}, ...]`
- `window.getPlayerPose()` → `{x, y, z, yaw, pitch}`

周囲モブ（半径36m）の鳴き声を距離・方向で減衰（PannerNode）。`playSFX('mob', {type, x, y, z})` の push 型3Dにも対応。

---

## 環境音アンビエンス（①／ambバス・BGMの下）
連続音の「寝床」（bandpassノイズ）＋散発の単発音を biome で切替。コアが `window.getBiome()` を実装すれば連動、無ければ `bgmScene` から代替推定（防御的・事故ゼロ）。音量は `setAmbVolume()`／`amb` バス。

| biome | 雰囲気 | 散発音 |
|---|---|---|
| `plains` | 草原 | bird |
| `desert` | 砂漠 | — |
| `snow` | 雪原 | — |
| `ocean` | 海 | — |
| `water` | 水中こもり | — |
| `cave` | 洞窟 | drip |
| `night` | 夜 | cricket |
| `village` | 村 | murmur |
| `castle` | ③ 王国城・**荘厳**（低い大広間のうなり） | choir（聖歌/オルガンのswell） |
| `shrine` | ③ 祠・**静謐** | chime（清らかな鈴） |

> **1号機へ依頼（③）**: `window.getBiome()` が王国城内で `'castle'`、祠で `'shrine'` を返せば、その場の荘厳な環境音に自動で切り替わります（口が無くても他biomeは不変）。

---

## 攻撃アクション連携
1号機が以下を呼ぶだけ（未呼出なら無音待機）。
- `window.onAttackHit(weapon, isCrit)` … `weapon`=`sword`(斬撃+金属) / `axe`(重い打撃) / `bow`(命中) / `fist`(パンチ)。`isCrit=true` でクリティカル強調音
- `window.onAttackWhiff()` … 空振り
- `window.onAttackCharge('start'|'full')` … 溜め開始 / 完了

---

## ① ボス戦の音（世界拡張・王国城/ボス三系統 連携）
1号機のボス三系統（`golem` / `dragon` / `skeleton_king`、role:`boss`）に対応。口は防御的（未呼出なら無音待機）。

- **出現の威圧音**: `window.onBossAppear(type)` を1回呼ぶ → 威圧音 `boss_roar` が鳴る。`type` はボス種（省略可）。
  例: `window.onBossAppear('dragon')`
- **ボス戦BGM**: combatより重厚な `boss` シーンを用意済み。1号機が `window.setMusicScene('boss')` を呼べば切替（1.8sクロス）。
- **撃破の勝利音**（②）: `window.onBossDefeat(type)` を1回呼ぶ → ファンファーレ `boss_defeat`（上昇ブラス→解決長三和音→きらめき＋ティンパニ）。撃破後は通常の `setMusicScene('day'|'night'|…)` でBGMを平常へ戻せばOK。

> **1号機へ依頼**: コアの `updateCombatMusic()`（index.html）は現在 `water>combat>night>day` のみ送出。近接敵にボス（role:`boss`）が含まれる場合に `'combat'` の代わりに `'boss'` を送れば、自動でボスBGMへ。出現/aggro時に `onBossAppear(m.def.type)`、撃破確定時に `onBossDefeat(m.def.type)` も1回呼んでください。**sound.js側は受け口を実装済み・呼ぶだけで動作**します。

---

## 仲間システムの音（新機能・NPCが仲間になる連携）
NPCが仲間になる新機能向け。口は防御的（未呼出なら無音待機）。`type` は仲間種（`'knight'` / `'archer'` / `'mage'` 等）で、省略でも汎用音として成立します。

- **① 加入音**: `window.onCompanionJoin(type)` → 心強い・温かい上昇ファンファーレ `companion_join`（長三和音→オクターブ着地＋低音ドローン）。type で軽い個性（knight=重厚／archer=軽やか高音／mage=魔法的きらめき）。
  例: `window.onCompanionJoin('archer')`
- **② 返事・反応音**: `window.onCompanionReply(type)` → 指示を受けた時の短い「了解！」二音 `companion_reply`。頻繁に鳴るので軽量。
- **③ 被ダメ音**: `window.onCompanionHit()` → 仲間が攻撃を受けた時の悲鳴＋衝撃 `companion_hit`（プレイヤーの `hurt` と区別できる音色）。
- **④ 離脱音**: `window.onCompanionLeave()` → 仲間が倒れた/解雇された時の物悲しい下降 `companion_leave`。

> **1号機へ依頼**: 4音とも sound.js 側は受け口実装済み・**呼ぶだけで動作**します。仲間加入時に `onCompanionJoin(type)`、被ダメ時に `onCompanionHit()`、離脱（撃破/解雇）時に `onCompanionLeave()` を1回呼んでください。**②の返事音 `onCompanionReply(type)` は当初の想定口（Join/Leave/Hit）に無かったため新設**しています — プレイヤーが仲間へ指示を出した瞬間に呼んでいただければ「了解！」が鳴ります（口名・引数の希望があれば #opゲーム で調整します）。`onCompanionHit/Leave` は将来の個体差用に `type` を任意で受けますが現状未使用でも安全です。

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
対象 name は上の効果音一覧と同じ（`footstep / jump / land / break / place / eat / pickup / craft / splash / swim / attack / hit / hurt / thunder / mob / whiff / charge_start / charge_full / boss_roar / boss_defeat / companion_join / companion_reply / companion_hit / companion_leave`）。

> 体感後に「この音だけ大きい/小さい」が出たら、上記 `setSfxGain` で1行調整 → そのまま保存されます。

---

## 3号機UI（設定画面）との連携
`UI_INTEGRATION.md` の希望IFに整合済み。設定スライダーは `setMasterVolume / setSfxVolume / setBgmVolume / setMuted`（＋個別は `setSfxGain`）に直結できます。値は `SoundSettings.get()` で取得、`soundsettingschange` で同期可能。
