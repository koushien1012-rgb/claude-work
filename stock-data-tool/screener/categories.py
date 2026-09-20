CATEGORY_LABELS = {
    "fx_weak": "円安・ドル高に強い",
    "fx_strong": "円高・ドル安に強い",
    "rate_up": "金利上昇に強い",
    "rate_down": "金利低下に強い",
    "cycle_expansion": "景気拡大に強い",
    "cycle_defensive": "景気後退に強い（ディフェンシブ）",
    "geopolitical": "有事・地政学リスクに強い",
    "oil_high": "原油高に強い",
}

CATEGORY_ORDER = [
    "fx_weak", "fx_strong",
    "rate_up", "rate_down",
    "cycle_expansion", "cycle_defensive",
    "geopolitical", "oil_high",
]

# Sector (as stored in our universe records) -> list of category ids it belongs to.
# JP sectors come from the Nikkei225 Wikipedia scrape; US sectors are our
# Japanese-translated GICS sector names. This is a heuristic financial-domain
# mapping, not an official classification -- adjust freely as needed.
SECTOR_CATEGORIES = {
    # --- Japan (Nikkei225 industry groups) ---
    "食品": ["cycle_defensive"],
    "繊維": ["fx_weak"],
    "パルプ・紙": ["cycle_expansion"],
    "化学": ["cycle_expansion", "oil_high"],
    "医薬品": ["cycle_defensive"],
    "石油": ["oil_high", "geopolitical"],
    "ゴム": ["fx_weak", "cycle_expansion"],
    "窯業": ["cycle_expansion"],
    "鉄鋼": ["cycle_expansion", "geopolitical"],
    "非鉄・金属": ["fx_weak", "geopolitical", "cycle_expansion"],
    "機械": ["fx_weak", "cycle_expansion"],
    "電気機器": ["fx_weak", "cycle_expansion", "rate_down"],
    "造船": ["fx_weak", "geopolitical"],
    "自動車": ["fx_weak", "cycle_expansion"],
    "精密機器": ["fx_weak", "cycle_expansion"],
    "その他製造": ["fx_weak"],
    "水産": ["cycle_defensive"],
    "鉱業": ["geopolitical", "oil_high"],
    "建設": ["rate_down", "cycle_expansion"],
    "商社": ["fx_weak", "geopolitical", "oil_high"],
    "小売業": ["fx_strong", "cycle_defensive"],
    "銀行": ["rate_up"],
    "証券": ["rate_up", "cycle_expansion"],
    "保険": ["rate_up"],
    "その他金融": ["rate_up"],
    "不動産": ["rate_down"],
    "鉄道・バス": ["cycle_defensive"],
    "陸運": ["cycle_defensive", "oil_high"],
    "海運": ["cycle_expansion", "geopolitical"],
    "空運": ["fx_strong", "oil_high"],
    "通信": ["cycle_defensive", "rate_down"],
    "電力": ["cycle_defensive", "rate_down"],
    "ガス": ["cycle_defensive"],
    "サービス": ["cycle_expansion"],

    # --- US (translated GICS sectors) ---
    # fx_weak here means USD strength (domestically-focused, insulated from a
    # strong dollar hurting overseas earnings); fx_strong means USD weakness
    # (multinational exporters whose overseas revenue translates to more USD).
    "情報技術": ["rate_down", "cycle_expansion", "fx_strong"],
    "ヘルスケア": ["cycle_defensive", "fx_weak"],
    "金融": ["rate_up", "fx_weak"],
    "一般消費財": ["cycle_expansion", "rate_down"],
    "通信サービス": ["cycle_defensive", "fx_weak"],
    "資本財": ["cycle_expansion", "fx_strong"],
    "生活必需品": ["cycle_defensive", "fx_weak"],
    "エネルギー": ["oil_high", "geopolitical"],
    "公益事業": ["cycle_defensive", "rate_down", "fx_weak"],
    "素材": ["cycle_expansion", "geopolitical", "fx_strong"],
}


def categories_for_sector(sector: str | None) -> list[str]:
    if not sector:
        return []
    return SECTOR_CATEGORIES.get(sector, [])
