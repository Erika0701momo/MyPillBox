from flask_babel import lazy_gettext as _l
from flask import g

# お薬服用単位の翻訳辞書
unit_labels = {
    "tablet": _l("錠"),
    "capsule": _l("カプセル"),
    "packet": _l("包"),
    "mg": _l("mg"),
    "drop": _l("滴"),
    "ml": _l("ml"),
}


def format_unit(taking_unit, locale):
    """
    服用単位をフォーマットする。英語版では 'tablet(s)' や 'capsule(s)' を生成。
    日本語版ではそのまま。
    """

    if locale.startswith("en"):
        if taking_unit in ["tablet", "capsule", "packet", "drop"]:
            return f"{taking_unit}(s)"
        return taking_unit  # デフォルトの表示
    return unit_labels.get(taking_unit, taking_unit)  # 日本語版


def format_dose_unit(dose, taking_unit):
    """
    服用単位を服用量に応じてフォーマット。英語版では'tablets'や'capsules'を生成。
    日本語版ではそのまま。
    """

    locale = g.locale
    if locale.startswith("en"):
        if dose and dose > 1:
            if taking_unit in ["tablet", "capsule", "packet", "drop"]:
                return f"{taking_unit}s"
            else:
                return taking_unit
        else:
            return taking_unit
    # 日本語版
    return unit_labels.get(taking_unit, taking_unit)
