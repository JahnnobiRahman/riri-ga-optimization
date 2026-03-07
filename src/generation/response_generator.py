import re
import random
import pandas as pd

from ga.genome import Genome

# ======================
# 4) Prompt templates + block banks
# ======================
BASE_TEMPLATES = {
    0: "You are Riri, a Bangla/Banglish mental health support assistant. Be safe and supportive.",
    1: "You are a culturally aware assistant for Bangladeshi youth. Use warm Banglish, non-judgmental tone.",
    2: "You are a calm, therapist-like assistant. Be structured, gentle, and practical."
}

# Different variants to increase output diversity (so GA has something to optimize)
EMPATHY_LINES = {
    "low": [
        "বুঝলাম।",
        "I understand.",
    ],
    "mid": [
        "শুনে খারাপ লাগছে। I hear you.",
        "That sounds hard. আমি বুঝতে পারছি।",
        "It makes sense you’re feeling this way.",
    ],
    "high": [
        "আমি বুঝতে পারছি—এটা সত্যিই কষ্টের। You’re not alone in this.",
        "তোমার অনুভূতিটা valid. It makes sense, and you deserve support.",
        "This sounds overwhelming—আমি সত্যিই তোমার কষ্টটা বুঝতে পারছি।",
        "তুমি অনেক কিছু carry করছো মনে হচ্ছে—ধীরে ধীরে একসাথে দেখি।",
    ]
}

STRUCTURE_PACK = {
    "low": {
        "grounding": [],
        "action": [],
        "question": ["আর একটু বিস্তারিত বলবে?", "What’s been going on lately?"]
    },
    "mid": {
        "grounding": ["একটু গভীর শ্বাস নাও—slow breath, in…out…", "Let’s take one slow breath together."],
        "action": ["আজকে ছোট করে ১টা কাজ: পানি খাও বা ৫ মিনিট হাঁটো।", "Try one small step: drink water / short walk / message someone."],
        "question": ["এই অনুভূতিটা কখন বেশি বাড়ে?", "When does it feel worst?"]
    },
    "high": {
        "grounding": [
            "চলো ৩০ সেকেন্ড grounding করি—একটু গভীর শ্বাস নাও, তারপর ৫টা জিনিস দেখো।",
            "Let’s do 5-4-3-2-1 grounding: 5 things you see, 4 you feel…"
        ],
        "action": [
            "আজকে একটা tiny step: কাউকে মেসেজ দাও (trusted friend/family).",
            "Write down the strongest thought in one line, then rate intensity 0–10."
        ],
        "question": [
            "তুমি এখন সবচেয়ে বেশি কোন চিন্তাটায় আটকে আছো?",
            "What thought is looping the most right now?"
        ]
    }
}

SAFETY_LINES = {
    "low": [
        "Be careful and avoid harmful advice.",
    ],
    "mid": [
        "Avoid validating harmful actions. Encourage seeking support if risk signs appear.",
    ],
    "high": [
        "If self-harm/suicide risk is suspected: do NOT validate intent. Encourage immediate help and escalation to a human professional."
    ]
}

ESCALATION_LINES = [
    "If you feel unsafe right now, please reach out to a trusted person immediately and consider contacting a mental health professional.",
    "If there’s any risk of harm, immediate help matters—talk to someone you trust or contact local emergency/helpline support.",
    "তুমি যদি এখন unsafe feel করো, দয়া করে এখনই বিশ্বাসযোগ্য কাউকে জানাও এবং প্রফেশনাল সাহায্য নাও।"
]



# ======================
# 6) Response generator (WEIGHT-SENSITIVE)
#    THIS is what fixes your flat plot.
# ======================
def generate_response(user_text: str, risk_label: str, g: Genome) -> str:
    safety_level = weight_to_level(g.w_s)
    empathy_level = weight_to_level(g.w_e)
    structure_level = weight_to_level(g.w_c)

    # Risk score proxy
    risk_score = {"low": 0.2, "mid": 0.6, "high": 0.9}[risk_label]

    # Escalate logic depends on thresholds + safety strictness
    escalate = False
    if risk_score >= g.theta_high:
        escalate = True
    elif risk_score >= g.theta_mid and safety_level in ("mid", "high"):
        escalate = True

    # --- Weight-sensitive number of lines ---
    # Higher empathy weight -> more empathy lines
    empathy_lines_count = 1
    if g.w_e >= 0.66: empathy_lines_count = 2
    if g.w_e >= 0.85: empathy_lines_count = 3

    # Higher structure -> more structured steps
    use_grounding = (g.w_c >= 0.40)
    use_action = (g.w_c >= 0.55)
    use_question = (g.w_c >= 0.25)

    # Higher safety -> stronger escalation phrasing + higher chance of adding extra safety reminder
    add_extra_safety = (g.w_s >= 0.75)

    parts = []
    parts.append(f"[TEMPLATE] {BASE_TEMPLATES[g.p_id]}")
    parts.append(f"[SAFETY] {random.choice(SAFETY_LINES[safety_level])}")

    # Empathy lines
    emp_bank = EMPATHY_LINES[empathy_level]
    for _ in range(empathy_lines_count):
        parts.append(random.choice(emp_bank))

    # Escalation
    if escalate and safety_level in ("mid", "high"):
        parts.append(random.choice(ESCALATION_LINES))
        if add_extra_safety:
            parts.append("If you are in immediate danger, seek urgent local help right now.")

    # Structured components
    pack = STRUCTURE_PACK[structure_level]
    if use_grounding and pack["grounding"]:
        parts.append(random.choice(pack["grounding"]))
    if use_action and pack["action"]:
        parts.append(random.choice(pack["action"]))
    if use_question and pack["question"]:
        parts.append(random.choice(pack["question"]))

    # Memory window proxy: smaller memory => shorter response (cuts tail)
    if g.memory_window <= 256 and len(parts) > 4:
        parts = parts[:4]

    return "\n".join(parts)


def weight_to_level(w: float) -> str:
    if w < 0.33: return "low"
    if w < 0.66: return "mid"
    return "high"


