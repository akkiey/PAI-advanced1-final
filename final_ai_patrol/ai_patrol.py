import sys
import time
import math

import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from rosgraph_msgs.msg import Clock

from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


# 日本語の指示と正解ラベルの例
examples = [
    ("近くを巡回してください", "patrol"),
    ("短いコースを一周して", "patrol"),
    ("小さな四角を走って", "patrol"),
    ("周囲を見回って", "patrol"),
    ("パトロールを始めて", "patrol"),
    ("周囲を点検して", "patrol"),
    ("停止してください", "stop"),
    ("その場で待って", "stop"),
    ("動かないで", "stop"),
    ("ストップ", "stop"),
    ("止まって", "stop"),
    ("巡回をやめて", "stop"),
]

# 文字の特徴から文章を分類するモデルを学習
model = make_pipeline(
    TfidfVectorizer(analyzer="char", ngram_range=(1, 3)),
    LogisticRegression(C=10, max_iter=1000, random_state=0),
)

model.fit(
    [text for text, label in examples],
    [label for text, label in examples],
)

def classify(instruction):
    scores = model.predict_proba([instruction])[0]
    best = int(scores.argmax())
    return str(model.classes_[best]), float(scores[best])


def main():
    instruction = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "近くを巡回してください"
    )
    
    label, score = classify(instruction)
    
    print(f"入力: {instruction}", flush=True)
    print(
        f"AI判定: {label} / 分類スコア: {score:.3f}",
        flush=True,
    )
    
    # 低スコアもゼロ速度を送ってから終了する。
    if score < 0.65:
        print("判定保留：走行せず停止指令を送ります。", flush=True)
        label = "uncertain"
    
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    
    node = rclpy.create_node("ai_patrol")
    publisher = node.create_publisher(Twist, "/cmd_vel", 10)
    
    state = {
        "sim": None,
        "received": time.monotonic(),
    }
    
    
    def on_clock(msg):
        state["sim"] = (
            msg.clock.sec + msg.clock.nanosec * 1e-9
        )
        state["received"] = time.monotonic()
    
    
    clock_sub = node.create_subscription(
        Clock,
        "/clock",
        on_clock,
        qos_profile_sensor_data,
    )
    
    
    def send(v=0.0, w=0.0):
        msg = Twist()
        msg.linear.x = float(v)
        msg.angular.z = float(w)
        publisher.publish(msg)
    
    
    try:
        # 通信とシミュレーション時刻を待つ
        deadline = time.monotonic() + 30
    
        while (
            state["sim"] is None
            or publisher.get_subscription_count() == 0
        ):
            rclpy.spin_once(node, timeout_sec=0.1)
    
            if time.monotonic() > deadline:
                raise RuntimeError(
                    "Gazeboの実行状態とブリッジを確認してください。"
                )
    
        if label == "patrol":
            # 前進：0.15m/sで4秒
            # 左回転：0.5rad/sで約90度
            # この組み合わせを4回繰り返す
            plan = [
                (0.15, 0.0, 4.0),
                (0.0, 0.5, math.pi),
            ] * 4
        else:
            plan = [(0.0, 0.0, 1.0)]
    
        for number, (v, w, duration) in enumerate(
            plan, start=1
        ):
            print(
                f"動作 {number}/{len(plan)}",
                flush=True,
            )
    
            started = state["sim"]
    
            while state["sim"] - started < duration:
                rclpy.spin_once(node, timeout_sec=0.05)
    
                if (
                    time.monotonic() - state["received"]
                    > 10
                ):
                    raise RuntimeError(
                        "時刻の受信が止まったため終了します。"
                    )
    
                if state["sim"] < started:
                    raise RuntimeError(
                        "シミュレーション時刻がリセットされました。"
                    )
    
                send(v, w)
    
            send()
    
        print("完了：停止しました。", flush=True)
    
    except KeyboardInterrupt:
        print("中断：停止します。", flush=True)
    
    finally:
        # 終了時に停止指令を繰り返して送信
        for _ in range(10):
            send()
            time.sleep(0.05)
    
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
