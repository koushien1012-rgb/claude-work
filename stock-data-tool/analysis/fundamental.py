import json

import anthropic

from stock_data.common import get_api_key, get_env

_DEFAULT_MODEL = "claude-sonnet-5"

_SYSTEM_PROMPT = """あなたは株式市場のファンダメンタルズ分析アシスタントです。
与えられたニュース記事・適時開示情報を読み、それぞれの株価への影響度を判定してください。
出力は必ず以下のJSON形式のみとし、説明文やコードブロックの前置きは一切含めないでください。

{
  "items": [
    {"title": "...", "sentiment": -1.0から1.0の数値, "reasoning": "一文の根拠"}
  ],
  "overall_sentiment": -1.0から1.0の数値,
  "summary": "1〜2文の日本語での総括"
}

sentimentの目安: 1.0 = 非常に強気材料, 0 = 中立/無関係, -1.0 = 非常に弱気材料
"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def analyze_news(ticker: str, news_items: list[dict], model: str | None = None) -> dict:
    if not news_items:
        return {"items": [], "overall_sentiment": 0.0, "summary": "分析対象のニュース・開示情報がありません。"}

    client = anthropic.Anthropic(api_key=get_api_key("ANTHROPIC_API_KEY"))

    formatted = "\n\n".join(
        f"[{i + 1}] {item.get('title', '')}\n"
        f"{item.get('summary', '')}\n"
        f"(公開日: {item.get('published_at', '')})"
        for i, item in enumerate(news_items)
    )
    user_prompt = f"銘柄: {ticker}\n\n以下のニュース・開示情報を分析してください。\n\n{formatted}"

    response = client.messages.create(
        model=model or get_env("CLAUDE_MODEL", _DEFAULT_MODEL),
        max_tokens=2048,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return _extract_json(response.content[0].text)
