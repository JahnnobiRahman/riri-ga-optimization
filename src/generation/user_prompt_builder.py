import random
from typing import Optional


def normalize_risk(risk_label: Optional[str]) -> str:
    if risk_label in {"low", "mid", "high"}:
        return risk_label
    return "low"


def build_realistic_user_prompt(
    raw_text: str,
    risk_label: Optional[str] = None,
    seed: int | None = None,
) -> str:
    """
    Converts dataset/context labels into a realistic Bangla/Banglish/English user message.

    Important:
    - If risk_label == "high", we force at least one high-risk sentence.
    - This prevents mismatch where the prompt sounds mild but the response escalates.
    """

    rng = random.Random(seed)
    text = str(raw_text).lower()
    risk_label = normalize_risk(risk_label)

    lines = []

    # ======================
    # High-risk alignment
    # ======================

    high_risk_keywords = [
        "suicide",
        "suicidal",
        "self-harm",
        "self harm",
        "not live",
        "cannot live",
        "don't want to live",
        "dont want to live",
        "no desire to live",
        "no future",
        "end",
        "death",
        "razor",
        "cut",
        "harm myself",
        "bachte ichcha kore na",
        "আর বাঁচতে",
        "বাঁচতে চাই না",
        "মরতে",
    ]

    has_high_risk_signal = any(k in text for k in high_risk_keywords)

    if risk_label == "high" or has_high_risk_signal:
        lines.append(rng.choice([
            "Sometimes I feel like I don’t want to live anymore.",
            "Majhe majhe mone hoy bachte ichcha kore na.",
            "মনে হয় আর বাঁচতে চাই না।",
            "I feel scared of what I might do if this gets worse.",
            "সবকিছু এত heavy লাগছে যে আর নিতে পারছি না।",
        ]))

    # ======================
    # Core emotional themes
    # ======================

    if "loneliness" in text or "lonely" in text:
        lines.append(rng.choice([
            "I feel really alone these days.",
            "Ami onek lonely feel kortesi lately.",
            "মনে হচ্ছে আমি একা হয়ে গেছি।",
        ]))

    if "hopeless" in text or "no future" in text:
        lines.append(rng.choice([
            "I feel like there’s no future for me.",
            "Ami mone kori amar kono future nai.",
            "মনে হচ্ছে সামনে কিছুই নেই।",
        ]))

    if "depression" in text or "nothing feels good" in text:
        lines.append(rng.choice([
            "Nothing really feels good anymore.",
            "Ami kono kichu te interest pachchi na.",
            "কিছুতেই ভালো লাগছে না।",
        ]))

    if "anxiety" in text or "stress" in text or "pressure" in text:
        lines.append(rng.choice([
            "I feel really anxious and overwhelmed.",
            "Ami onek pressure feel kortesi.",
            "মনে হচ্ছে মাথা কাজ করছে না।",
        ]))

    if "frustration" in text or "anger" in text:
        lines.append(rng.choice([
            "I feel frustrated and angry a lot.",
            "Ami easily rag hoye jai ajkal.",
            "খুব রাগ লাগে সবকিছুর উপর।",
        ]))

    # ======================
    # Relationship issues
    # ======================

    if "partner" in text or "relationship" in text:
        lines.append(rng.choice([
            "My relationship situation is really confusing and painful.",
            "Amar relationship niye onek confusion.",
            "সম্পর্কটা এখন অনেক কষ্ট দিচ্ছে।",
        ]))

    if "divorce" in text:
        lines.append(rng.choice([
            "After everything that happened, I feel completely broken.",
            "Divorce er por amar life ta ulta hoye geche.",
            "বিচ্ছেদের পর সবকিছু ভেঙে গেছে মনে হচ্ছে।",
        ]))

    if "infidelity" in text or "cheating" in text or "cheat" in text:
        lines.append(rng.choice([
            "I feel betrayed and can’t trust anything anymore.",
            "Amake cheat korar por ami mentally khub kharap hoye gechi.",
            "বিশ্বাসটা পুরোপুরি ভেঙে গেছে।",
        ]))

    if "abuse" in text or "insult" in text or "threat" in text:
        lines.append(rng.choice([
            "I feel mentally drained from how I’m being treated.",
            "Amake onek disrespect kora hocche.",
            "মানসিকভাবে খুব খারাপ লাগছে।",
        ]))

    # ======================
    # Family + life stress
    # ======================

    if "father" in text or "family" in text:
        lines.append(rng.choice([
            "Family situation is really affecting me.",
            "Family niye onek stress e achi.",
            "পরিবারের বিষয়গুলো খুব কষ্ট দিচ্ছে।",
        ]))

    if "academic" in text or "failure" in text or "study" in text:
        lines.append(rng.choice([
            "I feel like I’m failing in life.",
            "Porashona niye ami khub pressure e achi.",
            "নিজেকে ব্যর্থ মনে হচ্ছে।",
        ]))

    if "financial" in text or "money" in text:
        lines.append(rng.choice([
            "Financial stress is making everything worse.",
            "Taka niye onek stress hocche.",
            "টাকার চিন্তায় খুব খারাপ লাগছে।",
        ]))

    # ======================
    # Self-worth + identity
    # ======================

    if "worthless" in text or "loser" in text:
        lines.append(rng.choice([
            "I feel like I’m a failure.",
            "Ami nijeke loser mone kori.",
            "নিজেকে খুব মূল্যহীন লাগে।",
        ]))

    if "crazy" in text or "pagol" in text:
        lines.append(rng.choice([
            "I feel like I’m losing control of myself.",
            "Ami mone kori ami pagol hoye jacchi.",
            "মনে হচ্ছে নিজের উপর control নেই।",
        ]))

    # ======================
    # Self-harm / death details
    # ======================

    if "self-harm" in text or "self harm" in text or "cut" in text or "razor" in text:
        lines.append(rng.choice([
            "I have thoughts of hurting myself sometimes.",
            "Majhe majhe nijeke harm korte ichcha kore.",
            "নিজেকে আঘাত করার চিন্তা আসে।",
        ]))

    if "death" in text or "like death" in text:
        lines.append(rng.choice([
            "Everything feels unbearable right now.",
            "Mone hocche sob kichu shesh hoye jacche.",
            "সবকিছু অসহ্য লাগছে।",
        ]))

    # ======================
    # Sexual / impulse issues
    # ======================

    if "sexual" in text or "inappropriate" in text:
        lines.append(rng.choice([
            "Sometimes I say or think things that I later regret.",
            "Ami majhe majhe inappropriate kotha boli.",
            "কিছু আচরণ পরে নিজেকেই খারাপ লাগে।",
        ]))

    # ======================
    # PHQ / mental check
    # ======================

    if "phq" in text or "test" in text:
        lines.append(rng.choice([
            "I took a mental health test and it made me worried.",
            "Ami ekta test disi, result dekhe kharap lagche.",
            "একটা টেস্ট দেওয়ার পর বুঝলাম অবস্থা ভালো না।",
        ]))

    # ======================
    # Risk-aware fallback
    # ======================

    if not lines:
        if risk_label == "high":
            lines.append(rng.choice([
                "I’m feeling really unsafe with my thoughts right now.",
                "I feel like I might not be able to handle this alone.",
                "মনে হচ্ছে আমি নিজের সাথে safe feel করছি না।",
            ]))
        elif risk_label == "mid":
            lines.append(rng.choice([
                "I’m not feeling okay and I need someone to talk to.",
                "Ami bhalo feel kortesi na, support dorkar.",
                "মনে হচ্ছে আমি emotionally খুব overwhelmed.",
            ]))
        else:
            lines.append(rng.choice([
                "I’m not feeling okay and I don’t know how to explain it.",
                "Ami bhalo feel kortesi na.",
                "মনে হচ্ছে কিছু একটা ঠিক নেই।",
            ]))

    # ======================
    # Length control
    # ======================

    max_lines = 5 if risk_label == "high" else 4
    lines = lines[:max_lines]

    # ======================
    # Natural closing
    # ======================

    if risk_label == "high":
        closing = rng.choice([
            "I don’t know what to do and I feel scared.",
            "Can you help me stay safe right now?",
            "I feel like I need help immediately.",
            "",
        ])
    elif risk_label == "mid":
        closing = rng.choice([
            "I don’t know what to do.",
            "Can you help me?",
            "What should I do now?",
            "I just needed to tell someone.",
            "",
        ])
    else:
        closing = rng.choice([
            "Can you help me understand this?",
            "What should I do now?",
            "I just wanted to talk about it.",
            "",
        ])

    if closing:
        lines.append(closing)

    return " ".join(lines)