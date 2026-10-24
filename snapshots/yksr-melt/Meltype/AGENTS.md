# AGENTS.md

AI エージェント (Claude Code・Codex など) が Meltype で作業するときの決まりです。
詳しい開発の手順は [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)、貢献の決まりは [CONTRIBUTING.md](CONTRIBUTING.md) にあります。

## 構成

| 場所 | 中身 |
| --- | --- |
| `src/Meltype.Core` | OS によらない判定・変換のコア (Composition / Detection / Input / Config / Diagnostics)。判定・変換を直すときはまずここ |
| `src/Meltype.Core.Tests` | コアのテスト (どの OS でも動く) |
| `src/Meltype` | Windows 版 (TSF・UI・更新) |
| `src/Meltype.Tests` | Windows 版のテスト (Windows でしか動かない) |
| `src/Meltype.Mac.Native` | Mac 版から呼ぶコアの出口 |
| `native/tip`・`native/mozc` | ネイティブの部分 (TSF の TIP・Mozc) |
| `mac/` | Mac 版 (Swift) |
| `linux/` | Linux 版 (fcitx5・ibus) とパッケージの作成 |
| `web/` | Web (Cloudflare Workers・報告フォーム) |
| `dictionaries/` | 辞書 (英単語・固有名詞・同音異義語の候補・文脈の手がかり) |
| `tools/` | 辞書の生成・検査、ベンチマーク、テスト用のスクリプト |
| `docs/` | 使い方・開発・設計の文書 |

## ビルドとテスト

```
dotnet build Meltype.sln
dotnet run --project src/Meltype.Core.Tests                 # すべてのテスト (Linux / Mac でもこれ)
dotnet run --project src/Meltype.Core.Tests -- --eval       # 品質テスト
dotnet run --project src/Meltype.Core.Tests -- --repro kyouhagoogle enter   # 打ったときの見え方と確定の結果
dotnet run --project src/Meltype.Tests                      # すべてのテスト (Windows だけ)
dotnet run --project src/Meltype.Tests -- CompositionTests  # 名前に一致するテストだけ
dotnet run --project src/Meltype.Tests -- --explain konnichiwa hello   # 1 文字ずつの判定理由
dotnet run --project src/Meltype.Tests -- --convert きょうはいいてんき  # 変換の結果と文節の区切り
node tools/check-dictionaries.mjs                           # 辞書を変えたとき
```

Linux のクラウド環境では `src/Meltype.Tests` は動きません。`src/Meltype.Core.Tests` で確かめてください。

## 必ず守ること

- **新しいソースファイルの先頭** にライセンスと著作権の行を入れる。名前は既存のファイルをまねて `Yukishiro` にせず、変更を頼んだ人 (PR を出す人) の名前にする。分からなければ聞く。
  ```
  // SPDX-License-Identifier: GPL-3.0-or-later
  // Copyright (C) 2026 あなたの名前
  ```
- **PR は [テンプレート](.github/PULL_REQUEST_TEMPLATE.md) どおりに書く**。「確かめること」は `入力 → 期待` の形で書く (bot が PR のコードで再現を確かめます)。
- **AI を使ったことを PR に書く**。テンプレートの「AI を使った」にチェックを入れ、使った部分を書く。
- **判定・変換を変えたら**、報告された例をテストに足す。
- **説明は日本語で書く**。PR の本文・コメント・文書は、既存の文書に合わせて平易な日本語で書く。
- **変更はできるだけ小さくする**。頼まれたことに必要な分だけ直し、ついでの整理や書き換えはしない。

## してはいけないこと

- テストを消す・飛ばす・ゆるめることで通す。
- 生成されたファイル (辞書から作るもの、`tools/make-*` で作るものなど) を手で直す。生成のスクリプトを使う。
- 頼まれていないのに、リリース・Homebrew cask・winget などの配布まわりのワークフロー (`.github/workflows`・`Casks/`・`packaging/`) を変える。
