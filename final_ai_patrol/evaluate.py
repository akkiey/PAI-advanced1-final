"""Training-independent phrasing checks. Scores are not calibrated safety probabilities."""
import json
from ai_patrol import classify, examples
cases = [
 ('近くを巡回してください','patrol',True),('停止してください','stop',True),
 ('近くを巡回して','patrol',False),('周囲の巡回をお願いします','patrol',False),
 ('パトロールしてください','patrol',False),('今すぐ止まってください','stop',False),
 ('動かず待機して','stop',False),('巡回しないでください','stop',False),
 ('巡回を開始しないで','stop',False),('今日はいい天気ですね','unknown',False),
 ('こんにちは','unknown',False)]
results=[]
for text, expected, training in cases:
 label,score=classify(text)
 action=label if score>=.65 else 'uncertain'
 results.append(dict(instruction=text,expected=expected,in_training=training,label=label,score=round(score,6),action=action))
print(json.dumps(results,ensure_ascii=False,indent=2))
