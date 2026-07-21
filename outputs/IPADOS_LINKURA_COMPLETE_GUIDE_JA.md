# iPadOS/iOS版リンクラ HASU API版＋LinkuraVisualsIOS 0.8.1 完全導入ガイド

更新日: 2026年7月20日

この文書は、何も導入していないiPad
/iPhoneから始めて、次の状態まで進むための手順書です。

- iOS版リンクラ5.0.1を、HASU APIへ接続する
  5.1.0互換IPAへ変換する
- まずJIT・Tweakなしで起動し、ログインと約16.6GBの初回データ取得を完了する
- その後、LiveContainer、StikDebug、JIT、LinkuraVisualsIOS 0.8.1を設定する
- 60 FPS、解像度変更、活動記録・With×MEETSのカメラ、WM全長シーク、
  正規所持済みFesチケット／WM AFTERの誤判定修復などを利用する
- 7日署名の更新、日常の起動、更新、故障時の復旧まで行う

最初から拡張機能を入れず、**「基礎導入」と「拡張導入」を必ず分けて確認する**
のが重要です。基礎版が動くことを先に確認すれば、問題がIPA・API・JIT・Tweakの
どこにあるか切り分けられます。

---

## 0. 最初に読む注意事項

### 0.1 非公式構成である

この構成は、リンクラ公式、Apple、LiveContainer、SideStore、StikDebugの
各開発者による公式サポート対象ではありません。アプリ、API、iPadOS、
LiveContainerの更新により、将来動かなくなる可能性があります。

### 0.2 必要なのは「復号済み」「ネイティブ5.0.1」のIPA

LinkuraVisualsIOS 0.8.1が対応するのは、ネイティブバイナリの実体が5.0.1で、
API向けのクライアント表示だけを5.1.0へ合わせたIPAです。

- 適合: ネイティブ実体5.0.1＋HASU API向け表示5.1.0
- 不適合: 暗号化されたApp Store IPA
- 不適合: ネイティブ実体が別バージョンのIPA
- 不適合: Android APK

JSONの `Compatibility.BinaryVersion` は必ず `"5.0.1"` のままにします。

### 0.3 第三者APIへ情報が送られる

HASU APIは公式サーバーではなく第三者運営サービスです。ログイン情報、
セッショントークン、プレイデータ等が第三者サーバーへ送られる可能性があります。
運営者の説明とプライバシー条件を確認し、本番用・重要アカウントを避け、
検証用アカウントを使用してください。

- [HASU setup](https://alfa-l4.hasu-link.club/setup)
- [linkura-localify](https://github.com/ChocoLZS/linkura-localify)

パスワード、Apple Accountの確認コード、ペアリングファイル、署名証明書を
他人へ送らないでください。

### 0.4 権利判定修復は「正規所持済み」の場合だけ使う

LinkuraVisualsIOSには、正当に所持しているFesチケットや、正規に到達済みの
With×MEETS AFTERが誤って未解放と判定される場合の互換修復があります。

これは未所持チケットの付与、未購入コンテンツの解放、スター数・ポイント・
購入状態の改変を行う機能ではありません。実際に権利を持つ場合だけ有効にし、
チケットランクは自分の所持内容に合わせてください。

### 0.5 容量と時間

初回追加データは約 `16,600.4MB` と表示されます。展開・一時領域も考慮し、
最低25GB、できれば30GB以上の空き容量を用意してください。安定したWi-Fi、
充電器、十分な時間も必要です。

---

## 1. 全体の流れ

1. Mac、iPad、Apple Account、必要ファイルを準備する
2. 復号済み5.0.1 IPAを、MacでHASU API向け5.1.0互換版へ変換する
3. 公式手順でLiveContainer＋SideStoreをiPadへ導入する
4. SideStoreで署名し、LiveContainerへ証明書を取り込む
5. 変換済みIPAをLiveContainerへ入れる
6. **調整フォルダ `None`、JITオフ**で基礎動作を確認する
7. 約16.6GBのデータ取得を完了する
8. StikDebug、ペアリングファイル、LocalDevVPN、JITを準備する
9. LinkuraVisualsIOS 0.8.1を調整フォルダへ入れる
10. **調整フォルダ `LinkuraVisualsIOS`、JITオン**で拡張機能を確認する

---

## 2. 用意するもの

### 2.1 Mac

Windows OS搭載PCでも可能だと思いますが未検証です。iLoaderの導入とiPad/iPhoneへのファイルの送信ができれば問題ないです。

- macOSを搭載したMac
- iPadと接続できるUSBケーブル
- ターミナル
- Python 3
  - ターミナルで `python3 --version` が成功すること
  - 見つからない場合は、Python公式配布物またはHomebrew等、自分が管理できる
    信頼できる方法でPython 3を導入してから進む
- 2ファクタ認証を有効にしたApple Account
  - 普段使いとは別のサイドロード専用アカウントを推奨
  - 無料アカウントでは原則7日ごとに署名更新が必要
- 自分で正当に入手した復号済みiOS版リンクラ5.0.1 IPA
- 次のパッチファイル3点
  - `patch_ipa_api_510_compat.sh`
  - `patch_unityfs_bundle_version.py`
  - `verify_unityfs_versions.py`
- LinkuraVisualsIOS 0.8.1配布ZIP
  - `LinkuraVisualsIOS-0.8.1-wm-cover-and-play-pause.zip`

### 2.2 iPad/iPhone

- iPadOS/iOS 15以降
  - この構成はiPadOS/iOS 26.5.2でも実機確認済み
  - **第1段階の基礎導入**はiPadOS 15以降が対象
  - このガイドのStikDebugを使う**第2段階の完全導入**はiPadOS 17.4以降が対象
  - iPadOS 15～17.3では、別の対応JIT手段を自分で用意できない限り、第1段階
    までで止める。この文書では別方式のJIT設定は扱わない
- 25～30GB以上の空き容量
- 安定したWi-Fi
- 充電環境
- デベロッパモード
- LiveContainer＋SideStore
- LocalDevVPN
- 拡張機能を使う場合はStikDebugと有効なペアリングファイル

### 2.3 iPadOS/iOS 26で拡張機能を使う場合だけ必要

- 現行LiveContainerに対応する `dobby.dylib`
- 現行LiveContainer／Geode環境に対応する `Geode.js`

この2ファイルはLinkuraVisualsIOS配布ZIPには含まれていません。互換性の分からない
古いファイルや、出所不明のバイナリを使わず、使用中のLiveContainerに対応する
信頼できる配布元から入手してください。`Geode.js` は使用する公式StikDebugと
同じリリースのスクリプトを使い、`dobby.dylib` は
[LLLLResUpiOSの公式案内](https://github.com/DYY-Studio/LLLLResUpiOS)と
[Dobby公式ソース](https://github.com/jmpews/Dobby)を確認してください。

実機で動作確認した組み合わせの互換性識別情報は次の通りです。これは配布元の
真正性を保証するものではなく、**既に信頼できる経路で入手したファイルが、
確認済み組み合わせと同一かを照合するための参考値**です。

```text
dobby.dylib
size: 183968 bytes
SHA-256: 496703fcc5446930bd8a7c5f6d5ebaaefef0322fdba115df0186f6a0db17b472

Geode.js
size: 5859 bytes
SHA-256: 6fa925200dd7916f3c670c913d409091cb687269d9efb8b18d35c2eaf73290af
```

値が異なる場合、ただちに危険という意味ではありませんが、このガイドで確認した
組み合わせとは別物です。対応関係を確認できないまま試行せず、第1段階で止めます。

### 2.4 この作業フォルダ内の配布物

このガイドと同じ作業フォルダを受け取った場合、必要な自作配布物は次の場所に
あります。

- [IPA変換スクリプト](../work/ios_api_hook/patch_ipa_api_510_compat.sh)
- [UnityFSバージョン変更補助](../work/ios_api_hook/patch_unityfs_bundle_version.py)
- [UnityFS検証補助](../work/ios_api_hook/verify_unityfs_versions.py)
- [LinkuraVisualsIOS 0.8.1 ZIP](../work/ios_extensions/LinkuraVisualsIOS/dist/LinkuraVisualsIOS-0.8.1-wm-cover-and-play-pause.zip)

ガイドを単独で渡す場合は、上記スクリプト3点と0.8.1 ZIPを、ライセンスと
ソースを保持したまま別途添付してください。受け取る側は、後述するSHA-256で
ファイルを確認します。

---

## 3. 公式ツールの入手先

第三者が再梱包したLiveContainerやオンライン署名サイトを避け、必ず公式の
オープンソース配布物と公式手順を使ってください。

- [LiveContainer公式インストール案内](https://livecontainer.github.io/docs/installation)
- [LiveContainer＋SideStore公式手順](https://livecontainer.github.io/docs/installation/lc_sidestore)
- [LiveContainer公式Releases](https://github.com/LiveContainer/LiveContainer/releases)
- [SideStore公式インストール案内](https://docs.sidestore.io/docs/installation/install)
- [SideStore事前準備・LocalDevVPN](https://docs.sidestore.io/docs/installation/prerequisites)
- [iLoader公式サイト](https://iloader.app/)
- [StikDebug公式リポジトリ](https://github.com/StephenDev0/StikDebug)
- [StikDebug公式Releases](https://github.com/StephenDev0/StikDebug/releases)
- [StikDebug公式Pairing File Instructions](https://github.com/StephenDev0/StikDebug-Guide/blob/main/pairing_file.md)

LiveContainer公式は、Sideloadly、3u/i4 Tools、多くのオンライン署名サービス等を
非対応としています。LiveContainer＋SideStoreは、公式説明に従って最新の
iLoaderまたはImpactorで導入してください。古いiLoaderは正しく署名できない場合が
あるため、最新のものを使用します。

---

## 4. Apple Accountを準備する

1. サイドロード専用Apple Accountを用意します。
2. 2ファクタ認証を有効にします。
3. MacのSafariで
   [Apple Developer Account](https://developer.apple.com/account/)を開きます。
4. 同じApple Accountでサインインします。
5. Apple Developer Agreementが表示された場合だけ、内容を確認して同意します。

有料のApple Developer Programへの加入は必須ではありません。無料アカウントでは
原則7日ごとに再署名します。

---

## 5. 復号済み5.0.1 IPAをMacで変換する

(これはGoogle Drive上のipaファイルを使う場合は飛ばして良いです)

最初に、MacのターミナルでPython 3が使えることを確認します。

```zsh
python3 --version
```

`Python 3.x.x` と表示されない場合は、ここで作業を止め、第2.1節の案内に従って
Python 3を導入してから再開してください。

### 5.1 パッチファイルを同じフォルダへ置く

次の3ファイルを同じフォルダへ置きます。

```text
patch_ipa_api_510_compat.sh
patch_unityfs_bundle_version.py
verify_unityfs_versions.py
```

このスクリプトは次を変更します。

- API URL:
  `https://api.link-like-lovelive.app`
  → `https://api-alfa-l4.hasu-link.club`
- Unity PlayerSettingsのクライアントバージョン:
  `5.0.1` → `5.1.0`
- `Info.plist` の表示バージョン:
  `5.0.1` → `5.1.0`

ネイティブ実行バイナリそのものは5.0.1のままです。

### 5.2 元IPAのハッシュを記録する

実機確認に使用した元IPAのSHA-256参考値は次です。

```text
5d65a125b7701f511c3aabb9c45e3a22179b25cdf2be2293de652961a4dd1be5
```

ターミナルで確認します。

```zsh
shasum -a 256 "/path/to/original-5.0.1-decrypted.ipa"
```

復号・再梱包方法やZIP圧縮条件が違えば、同じ5.0.1でもIPA全体のハッシュは
変わります。そのため不一致だけで不適合とは判断しません。各自の元ファイルの
ハッシュを記録したうえで、入手元、復号状態、アプリの表示版、スクリプトの
検証結果を確認してください。

### 5.3 通常版を生成する

ターミナルでパッチファイルのフォルダへ移動し、次を実行します。

```zsh
chmod +x patch_ipa_api_510_compat.sh
./patch_ipa_api_510_compat.sh \
  "/path/to/original-5.0.1-decrypted.ipa" \
  "/path/to/Linkura-5.1.0-hasu-synced.ipa"
```

成功すると、最後に次の内容が表示されます。

```text
created: ...
API URL: ... -> ...
managed client version: 5.0.1 -> 5.1.0
CFBundleShortVersionString: 5.0.1 -> 5.1.0
resource version: kept at R2604001
```

実機でログインと追加データ取得まで確認したのは、内部素材バージョン
`R2604001` を維持するこの通常版です。

### 5.4 `--spoof-resource-version` は通常使わない

スクリプトには素材バージョンも変更するオプションがありますが、現在の再現手順
では使用しません。通常版で不足するとAPI運営側から明示された場合だけ検討します。

### 5.5 出力IPAの注意

パッチ後は元のコード署名が無効になります。iPadへ通常のアプリとして直接入れず、
LiveContainerで読み込み、LiveContainer側で再署名して実行します。

参考として、確認済み通常版のSHA-256は次です。

```text
b33b37231409dc488ce9869f1cd4860a9843aa7707c77c41ea0ce3288bf67386
```

この値は改変済みIPAを共有するためのものではありません。各自の元IPAと
パッチスクリプトから再生成してください。

---

## 6. LiveContainer＋SideStoreをiPadへ導入する

画面名はiPadOSやLiveContainerの更新で少し変わる場合があります。

### 6.1 Macからインストールする

1. 最新のiLoaderまたはLiveContainer公式が案内するImpactorをMacへ入れます。
2. iPadをUSB接続します。
3. iPadのロックを解除します。
4. 「このコンピュータを信頼」が出たら「信頼」を選びます。
5. LiveContainer公式手順に従い、`LiveContainer + SideStore` を選んで
   インストールします。
6. インストール完了までUSB接続を維持します。

安定版とNightlyのどちらを使うかは、公式の対応表に従ってください。iPadOS 26で
JITスクリプトを使う場合は、古いビルドを避け、対応する現行版を使用します。

### 6.2 デベロッパAppを信頼する

iPadで次を開きます。

```text
設定
└─ 一般
   └─ VPNとデバイス管理
```

「デベロッパApp」欄でインストールに使ったApple Accountを選び、「信頼」を
押します。

### 6.3 デベロッパモードをオンにする

```text
設定
└─ プライバシーとセキュリティ
   └─ デベロッパモード
```

デベロッパモードをオンにします。再起動を求められた場合は再起動し、起動後に
有効化を確定します。

---

## 7. LocalDevVPNと内蔵SideStoreを設定する

### 7.1 LocalDevVPN

1. [SideStore公式事前準備](https://docs.sidestore.io/docs/installation/prerequisites)
   から案内されるLocalDevVPNをインストールします。
2. LocalDevVPNを開きます。
3. VPN構成の追加を許可します。
4. `Connect` を押し、`Connected` になったことを確認します。

LocalDevVPNはゲームのAPI接続先を変えるVPNではありません。SideStoreの署名更新と
StikDebugの端末内接続に使います。

### 7.2 内蔵SideStoreへサインインする

1. LiveContainerを開きます。
2. 「アプリ」画面左上のSideStoreアイコンを押します。
3. 内蔵SideStoreの設定を開きます。
4. 手順4で用意したApple Accountへサインインします。
5. 6桁の確認コードが出たら、自分の端末に届いたコードを入力します。

`invalid Trust Key` や `-45003` が出る場合は、SideStore設定の
Anisette Serverを公式推奨のものへ変更し、再試行します。過去の確認環境では
`SideStore (.zip)` / `https://ani.sidestore.zip` で解決しましたが、
現在のSideStore公式案内を優先してください。

### 7.3 署名を更新する

1. LocalDevVPNが `Connected` であることを確認します。
2. 内蔵SideStoreの `My Apps` を開きます。
3. `Refresh All`、または対象アプリ横の残り日数を押します。
4. LiveContainerの残り日数が約 `7 DAYS` になったことを確認します。
5. SideStoreを終了してLiveContainerへ戻ります。

### 7.4 証明書をLiveContainerへ取り込む

1. LiveContainerの「設定」を開きます。
2. `SideStoreから証明書をインポート` を実行します。
3. ボタンが「証明書を削除」相当の表示に変われば取り込み済みです。
4. `JITなしモード診断` を開きます。
5. `JITレスモードテスト` を実行します。
6. 成功表示を確認します。

証明書が見つからない場合は、
[LiveContainer＋SideStore公式手順](https://livecontainer.github.io/docs/installation/lc_sidestore)
の「Export Signing Certificate」回避手順を使用してください。

---

## 8. 変換済みIPAをiPadへ転送する

AirDropではLiveContainerのファイルとして正しく表示されない場合があります。
USB接続とFinderのファイル共有が安定しています。

1. MacとiPadをUSB接続します。
2. MacのFinderでiPadを選びます。
3. 「ファイル」タブを開きます。
4. LiveContainerを開きます。
5. 作成した `Linkura-5.1.0-hasu-synced.ipa` をコピーします。
6. コピー完了後、iPadでLiveContainerをアプリスイッチャーから完全終了します。
7. LiveContainerを開き直します。

---

## 9. IPAをLiveContainerへインストールする

### 9.1 初回

1. LiveContainerの「アプリ」画面を開きます。
2. 左上の「＋」を押します。
3. 「IPAファイルをインストール」を選びます。
4. 転送したIPAを選びます。
5. 「新規インストール」を選びます。

### 9.2 元の5.0.1も残したい場合

同じバンドル識別子でも「新規インストール」を選ぶと別エントリにできます。
どちらか分かるよう、アプリを長押し→「設定」→「備考」に、例えば次を入力します。

```text
HASU API 5.1.0静的置換版
```

更新時に既存エントリを選ぶ場合は、元の5.0.1ではなく、現在使用中の
HASU版バンドルフォルダを選んでください。

---

## 10. 第1段階: JIT・Tweakなしで基礎動作を確認する

拡張機能を入れる前に、必ずこの状態で起動します。

### 10.1 アプリ設定

インストールしたリンクラを長押しし、「設定」を開きます。

| 項目 | 基礎確認時の設定 |
|---|---|
| 調整フォルダ | `None` |
| JITで起動 | オフ |
| JIT起動スクリプト | なし |
| ファイル選択を修正 | オフ |
| ローカル通知を修正 | オフ |
| LiveContainerのバンドル識別子を使用 | オフ |
| Dylib APIからLiveContainerを隠す | オフ |
| TweakLoaderを注入しない | 通常はオフ |
| 外部dylib | 追加しない |

この段階ではStikDebug、Dobby、Geode.js、LinkuraVisualsIOSを使いません。

### 10.2 初回起動

1. パッチ版の「実行」を押します。
2. タイトル左上が `Ver.5.1.0` であることを確認します。
3. 検証用LinkLikeIDでログインします。
4. ユーザー作成・ログイン処理を進めます。
5. 約 `16,600.4MB` の追加データ確認が表示されれば、API URL、
   クライアントバージョン、ログイン処理を通過しています。

### 10.3 追加データを取得する

1. 25～30GB以上の空き容量を再確認します。
2. 充電器を接続します。
3. 安定したWi-Fiへ接続します。
4. `OK` を押します。
5. ダウンロード中はLiveContainer／リンクラを前面に保ちます。
6. 画面をロックせず、アプリを強制終了しません。

ダウンロードは複数区分に分かれるため、区分切替時に容量表示や進捗率が
リセットされたように見える場合があります。

### 10.4 この段階の合格条件

- `Ver.5.1.0` と表示される
- ログインできる
- 初回データ取得が進む
- データ取得後にホーム画面へ入れる
- JITなしで安定して起動できる

ここまで成功してから拡張導入へ進みます。

---

## 11. 第2段階: StikDebugとJITを準備する

LinkuraVisualsIOSはTweakなのでJITが必要です。StikDebugはiOS/iPadOS 17.4以降で
端末内JITを有効にできます。初回にはMacで作成した、そのiPad専用の有効な
ペアリングファイルが必要です。

iPadOS 15～17.3でこの章へ進まないでください。このガイドに記載するStikDebug方式
の対象外です。iPadOS 26では、LiveContainerのiOS 26 JITスクリプト対応版と、
互換するDobby／Geode.jsの組み合わせが追加で必要です。

### 11.1 StikDebugを導入する

1. [StikDebug公式リポジトリ](https://github.com/StephenDev0/StikDebug)の
   公式配布方法を確認します。
2. 公式Release、公式AltSource、または自分でビルドしたIPAを使用します。
3. SideStore等でStikDebugをインストールします。
4. 必要に応じてデベロッパAppを信頼します。

StikDebugの入手方法は変更される可能性があります。App Store版の有無を前提にせず、
公式リポジトリが案内する現行の配布方法を使い、非公式再配布サイトは使わないで
ください。

### 11.2 ペアリングファイルを用意する

1. [StikDebug公式Pairing File Instructions](https://github.com/StephenDev0/StikDebug-Guide/blob/main/pairing_file.md)
   を開きます。
2. 対象iPadをMacへUSB接続し、ロックを解除してMacを信頼します。
3. MacのiLoaderで `Manage Pairing File` を開きます。
4. `StikDebug` の右側にある `Place` を押します。
5. `Pairing file placed successfully!` が表示されたことを確認します。

手動でペアリングファイルを書き出した場合は、iPadへ安全に転送し、
StikDebugの `Import Pairing File` から取り込みます。iLoaderやStikDebugの
画面が変更された場合は、この文書より公式Pairing File Instructionsを優先します。

ペアリングファイルには端末接続用の機密情報が含まれます。公開・共有しないで
ください。iPadOS更新、端末リセット、再ペアリング等で無効になった場合は
作り直します。

### 11.3 StikDebugを確認する

1. Wi-Fiへ接続します。
2. LocalDevVPNを `Connected` にします。
3. iPadをロック解除したままStikDebugを開きます。
4. `Apps` → `JIT` にLiveContainerが表示されることを確認します。

`Connection Error`、`Operation timed out (os error 60)`、heartbeatエラーの場合:

- Wi-FiとLocalDevVPNの両方が接続済みか確認する
- iPadを起こしてロック解除する
- ペアリングファイルを再取り込みする
- StikDebugとLocalDevVPNを完全終了して開き直す
- StikDebugのTarget Device IPが、LocalDevVPNの案内する値と一致するか確認する
- OS更新後ならペアリングファイルを作り直す

### 11.4 iPadOS/iOS 26用のDobbyとGeode

1. 使用中の公式StikDebugと同じリリースの `Geode.js` を用意します。
2. 「2.3」のサイズとSHA-256を記録し、入手元・StikDebug・LiveContainerの
   バージョンもメモします。
3. `Geode.js` をFinderのLiveContainerファイル領域へコピーします。
4. 対応する `dobby.dylib` は、次項で作るLinkuraVisualsIOS調整フォルダへ
   コピーします。

別バージョン用のDobbyやGeode.jsを混ぜると、起動しない、JIT待機のままになる、
Tweakが読み込まれない、クラッシュする等の原因になります。

---

## 12. LinkuraVisualsIOS 0.8.1を導入する

使用するのは次の配布物だけです。

```text
LinkuraVisualsIOS-0.8.1-wm-cover-and-play-pause.zip
```

古い0.7.x、診断版、個別修正版を選ばないでください。

配布物の確認用SHA-256:

```text
ZIP:
e3aa1b1586681c867e8f2ecbf2980e648d8ca3cb9d276d168b14862336874120

単体dylib:
e46bedef60c190101d5089c80e775cf103f5c9068c708b70259b23b73237d6c4
```

### 12.1 ZIPを展開する

ZIPを展開すると、`Install` フォルダに次の3ファイルがあります。

```text
LinkuraVisualsIOS.dylib
LinkuraVisualsIOS.json
IL2CPP_OFFSETS_5.0.1.json
```

### 12.2 調整フォルダを作る

1. LiveContainerを開きます。
2. 上部の「調整」タブを開きます。
3. 右上の「＋」→「新規フォルダ」を選びます。
4. 名前を `LinkuraVisualsIOS` にします。
5. フォルダを開きます。
6. 「調整をインポート」またはファイルアプリから、上記3ファイルを入れます。
7. iPadOS/iOS 26では、同じフォルダへ対応する `dobby.dylib` も入れます。

最終的に次のようにします。

```text
LinkuraVisualsIOS/
├─ LinkuraVisualsIOS.dylib
├─ LinkuraVisualsIOS.json
├─ IL2CPP_OFFSETS_5.0.1.json
└─ dobby.dylib                 # iPadOS/iOS 26
```

LiveContainerの調整画面にスイッチが表示される場合は、4ファイルをオンにします。
親画面にある `TweakLoader.dylib` はLiveContainer側の管理ファイルです。
削除・改名せず、そこにオン／オフ項目がなくても異常ではありません。

### 12.3 アプリへ調整フォルダを割り当てる

1. 「アプリ」タブへ戻ります。
2. HASU版リンクラを長押しします。
3. 「設定」を開きます。
4. `調整フォルダ` に `LinkuraVisualsIOS` を選びます。
5. `JITで起動` をオンにします。
6. iPadOS/iOS 26では `JIT起動スクリプト` に `Geode.js` を選びます。

LiveContainer全体の設定に `JITイネーブラー` がある場合は `StikDebug` を選びます。

### 12.4 初回JIT起動前に権利修復を安全な状態へ戻す

0.8.1配布ZIPのJSONには、今回の実機検証に使った権利誤判定修復値が含まれて
います。他の利用者は、**初回JIT起動より前に** `LinkuraVisualsIOS.json` を
編集し、次の2項目をいったん `false` にしてください。

```json
"FesArchive.ValidTicketRepair.Enable": false,
"WithMeets.After.ValidAdmissionRepair.Enable": false,
"WithMeets.Archive.PlayPauseButton.Enable": false
```

保存後、JSON編集画面で両方がBooleanの `false` と表示されることを確認します。
基礎機能とカメラUIの動作確認が終わったあと、正規所持済みの権利が誤判定される
場合に限り、第17.3節・第17.4節と、第21.16節・第21.17節を読み、実際の
所持内容へ合わせて有効にします。

この確認を済ませるまで、JITを有効にしてリンクラを起動しないでください。

### 12.5 初回JIT起動

1. Wi-Fiへ接続します。
2. LocalDevVPNを `Connected` にします。
3. LiveContainerからHASU版リンクラの「実行」を押します。
4. `JITを待機中` と表示され、StikDebugへ移動します。
5. StikDebugに
   `Enable JIT?` / `Enable and Run Script`
   が出たら、`Enable and Run Script` を押します。
6. リンクラが起動するまで待ちます。

StikDebugを開いただけで何も起きない場合は、StikDebugの `Apps` → `JIT` で
LiveContainerを選び、JITを有効にしてからLiveContainerへ戻ります。

`JITなしで実行` は基礎動作確認・緊急復旧用です。LinkuraVisualsIOSの機能を
使う起動では選びません。

---

## 13. 拡張機能が読み込まれたか確認する

次の順で確認します。

1. タイトル画面が `Ver.5.1.0`
2. アプリ内のグラフィック設定に、Story倍率
   `0.6x / 1.0x / 1.4x` が表示される
3. 対象の活動記録本編でカメラパネルが出る
4. 対応するWith×MEETS 3Dアーカイブでカメラパネルとシークバーが出る
5. WMシークバー左に再生／一時停止ボタンが出る

`0.6x` 等がなく、カメラパネルも出ない場合は、アプリ本体は起動していても
Tweakが読み込まれていません。「21. トラブルシュート」を確認してください。

---

## 14. LinkuraVisualsIOS 0.8.1で使える機能

### 14.1 映像・描画

- With／Fes LiveStreamの解像度変更
  - Low: 短辺720
  - Medium: 短辺1080
  - High: 短辺1440
- Story描画解像度
  - Low: 0.6倍
  - Medium: 1.0倍
  - High: 1.4倍
- 目標60 FPS
- 4xアンチエイリアス
- MagicaCloth 60Hz、1フレーム最大3回計算

値を上げるほど発熱、消費電力、処理落ち、クラッシュの危険が増えます。
最初は同梱値で確認してください。Storyのズーム時に見かけの画質が落ちる挙動は、
元の描画方式にも依存します。

### 14.2 Fesアーカイブ

- Fesカメラの移動距離・回転角・FOV調整
- 正規所持済みチケットのランク／カメラ権限が誤認された場合の互換修復

同梱JSONはSランク相当とカメラ4種が設定されています。自分の所持チケットと
異なる場合は必ず実際の内容へ変更するか、修復をオフにします。

### 14.3 活動記録

- 本編の自由カメラ
- 縦横画面切替の互換修復
- 背景、遷移、非キャラクター3D、被写界深度、プリセットエフェクトの個別非表示
- 左端タブによるスクリーンショット用UI一時非表示

実機確認では:

- 3D背景セットを消す: `ActivityRecord.HideNonCharacter3D=true`
- 背景上のグラデーションを消す: `ActivityRecord.HidePresetEffect=true`

`HideBackground` だけでは、非キャラクター3Dとして実装された背景が残る場面が
あります。

### 14.4 With×MEETSアーカイブ

- 既知59件と、サーバーが有効な `.md` URLを返す回のALST/IARC 3D再生
- アーカイブごとの縦／横画面判定の復元
- IARC全長シーク
- 固定映像区間境界での誤ったREPLAY、暗転、入力遮断、自動停止の抑止
- 開始前やAFTER暗転区間の固定待機カバーを抑止し、背後の映像を表示
- 正規到達済みAFTERが誤って未解放の場合の、完全一致証拠に基づく互換修復
- WM標準シークバー左の再生／一時停止ボタン
- IARC 3Dアーカイブの自由カメラ
- スクリーンショット用UI一時非表示

#### HLS/USMとIARCの違い

| 形式 | 内容 | 自由カメラ |
|---|---|---|
| HLS/USM | 収録済みの固定2D映像 | 不可 |
| StreamingIarc / ALST / IARC | 端末で3Dモデル・モーションを再生 | 可 |

固定動画しか存在しない回では、映像に視点情報が追加されるわけではないため、
カメラパネルは表示されません。シークや再生／一時停止等のWM共通機能は対象に
なる場合があります。

カタログ外で `.md` URLが返らない回は、安全のためURLを推測せず固定映像を
維持します。

### 14.5 意図的に含まれない機能

- 翻訳
- フォント置換
- 未所持AFTERの解放
- 未所持チケットの付与
- 購入状態、スター数、ポイントの改変
- Focus範囲制限の回避
- プレイヤーIDの改変

---

## 15. カメラパネルの使い方

対象の活動記録、またはWMの `StreamingIarc` 本編カメラが確定すると、
左上にメインパネル、右下にジョイスティックが出ます。

1. 左上の `GAME` を押し、表示を `FREE` に切り替えます。
2. カメラを操作します。
3. ゲーム側のカメラ制御へ戻すときは `FREE` を押して `GAME` に戻します。

### 15.1 右側パネル

| 操作 | 動作 |
|---|---|
| 右ジョイスティック | カメラ基準で前後左右へ連続平行移動 |
| `←` / `→` | 同じカメラ位置から視線だけを左右へ連続回転 |
| `* XZ` / `* XY` | ジョイスティック前後を、前後移動／ワールド上下移動へ切替 |
| `R` | FREEへ切替時の位置・回転・ズームへ戻す |

### 15.2 左側パネル

| 操作 | 動作 |
|---|---|
| `←` / `→` | 左右へ1段階移動 |
| `↑` / `↓` | 前後へ1段階移動 |
| `+Y` / `-Y` | ワールド基準で上下移動 |
| `YAW ←` / `YAW →` | 左右へ回転 |
| `P ↑` / `P ↓` | 上下へ回転 |
| `Q −` / `E +` | 長押し中ズームアウト／ズームイン |
| `RESET` | FREEへ切替時の状態へ戻す |

透視カメラでは `E +` がFOVを小さくし、見た目を拡大します。平行投影では
表示サイズを小さくします。対象カメラが演出により切り替わると、安全のため
`GAME` へ戻る場合があります。

### 15.3 スクリーンショット用にUIを隠す

画面左端中央の小さな `◀` タブを押すと、左パネルと右ジョイスティックをまとめて
隠せます。非表示中はタブも透明になります。同じ左端中央の位置を再度押すと
戻ります。カメラ位置、回転、ズーム、FREE状態は維持されます。

---

## 16. WMのシーク、REPLAY、待機画面、再生／一時停止

### 16.1 全長シーク

`WithMeets.Archive.IarcFullSeek.Enable=true` では、固定映像区間の境界を越えて
IARCアーカイブ全長へシークできます。過去に29分／50分のような不一致が
ありましたが、0.8.1では表示上限と内部再生可能率の両方を補正します。

### 16.2 誤REPLAYの抑止

`WithMeets.Archive.IarcReplayOverlay.Suppress=true` では、固定映像区間の境界を
誤って終端と判断した場合の中央REPLAY、薄暗化、入力遮断、0秒復帰、自動停止を
抑止します。本来の実終端は純正処理を維持します。

### 16.3 固定待機カバーの抑止

`WithMeets.Archive.RenderImageCover.Suppress=true` では、WMアーカイブの
開始前やAFTER暗転中に固定待機画像を前面へ出さず、背後で描画されている映像を
見える状態にします。

### 16.4 再生／一時停止

`WithMeets.Archive.PlayPauseButton.Enable=true` では、WM標準シークバー左側に
小さな再生／一時停止ボタンが出ます。

- 一時停止: 現在位置で停止
- 再生: 同じ位置から再開
- 一覧へ戻る: WMモデル破棄に合わせてボタンも消える

0秒から再生し直す処理やシーク位置変更は行いません。

---

## 17. JSON設定を編集する

設定ファイルは `LinkuraVisualsIOS.json` です。

### 17.1 編集前に必ずバックアップする

調整フォルダ内のJSONを複製し、例えば次の名前で保存します。

```text
LinkuraVisualsIOS.backup.json
```

更新ZIPのJSONで上書きすると、活動記録の非表示設定など、自分で変えた値が
配布初期値へ戻ります。更新時は旧JSONを保管し、新しいキーだけ追加する方法が
安全です。

### 17.2 JSONの注意

- キー名は完全一致
- キー末尾に空白を入れない
- `true` / `false` はBooleanとして書く
- `"true"` のような文字列にしない
- 行間や字下げの空白は問題ない
- キー名の引用符内に入った空白は別キーになる
- 最後の項目以外は行末のカンマを忘れない
- `Compatibility.BinaryVersion` は変更しない

誤りの例:

```json
"WithMeets.Archive.IarcFullSeek.Enable ": true
```

正しい例:

```json
"WithMeets.Archive.IarcFullSeek.Enable": true
```

編集後はリンクラとLiveContainerを完全終了し、LocalDevVPN＋StikDebugで
JITを取り直して起動します。

### 17.3 主な設定と0.8.1配布値

| キー | 配布値 | 内容 |
|---|---:|---|
| `Compatibility.BinaryVersion` | `"5.0.1"` | 変更禁止 |
| `TargetFPS` | `60` | 目標FPS |
| `AntiAliasingSamples` | `4` | AA。通常1/2/4/8 |
| `LiveStream.Quality.Low.ShortSide` | `720` | LiveStream Low短辺 |
| `LiveStream.Quality.Medium.ShortSide` | `1080` | LiveStream Medium短辺 |
| `LiveStream.Quality.High.ShortSide` | `1440` | LiveStream High短辺 |
| `Story.Quality.Low.Factor` | `0.6` | Story Low倍率 |
| `Story.Quality.Medium.Factor` | `1.0` | Story Medium倍率 |
| `Story.Quality.High.Factor` | `1.4` | Story High倍率 |
| `MagicaCloth.SimulationFrequency` | `60` | 布シミュレーション周波数 |
| `MagicaCloth.MaxSimulationCountPerFrame` | `3` | 1フレーム最大計算回数 |
| `Enable.FesCameraHook` | `true` | Fesカメラ調整 |
| `FesArchive.ValidTicketRepair.Enable` | `true` | 実機検証用配布値。初回JIT前に`false`へ変更 |
| `FesArchive.ValidTicketRepair.TicketRank` | `6` | 実機検証用配布値はS。実所持ランク以外に使わない |
| `FesArchive.ValidTicketRepair.SelectableCameraTypes` | `[1,2,3,4]` | 実機検証用配布値。実際に利用できるカメラだけに合わせる |
| `ActivityRecord.HideBackground` | `false` | 背景命令を除外 |
| `ActivityRecord.HideTransition` | `false` | 暗転・遷移命令を除外 |
| `ActivityRecord.HideNonCharacter3D` | `false` | キャラ以外の3Dを除外 |
| `ActivityRecord.HideDepthOfField` | `false` | 被写界深度を除外 |
| `ActivityRecord.HidePresetEffect` | `false` | プリセット効果を除外 |
| `ActivityRecord.CameraControl.Enable` | `true` | 活動記録カメラ |
| `ActivityRecord.LandscapeRepair.Enable` | `true` | 活動記録の縦横修復 |
| `WithMeets.CameraControl.Enable` | `true` | WM IARCカメラ |
| `WithMeets.Archive.MotionCaptureReplay.Enable` | `true` | 対応WMをIARC優先 |
| `WithMeets.Archive.IarcFullSeek.Enable` | `true` | WM IARC全長シーク |
| `WithMeets.Archive.IarcReplayOverlay.Suppress` | `true` | 誤REPLAY・暗転・自動停止を抑止 |
| `WithMeets.Archive.OrientationRepair.Enable` | `true` | WM縦横修復 |
| `WithMeets.Archive.RenderImageCover.Suppress` | `true` | 固定待機カバーを抑止 |
| `WithMeets.Archive.PlayPauseButton.Enable` | `true` | WM再生／一時停止。動作未確認なので`false`へ |
| `WithMeets.After.ValidAdmissionRepair.Enable` | `true` | 実機検証用配布値。初回JIT前に`false`へ変更 |
| `CameraControl.UI.Enable` | `true` | カメラUI |
| `CameraControl.UI.ScreenshotHide.Enable` | `true` | UI一時非表示 |
| `CameraControl.Joystick.Enable` | `true` | 右ジョイスティック |

### 17.4 Fesランクとカメラ種別

チケットランク:

| 値 | ランク |
|---:|---|
| 1 | Guest |
| 2 | D |
| 3 | C |
| 4 | B |
| 5 | A |
| 6 | S |
| 7 | E |

カメラ種別:

| 値 | カメラ |
|---:|---|
| 1 | Dynamic |
| 2 | Arena |
| 3 | Stand |
| 4 | SchoolIdle |

正規所持ランクと異なる値を設定しないでください。修復が不要なら:

```json
"FesArchive.ValidTicketRepair.Enable": false
```

### 17.5 活動記録の非表示機能は1項目ずつ試す

5項目を一度にオンにすると、どの設定が何を消したか分からなくなります。
まず全て `false` にし、1項目ずつ `true` にして同じ場面を比較します。

組み合わせにより背景が完全に空になる、意図した暗転が消える、演出の見え方が
変わる場合があります。

---

## 18. 毎回の起動手順

LinkuraVisualsIOSを使う通常起動は次の順です。

1. Wi-Fiへ接続する
2. LocalDevVPNを開き、`Connected` にする
3. StikDebugを一度開く
4. LiveContainerを開く
5. HASU版リンクラの「実行」を押す
6. `JITを待機中` からStikDebugへ移動したら、
   `Enable and Run Script` を押す
7. リンクラが起動し、`0.6x / 1.0x / 1.4x` 等があることを確認する

起動後もStikDebugがJIT取得にLocalDevVPNを必要とするため、安定性確認が終わる
までは接続したままにします。基礎版だけをJITなしで使う場合はLocalDevVPNは
SideStoreの署名更新時だけ必要です。

---

## 19. 7日署名を更新する

無料Apple Accountでは、期限切れ前に次を実行します。

1. Wi-Fiへ接続します。
2. LocalDevVPNを `Connected` にします。
3. LiveContainer左上から内蔵SideStoreを開きます。
4. `My Apps` を開きます。
5. `Refresh All` を押します。
6. LiveContainerが約 `7 DAYS` になったことを確認します。
7. LiveContainerへ戻ります。
8. 必要なら証明書を再インポートし、JITなしモード診断を確認します。

残り1日未満になる前に更新することを推奨します。

---

## 20. IPA・Tweakを更新する

### 20.1 IPAを更新する

1. データコンテナを削除しません。
2. 新しいIPAをFinderのLiveContainer領域へコピーします。
3. LiveContainerを完全終了して開き直します。
4. 「＋」→「IPAファイルをインストール」を選びます。
5. 現在使っているHASU版バンドルフォルダを選びます。
6. 更新後も以前と同じデータコンテナが選択されているか確認します。
7. まず調整フォルダ `None`、JITオフで基礎起動を確認します。
8. その後に調整フォルダとJITを戻します。

### 20.2 LinkuraVisualsIOSを更新する

1. 現在の `LinkuraVisualsIOS.json` をバックアップします。
2. アプリを完全終了します。
3. 調整フォルダの `LinkuraVisualsIOS.dylib` と
   `IL2CPP_OFFSETS_5.0.1.json` を新しいものへ置換します。
4. JSONは、自分の設定を保持するなら既存を残し、新規キーだけ追加します。
5. iPadOS/iOS 26では `dobby.dylib` が残っていることを確認します。
6. 全ファイルのスイッチをオンにします。
7. JITを取り直して起動します。
8. `0.6x`、活動記録、WMの順に確認します。

診断版や古い0.7.xを混在させず、0.8.1の3ファイルを同じセットで使用します。

---

## 21. トラブルシュート

### 21.1 タイトルが5.0.1のまま

`Info.plist` とUnity PlayerSettingsの両方が更新されていないIPAです。
現在のパッチスクリプトで通常版を作り直します。

### 21.2 ユーザー作成後に予期せぬエラー

API URLだけを変え、クライアントバージョンが5.0.1のままの版で起こります。
通常の `synced` 版を作り直します。

### 21.3 AirDropしたIPAを選べない

MacとiPadをUSB接続し、Finder→iPad→「ファイル」→LiveContainerへコピーします。

### 21.4 同じリンクラが2個表示される

故障ではありません。同じバンドル識別子を別バンドルフォルダへ新規インストール
した状態です。「備考」とデータコンテナで区別します。

### 21.5 `API-HOOKED` と表示されない

正常です。この構成は外部APIフックdylibではなくIPAの静的置換です。

### 21.6 `0.6x` がない、カメラパネルがない

Tweakが読み込まれていません。次を上から確認します。

1. リンクラとLiveContainerを完全終了する
2. アプリの `調整フォルダ` が `LinkuraVisualsIOS`
3. フォルダに次がある
   - `LinkuraVisualsIOS.dylib`
   - `LinkuraVisualsIOS.json`
   - `IL2CPP_OFFSETS_5.0.1.json`
   - iPadOS/iOS 26なら `dobby.dylib`
4. 調整画面の全ファイルがオン
5. `JITで起動` がオン
6. iPadOS/iOS 26ならJIT起動スクリプトが `Geode.js`
7. LiveContainerのJITイネーブラーが `StikDebug`
8. Wi-FiとLocalDevVPNが接続済み
9. StikDebugのペアリングファイルが有効
10. 起動時に `Enable and Run Script` を押した
11. `JITなしで実行` を選んでいない

それでも直らない場合は、調整フォルダの各ファイルを一度オフ→オンにする、
調整フォルダを `None`→`LinkuraVisualsIOS` と再選択する、0.8.1の3ファイルを
再コピーする、の順で試します。データコンテナは削除しません。

### 21.7 StikDebugがタイムアウトする

- LocalDevVPNを接続する
- Wi-Fiを使用する
- iPadを起こしてロック解除する
- StikDebugへペアリングファイルを再取り込みする
- OS更新後はペアリングファイルを作り直す
- StikDebug、LocalDevVPN、LiveContainerを完全終了して開き直す

### 21.8 JIT待機のまま進まない

- StikDebugの `Apps` → `JIT` でLiveContainerを選ぶ
- 表示された `Enable and Run Script` を押す
- `Geode.js` が選択済みか確認する
- DobbyとGeode.jsの組み合わせが現行LiveContainer対応か確認する

### 21.9 活動記録で背景が残る

背景の種類により対象キーが異なります。

- 一般背景命令: `HideBackground`
- 3D背景セット: `HideNonCharacter3D`
- グラデーション／ポスト効果: `HidePresetEffect`

同じ場面で1項目ずつ比較します。

### 21.10 活動記録の横画面で暗転する

次を確認します。

```json
"ActivityRecord.LandscapeRepair.Enable": true
```

完全終了してJITを取り直します。画面回転中に本編カメラが再生成されるため、
数秒待ってから操作パネルを確認します。

### 21.11 WMでカメラパネルが出ない

まず形式を確認します。

- IARC 3D: パネルが出る
- HLS/USM固定2D: 視点変更データがないので出ない

IARCのはずなのに出ない場合:

```json
"WithMeets.CameraControl.Enable": true,
"WithMeets.Archive.MotionCaptureReplay.Enable": true
```

カタログ外かつサーバー応答に有効な `.md` URLがない回は固定映像を維持します。

### 21.12 WMのシークが固定映像区間を越えない

キー名末尾の空白も含めて確認します。

```json
"WithMeets.Archive.IarcFullSeek.Enable": true
```

JSON変更後はアプリとLiveContainerを完全終了し、JITを取り直します。

### 21.13 WMでREPLAY・暗転・0秒復帰が出る

```json
"WithMeets.Archive.IarcFullSeek.Enable": true,
"WithMeets.Archive.IarcReplayOverlay.Suppress": true
```

0.8.1のdylib、JSON、offsetsが同じセットか確認します。古いdylibだけが残っていると、
JSONにキーがあっても機能しません。

### 21.14 WMで固定待機画面が残る

```json
"WithMeets.Archive.RenderImageCover.Suppress": true
```

これはWMアーカイブ再生スコープだけに適用されます。ホーム、WM一覧、活動記録、
Fesのカバーには適用しません。

### 21.15 WMの再生／一時停止ボタンがない

```json
"WithMeets.Archive.PlayPauseButton.Enable": true
```

0.8.1より前のdylibにはこのボタンがありません。dylibのSHA-256を確認します。

### 21.16 正規所持Fesチケットなのにカメラを選べない

1. 本当に対象アーカイブ用チケットを所持しているか確認します。
2. `FesArchive.ValidTicketRepair.Enable=true` を確認します。
3. `TicketRank` を実際の所持ランクへ合わせます。
4. `SelectableCameraTypes` を実際に許可されるカメラへ合わせます。
5. 完全終了してJITを取り直します。

未所持の権利を作る用途には使いません。

### 21.17 正規到達済みWM AFTERへ入れない

```json
"WithMeets.After.ValidAdmissionRepair.Enable": true
```

この修復は、一覧・詳細・アーカイブID・Extraチャプター・再生時間等の完全一致証拠が
ある場合だけ動作します。証拠が不足すると安全のため何も変更しません。
スター数、ポイント、閾値、購入状態は変更しません。

---

## 22. 緊急復旧

Tweak更新後にクラッシュする、一覧へ入るだけで落ちる、設定機能が全て消えた場合も、
最初にデータコンテナを削除しないでください。

### 22.1 基礎版へ戻す

1. LiveContainerを開きます。
2. HASU版リンクラを長押し→「設定」を開きます。
3. `調整フォルダ` を `None` にします。
4. `JITで起動` をオフにします。
5. JIT起動スクリプトを外します。
6. JITなしで起動します。

これで基礎版が起動すれば、IPAとデータコンテナは正常で、問題はJITまたは
調整フォルダ側です。

### 22.2 0.8.1を入れ直す

1. JSONをバックアップします。
2. 0.8.1 ZIPを再展開します。
3. `Install` の3ファイルを調整フォルダへ再コピーします。
4. iPadOS 26では対応するDobbyを確認します。この場合、調整フォルダ内に
   次の4ファイルがそろっていることを確認します。

   ```text
   LinkuraVisualsIOS.dylib
   LinkuraVisualsIOS.json
   IL2CPP_OFFSETS_5.0.1.json
   dobby.dylib
   ```

5. ファイルをオンにします。
6. 調整フォルダを再選択します。
7. JITオン、Geode.js選択、StikDebugで起動します。

### 22.3 それでも起動しない

1. 基礎版 `None` で起動できるか再確認します。
2. ペアリングファイルを更新します。
3. Dobby／Geode.js／LiveContainerの互換組み合わせを確認します。
4. JSONを同梱初期版へ一時的に戻します。
5. 追加設定は1項目ずつ戻します。

データコンテナの削除、アプリの新規データフォルダ作成、約16.6GBの再取得は
最後の手段です。

---

## 23. 確認済み環境と限界

実機確認例:

- iPad Pro M1/iPhone 17Pro A19Pro
- iPadOS 26.5.2/iOS 26.5.2
- LiveContainer＋SideStore
- StikDebug＋LocalDevVPN
- ネイティブ5.0.1／API表示5.1.0
- LinkuraVisualsIOS 0.8.1

確認された主な動作:

- HASU APIログイン、初回データ取得
- 0.6x／1.0x／1.4x、60 FPS等
- 活動記録の表示制御、自由カメラ、横画面
- 正規所持Fesチケットのカメラ誤判定修復
- 対応WMのIARC再生、自由カメラ、縦横画面、全長シーク
- 誤REPLAY／暗転／0秒復帰の抑止
- 開始前／AFTER固定待機カバーの抑止
- 正規到達済みWM AFTERの誤判定修復
- WM再生／一時停止ボタン
- カメラUIのスクリーンショット用非表示

全WMが3Dになるわけではありません。IARCデータがない固定映像は自由カメラ不可です。
また、端末、OS、LiveContainer、配信データの組み合わせごとに最終確認が必要です。

---

## 24. 最終チェックリスト

### 基礎導入

- [ ] Macで `python3 --version` が成功した
- [ ] 通常版パッチを作成した
- [ ] LiveContainer＋SideStoreを公式手順で導入した
- [ ] SideStoreで約7 DAYSに更新した
- [ ] 証明書をLiveContainerへ取り込んだ
- [ ] `調整フォルダ=None`、JITオフで起動した
- [ ] `Ver.5.1.0` を確認した
- [ ] 約16.6GBのデータ取得を完了した

### 拡張導入

- [ ] iPadOS 17.4以降である
- [ ] StikDebugへ有効なペアリングファイルを取り込んだ
- [ ] LocalDevVPNがConnected
- [ ] 0.8.1 ZIPの3ファイルを同じ調整フォルダへ入れた
- [ ] iPadOS/iOS 26では、信頼できるDobby／Geode.jsの入手元・版・SHA-256を記録した
- [ ] iPadOS/iOS 26ではDobbyを追加した
- [ ] iPadOS/iOS 26ではJIT起動スクリプトにGeode.jsを選んだ
- [ ] 調整フォルダに `LinkuraVisualsIOS` を選んだ
- [ ] JITで起動をオンにした
- [ ] 初回JIT起動前にFes／WM AFTER権利修復をいったん`false`へ変更した
- [ ] StikDebugで `Enable and Run Script` を実行した
- [ ] `0.6x / 1.0x / 1.4x` を確認した
- [ ] 正規所持権利に合わせてFesランクを確認した
- [ ] 活動記録・WM・Fesを1つずつ確認した

---

## 25. 関連資料

- [LiveContainer公式ドキュメント](https://livecontainer.github.io/docs/)
- [LiveContainer＋SideStore](https://livecontainer.github.io/docs/installation/lc_sidestore)
- [SideStore公式ドキュメント](https://docs.sidestore.io/)
- [StikDebug](https://github.com/StephenDev0/StikDebug)
- [linkura-localify](https://github.com/ChocoLZS/linkura-localify)
- [LLLLResUpiOS v0.0.17](https://github.com/DYY-Studio/LLLLResUpiOS/tree/v0.0.17)
- [IOS-Il2cppResolver](https://github.com/DYY-Studio/IOS-Il2cppResolver)

LinkuraVisualsIOSの詳細な実装範囲、設定値、ライセンスは、0.8.1配布ZIP内の
`README_JA.md`、`NOTICE.md`、`LICENSE-AGPL-3.0`、
`LICENSE-MIT-UPSTREAM` を確認してください。
