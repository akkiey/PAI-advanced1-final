# 日本語指示による簡易巡回ロボット

日本語の指示を scikit-learn で「巡回／停止」に分類し、ROS 2からGazeboのdemoRobotへ速度指令を送ります。AIは指示分類だけに使い、経路は固定です。APIキー不要。

## 動作環境

実測：Ubuntu 22.04.5 LTS / ROS 2 Humble / Ignition Gazebo Fortress 6.16.0 / Python 3.10 / scikit-learn 0.23.2 / NumPy 1.24.4 / SciPy 1.8.0。
Dockerイメージ：`airobotbook/ros2-desktop-ai-robot-book-humble:latest`。

## 構成

- `final_ai_patrol/ai_patrol.py`: 12例の文字TF-IDF + ロジスティック回帰。閾値0.65。4辺の定型巡回と終了・Ctrl+C時停止。
- `final_ai_patrol/evaluate.py`: 学習文と未学習文の分類評価。
- `final_ai_patrol/measure.py`: オドメトリ記録。
- `final_ai_patrol/record.sh`: X11画面の自動録画。環境変数で画面サイズ・切り取りを指定。
- `ros2_ws_src/`: 使用したサンプル由来のROSパッケージとモデル。
- `evidence/`: 実測ログ、分類結果、オドメトリ、集計結果。観測値であり再実行時の保証ではありません。

## ビルド（コンテナ内）

このディレクトリを例として `/workspace/submission` に置きます。既存のビルドやコンテナを削除しないでください。

```bash
source /opt/ros/humble/setup.bash
mkdir -p /workspace/submission_ws
cd /workspace/submission_ws
colcon build --base-paths /workspace/submission/ros2_ws_src --cmake-args -DBUILD_TESTING=OFF
source install/setup.bash
ros2 launch nav_dev nav_ai.launch.py
```

`nav_ai.launch.py` は元のlaunchから手動操作ノードを除き、`/clock` とオドメトリの一方向ブリッジを追加したものです。同じワールドやブリッジを二重起動しないでください。既存の `nav_teleop.launch.py` で試す場合は、キー操作ノードが常時送るゼロ速度との競合を避けてください。今回の実測は既存launchを保持し、操作ノードのみSIGSTOP、追加ブリッジで実行しました。

別ターミナルで：

```bash
source /opt/ros/humble/setup.bash
python3 /workspace/submission/final_ai_patrol/evaluate.py
python3 /workspace/submission/final_ai_patrol/ai_patrol.py '近くを巡回して'
python3 /workspace/submission/final_ai_patrol/ai_patrol.py '今すぐ止まってください'
```

巡回は前進0.15 m/s×4シミュレーション秒、左回転0.5 rad/s×πシミュレーション秒を4回行います。最大分類スコア0.65未満は保留し、ゼロ速度を送ります。停止指示もゼロ速度のみを送ります。分類スコアは校正された安全確率ではありません。

走行中の別の日本語入力を監視する機能はありません。中断はCtrl+Cです。/clockが止まると10秒で処理を中断し停止指令を送りますが、強制終了・ブリッジ故障・通信断まで停止を保証する仕組みではありません。障害物回避・位置フィードバックはありません。

## 実測結果

- W/A/S/Dをサンプルへ入力し前後進・左右回転を確認。
- 未学習「近くを巡回して」→巡回0.829875、8動作と自動停止を確認。
- 動作実時間約50.5秒、シミュレーション時刻約28.5秒。積算距離2.3865 m、出発位置との差0.02114 m、向きの差約-0.412度。
- 終了後約3.94シミュレーション秒の位置変化は数値誤差程度。終了速度・角速度は0。
- 未学習「今すぐ止まってください」→停止0.78505。8シミュレーション秒で移動距離0 m。
- 「周囲の巡回をお願いします」→0.504866で保留。無関係な「今日はいい天気ですね」→停止0.668112。少数の例文による一般化の限界がある。

これらは学習モデルの精度評価を代表するベンチマークではなく、選んだ少数例の観察です。各試行の入力と結果は `evidence/classification.json` にあります。

## サンプルからの変更・整理

日本語指示分類、スコア判定、定型巡回、時刻による制御、終了時停止を追加。録画・計測・評価スクリプトを追加。提出用には利用しない地図・他モデル・SLAM設定・lidar_nodeを省き、CMakeの対象を整理。個人情報保護のためpackage.xmlの連絡先を実在しないプレースホルダーへ置換。元のモデル・速度ブリッジ・手動操作のソースは保持。元環境のファイルは変更していません。

提出用ソースの3パッケージは独立したビルドディレクトリでビルド成功。元の実行環境で巡回・停止を実測済み。新しいnav_ai.launch.pyを使ってワールドを再起動する検証は、既存シミュレーション保持のため行っていません。

## 出典とライセンス

- 課題資料「最終課題（10_19 改訂版）」：コード公開用リポジトリには含めず、引き継ぎ資料として別添。
- Qiita N622「gazeboとROS2を連携してロボットを操作する」: https://qiita.com/N622/items/9d89f77d85d9da0af29e
- 元リポジトリ: https://github.com/OsawaKousei/2DRoboPrac_ws
- 参照commit: `123fd2e4ddfccf420499a02a3852c17a369f93bb`
- 元リポジトリのApache-2.0ライセンスは `LICENSE-upstream` に保存。ソース中の著作権表記は保持。
- 追加Python・シェルコードもApache-2.0で提供します。

元コード中のkey_eventパッケージのpackage.xmlにはライセンス未指定のTODOが残っています。配布元全体のApache-2.0 LICENSEに基づき同梱し、個別のライセンス表記は推測で変更していません。

## 動画

実際のX11録画のGazebo部分のみを切り出し、日本語説明を合成。映像は実時間の1倍速で、Dockerのシミュレーション進行は実時間より遅い状態でした。軌跡図は実測オドメトリを描画したもので、ロボット映像の代用ではありません。
