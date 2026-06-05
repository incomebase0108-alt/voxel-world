# サウンド実装一覧（`sound.js` / 2号機・音響担当）

WebAudio による合成音。本体コードと疎結合で、コアは `window.playSFX(name, opts)` や `window.on*` の口を呼ぶだけ。`sound.js` 未読込でも本体は壊れません。素材は仮の合成音で、後から音声ファイル再生に差し替え可能です。

## 1号機向け 公開API早見表（呼ぶだけ・未呼出でも無音で安全）
| 用途 | 口 | 備考 |
|---|---|---|
| 動物SE（敵/仲間/ペット） | `playAnimalSFX(species, event, {x,y,z,vol})` | **推奨**。種×イベント→SE。座標で3D定位。`critterSE` から委譲済 |
| 効果音 個別 | `playSFX('key', opts)` | 上表の個別キーを直叩き |
| 環境音 切替 | `setAmbient('forest'|…)` / `setAmbient(null)` | 未呼出でも `getBiome()` 連動で自動 |
| 女王さくら（最終ボス） | `onQueenAppear()` / `onQueenDefeat()` | 咆哮＋威圧テーマ同時 / 勝利音 |
| 敵 aggro | `onEnemyAggro()` | 交戦突入の緊張スティンガー |
| 既存ボス | `onBossAppear(type)` / `onBossDefeat(type)` | `type`=golem/dragon/skeleton_king/queen |
| BGMシーン | `setMusicScene('day'|'night'|'combat'|'water'|'boss'|'queen'|'escape')` | 1.8sクロスフェード |
| 序章『脱走』 | `setMusicScene('escape')` ＋ `onEscapeSuccess()` | 忍び/緊張テーマ＋脱走成功ジングル |
| 仲間 | `onCompanionJoin/Reply/Hit/Leave(type)` | — |
| 攻撃 | `onAttackHit(weapon,isCrit)` / `onAttackWhiff()` / `onAttackCharge('start'|'full')` | — |
| 音量/診断 | `setMasterVolume/SfxVolume/BgmVolume/AmbVolume`・`setSfxGain(key,x)`・`getSoundDiag()` | ④設定・実機診断 |

## バス構成
`各音源 → (sfxBus | bgmBus | ambBus) → master → limiter → 出力`
- `master` … 全体音量（ミュート時は0）
- `sfxBus` … 効果音 ／ `bgmBus` … BGM ／ `ambBus` … 環境音
- `limiter` … master直前のセーフティ・リミッタ（クリップ防止）
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
| `queen` | ⑧ 女王さくら（最終ボス）・**気高くも威圧的**（Fマイナー寄りクラスタ+shimmerの艶） | 138 | bossより速く張りつめ。`setMusicScene('queen')` |
| `escape` | ⓪ 序章『脱走』・**忍び/緊張**（低密度・小音量・半音A↔A#の不穏＋心臓の鼓動） | 100 | `setMusicScene('escape')`。`setDangerLevel(0..1)`で緊張増 |

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
コアの読み取り口があれば自動有効化（無ければ黙って無効）。**1号機が実装済み**（`getMobPositions`/`getPlayerPose`/`getBiome`）なので実機で稼働。
- `window.getMobPositions()` → `[{x, y, z, type, hostile}, ...]`
- `window.getPlayerPose()` → `{x, y, z, yaw, pitch}`（リスナー位置・向きに反映）

周囲モブ（半径36m）の鳴き声を距離・方向で減衰（PannerNode）。`playSFX('mob', {type, x, y, z})` の push 型3Dにも対応。

**動物SE（critter）の空間化（P2）**: `playAnimalSFX(species, event, {x,y,z})` は座標があれば内部で `makePanner` を生成し、`tone/noise → panner → sfxBus → master → limiter → 出力` の経路で**距離減衰つきの定位音**になる。`critterSE`（index.html）は常に座標を渡すので全 critter SE が空間化される。パンナーは `inverse`/`equalpower`・`refDistance 4`/`maxDistance 40`/`rolloff 1`、発音後 2 秒で自動 `disconnect`（ノードリーク防止）。
- **セーフティ・リミッタ**: `master` 直前に `DynamicsCompressor`（threshold −3dB / ratio 20 / 速attack）を挿入し、多数のSE＋BGM重畳時も**クリップしない**。抑制量は `getSoundDiag().limiterReductionDb` で確認可（0＝余裕／負＝ピーク抑制中）。

---

## 環境音アンビエンス（①⑤⑥／ambバス・BGMの下）
連続音の「寝床」（bandpassノイズ＝風/波/こもり）＋散発の単発音を biome で切替。**1号機が `window.getBiome()` 実装済み**（`plains/forest/rocky/desert/snow/ocean`＋`castle/shrine`）なので**自動で連動**。未実装環境でも `bgmScene` から代替推定（防御的・事故ゼロ）。音量は `setAmbVolume()`／`amb` バス。

| biome | 雰囲気（寝床） | 散発音 |
|---|---|---|
| `plains` | 草原 | bird（小鳥） |
| `forest` | 森 | forest（小鳥＋葉擦れ） |
| `rocky` | 岩場（チンチラの故郷）＝吹き抜ける風 | gust（風の一吹き） |
| `desert` | 砂漠＝乾いた熱風 | gust（熱風） |
| `snow` | 雪原＝こもった静寂 | windhowl（遠い風鳴り・控えめ） |
| `ocean` | 海＝寄せる波 | wave（ザザーと寄せ返す波） |
| `water` | 水中こもり | — |
| `cave` | 洞窟＝反響 | drip（水滴） |
| `night` | 夜 | cricket |
| `village` | 村 | murmur |
| `castle` | ③ 王国城・**荘厳**（低い大広間のうなり） | choir（聖歌/オルガンのswell） |
| `shrine` | ③ 祠・**静謐** | chime（清らかな鈴） |

**公開口（⑥）**:
```js
window.setAmbient('forest');   // 明示切替（既知 biome のみ採用・未知は無視）
window.setAmbient(null);       // または 'auto' で getBiome 連動へ復帰
window.getAmbientBiome();      // 現在鳴っている環境音タイプ（診断/UI）
```
- `setAmbient` を呼ばなくても `getBiome()` 連動で自動切替。呼べば手動上書きが最優先（`null`/`'auto'` で連動へ戻す）。切替時は寝床のフィルタ/音量をクロスで滑らかに変化。
- **1号機へ**: `getBiome()` は実装済みのため**追加配線は不要**。任意で `setAmbient(biome)` を使えば演出上の強制切替（例: イベントシーン）も可能です。

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

### ⑧ 女王さくら（最終ボス）＆ 敵 aggro スティンガー
- **女王さくら出現**: `window.onQueenAppear()` を1回 → 咆哮スティンガー `boss_roar('queen')`（巨大チンチラ女王の気高い金切り＋荘厳な低和音＋鐘）＋専用威圧テーマ `setMusicScene('queen')` を同時発火。`boss_roar` の `type` に `'queen'` を渡しても同じ咆哮。
- **女王撃破**: `window.onQueenDefeat()` → 既存の勝利ファンファーレ。撃破後コアが `setMusicScene('day'|…)` で平常へ戻す。
- **敵 aggro スティンガー**: `window.onEnemyAggro()`（= `playSFX('aggro_stinger')`）→ 敵が交戦状態に入った瞬間の短い緊張の刺し（低い衝撃＋上昇2音）。頻発OK・軽量。
- `boss_roar` の `type`: `golem` / `dragon` / `skeleton_king` / **`queen`**（省略でも汎用咆哮）。

> **1号機へ依頼（⑧）**: 女王さくらの出現確定で `onQueenAppear()`、撃破で `onQueenDefeat()` を1回ずつ。任意の敵が aggro 状態へ遷移した瞬間に `onEnemyAggro()` を呼べば緊張スティンガーが鳴ります（**sound.js側は受け口実装済み・呼ぶだけ**）。

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

## チンチラ世界の動物SE（敵8種＋仲間＋ペット）
チンチラ世界の生き物向けプロシージャル合成音。口は防御的（**呼ぶだけ・未配線でも無音で安全**）。1号機は次のどちらでも鳴らせます。

- **推奨**: `window.playAnimalSFX(species, event, opts?)` … 種×イベントを自動でSEへ写像。
- **個別**: `window.playSFX('wolf_howl', opts?)` … 下表の `key` を直接指定。
- `opts.x/y/z` を渡せば**3D定位＋距離減衰**（③のPannerNode経由・座標が無ければ通常再生）。`opts.vol` で個体ごとの強弱（既定1）。

### 動物SE一覧（`playAnimalSFX(species, event, {x,y,z,vol})`）
1号機の `critterSE()`（index.html）は**この `playAnimalSFX` に委譲済み**（`bafbbec`）。種は `m.def.type`、座標も渡るので**実機で 3D 定位つきで鳴る**。`event` は種ごとに下表のキーへ写像（未定義 event は `default` にフォールバック＝無音回避）。

| species | spot（発見） | attack（打撃） | hurt（被ダメ） | die（死亡） | その他 event → key |
|---|---|---|---|---|---|
| `wolf` | `wolf_growl` うなり | `attack_bite` 噛みつき | `animal_hurt`※ | `animal_die`※ | `howl`→`wolf_howl` 遠吠え / `skill`→`wolf_howl` |
| `snake` | `snake_hiss` シューッ | `snake_strike` 毒牙ラッシュ | `animal_hurt`※ | `animal_die`※ | `skill`→`snake_hiss` |
| `weasel` | `weasel_screech` 甲高い威嚇 | `attack_bite` 噛みつき | `animal_hurt`※ | `animal_die`※ | `skill`→`weasel_screech` |
| `bird`（猛禽） | `bird_screech` 猛禽の鳴き | `bird_wingflap` 急降下の羽ばたき | `animal_hurt`※ | `animal_die`※ | `dive`/`skill`→`bird_wingflap` |
| `squirrel` | `squirrel_chitter` チチッ | `squirrel_chitter` | `animal_hurt`※ | `animal_die`※ | `skill`/`tamed`/`happy`→`squirrel_chitter` |
| `rabbit` | `rabbit_thump` 後足ドン | — | `animal_hurt`※ | `animal_die`※ | `alert`/`skill`/`tamed`→`rabbit_thump` |
| `guineapig` | `guineapig_wheek` ウィーク | — | `animal_hurt`※ | `animal_die`※ | `skill`/`tamed`/`happy`→`guineapig_wheek` |
| `hedgehog` | `hedgehog_huff` フスフス | — | `animal_hurt`※ | `animal_die`※ | `curl`/`skill`/`tamed`→`hedgehog_huff` |
| `pet`（さくら） | `pet_squeak` 鳴き | `pet_bite` 噛みつき | `pet_squeak` | `pet_squeak` | `skill`→`pet_pee` / `happy`・`tamed`→`pet_happy` / `purr`・`petted`→`pet_purr` なでられ満足 / `sandbath`・`dust`→`pet_sandbath` 砂浴び |

※ `animal_hurt` / `animal_die` は**全種共通のジェネリック音**。`playAnimalSFX` が `opts.species` を注入し、種ごとに基準ピッチ・音色（`VOICE` 表）を変えるので**種が聞き分け可能**。蛇だけは噴気的（hiss）に分岐。

**個別キー一覧（`playSFX('key')` 直叩きも可）**: `wolf_howl` / `wolf_growl` / `snake_hiss` / `snake_strike` / `weasel_screech` / `bird_screech` / `bird_wingflap` / `attack_bite`（捕食者の噛みつき共通） / `animal_hurt` / `animal_die`（種別ピッチ） / `squirrel_chitter` / `rabbit_thump` / `guineapig_wheek` / `hedgehog_huff` / `critter_step`（小動物の足音・極小） / `pet_squeak` / `pet_bite` / `pet_happy` / `pet_pee` / `pet_purr` / `pet_sandbath`。

**⑨ 足音（任意・控えめ）**: `playAnimalSFX(species, 'step'|'move', {x,y,z})` は**種に依らず**極小音量の `critter_step`（パタッ）を鳴らす（誤って鳴き声を出さない設計）。頻発するので 1号機側で**間引いて**呼ぶ想定。

- **species**: `wolf / snake / weasel / bird / squirrel / rabbit / guineapig / hedgehog / pet`。別名: `sakura`・`さくら`→`pet`、`raptor/hawk/eagle/owl`→`bird`、`cavy`→`guineapig`。
- **event**: `spot` / `attack` / `hurt` / `die` / `skill` / `tamed` / `happy`、および 1号機語彙 `howl` / `dive` / `curl` / `alert` / `tame`（=`tamed`）。未定義 event は `default` フォールバック。未知 species は無音（事故ゼロ）。
- 旧来の `on*` スタイル用の別名 `window.onAnimalSound(species, event, opts)` も用意（任意）。

> **整合メモ（2号機）**: 1号機の先行スタブ8キー（`e96451b`）は3D対応リッチ版に一本化。`critterSE` が `playAnimalSFX` へ委譲（`bafbbec`）したので互換シム `bird_chirp`/`bird_flap` は撤去済み（呼び元が消えたため安全）。`weasel`/`guineapig` も委譲経由で正規の `weasel_screech`/`guineapig_wheek` が鳴る（旧 `pickup` 代用は解消）。**P1 追加**: 全種に `hurt`/`die`（種別ピッチ）と捕食者の `attack`（噛みつき/毒牙）を足し、`spot`（鳴き声）と聞き分け可能に。

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
対象 name は上の効果音一覧と同じ（`footstep / jump / land / break / place / eat / pickup / craft / splash / swim / attack / hit / hurt / thunder / mob / whiff / charge_start / charge_full / boss_roar / boss_defeat / companion_join / companion_reply / companion_hit / companion_leave`、`aggro_stinger`、動物SE `wolf_howl / wolf_growl / snake_hiss / snake_strike / weasel_screech / bird_screech / bird_wingflap / attack_bite / animal_hurt / animal_die / squirrel_chitter / rabbit_thump / guineapig_wheek / hedgehog_huff / pet_squeak / pet_bite / pet_happy / pet_pee / pet_purr / pet_sandbath / pet_dust`）。

> 体感後に「この音だけ大きい/小さい」が出たら、上記 `setSfxGain` で1行調整 → そのまま保存されます。

---

## 3号機UI（設定画面）との連携
`UI_INTEGRATION.md` の希望IFに整合済み。設定スライダーは `setMasterVolume / setSfxVolume / setBgmVolume / setMuted`（＋個別は `setSfxGain`）に直結できます。値は `SoundSettings.get()` で取得、`soundsettingschange` で同期可能。
