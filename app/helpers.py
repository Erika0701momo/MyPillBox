from flask_babel import lazy_gettext as _l

# お薬服用単位の翻訳辞書
unit_labels = {
    "tablet": _l("錠"),
    "capsule": _l("カプセル"),
    "packet": _l("包"),
    "mg": _l("mg"),
    "drop": _l("滴"),
    "ml": _l("ml"),
}


def format_taking_unit(unit, locale):
    """
    服用単位をフォーマットする。英語版では 'tablet(s)' や 'capsule(s)' を生成。
    日本語版ではそのまま。
    """

    if locale == "en":
        if unit in ["tablet", "capsule", "packet", "drop"]:
            return f"{unit}(s)"
        return unit  # デフォルトの表示
    return unit_labels.get(unit, unit)  # 日本語版
