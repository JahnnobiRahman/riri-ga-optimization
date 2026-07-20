"""
distress_scorer.py (SECOND CORRECTION -- lookbehind-based)

ATTEMPT 1 (retracted): \\bkeyword\\b -- broke stem matching entirely
(suicid/hopeless stopped matching their intended variants).

ATTEMPT 2 (retracted): \\bkeyword (leading boundary only) -- fixed the
stem-matching regression, but the sanity check caught that it STILL
matched রক্ত inside বিরক্তিবোধ. Root cause: Python's re module's \\b
relies on its \\w definition, which does not reliably treat Bangla
combining vowel signs (matras) as word characters. In বিরক্তিবোধ, the
ি (i-matra) immediately before the embedded "র" is apparently
classified as a non-word character by re's Unicode handling, so \\b
sees a false boundary there even though the matra is linguistically
inseparable from its base letter.

ATTEMPT 3 (this version): explicit negative lookbehind against the
actual Bengali Unicode block (U+0980-U+09FF, which covers letters,
matras, virama, digits -- everything), rather than trusting regex's
\\w classification. This directly checks "is the character immediately
before this match ANY Bengali-script character or ASCII word
character" rather than relying on an unreliable built-in definition.

VERIFIED empirically via distress_scorer_impact_check.py (v3) before
being presented as fixed -- see that script's sanity-check output.
"""

import re
import pandas as pd

DISTRESS_KEYWORDS = {
    "suicid": 1.0,
    "kill myself": 0.95,
    "end my life": 0.95,
    "not live": 0.90,
    "can't live": 0.90,
    "don't want to live": 0.90,
    "dont want to live": 0.90,
    "আত্মহত্যা": 1.0,
    "মরে যেতে": 0.90,
    "আর বাঁচতে": 0.85,
    "মৃত্যু": 0.80,

    "self-harm": 0.90,
    "self harm": 0.90,
    "hurt myself": 0.85,
    "cutting": 0.80,
    "নিজেকে ক্ষতি": 0.90,
    "রক্ত": 0.75,

    "no future": 0.75,
    "hopeless": 0.75,
    "no reason to live": 0.80,
    "nothing matters": 0.75,
    "কোন ভবিষ্যত": 0.75,
    "ভবিষ্যত নেই": 0.75,

    "completely alone": 0.65,
    "nobody cares": 0.70,
    "isolated": 0.60,
    "একা": 0.60,
    "কেউ বোঝে না": 0.65,

    "cannot handle": 0.60,
    "falling apart": 0.65,
    "unbearable": 0.70,
    "সহ্য করতে পারছি না": 0.70,
}

# Negative lookbehind: match only if NOT immediately preceded by an
# ASCII word character OR any Bengali Unicode block character
# (U+0980-U+09FF covers the full Bengali script: consonants, vowels,
# matras, virama, digits, signs). No trailing constraint -- preserves
# intentional stem matches (suicid -> suicidal/suicide).
_BENGALI_BLOCK = "\u0980-\u09FF"
_COMPILED_PATTERNS = {
    keyword: re.compile(r"(?<![\w" + _BENGALI_BLOCK + r"])" + re.escape(keyword.lower()))
    for keyword in DISTRESS_KEYWORDS
}


def compute_distress_score(prompt_text: str) -> float:
    """
    Compute continuous distress score h(x_i) from prompt text.

    Uses a Bengali-Unicode-block-aware negative lookbehind (not
    regex's built-in \\b, which is unreliable for Bangla combining
    marks -- see module docstring) to block keywords from matching
    when embedded mid-word inside an unrelated longer word, while
    preserving intentional stem matches for morphological variants.

    Parameters
    ----------
    prompt_text : str
        User prompt in Bangla, Banglish, or English

    Returns
    -------
    float in [0, 1]
        Weighted sum of distress markers, capped at 1.0.
    """
    if pd.isna(prompt_text):
        return 0.0

    text = str(prompt_text).lower()
    score = 0.0
    matched_keywords = []

    for keyword, weight in DISTRESS_KEYWORDS.items():
        if _COMPILED_PATTERNS[keyword].search(text):
            score += weight
            matched_keywords.append(keyword)

    score = min(1.0, score)

    if len(matched_keywords) > 3:
        score = max(score - 0.05, 0.0)

    return float(score)