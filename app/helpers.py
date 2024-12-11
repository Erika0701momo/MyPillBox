from flask_babel import lazy_gettext as _l

# お薬服用単位の翻訳辞書
unit_labels = {
    "tablet": _l("錠"),
    "capsule": _l("カプセル"),
    "package": _l("包"),
    "mg": _l("mg"),
    "drop": _l("滴"),
    "ml": _l("ml"),
}
