import random
from typing import Any, Dict, List, Optional

from ga.genome import Genome


BASE_TEMPLATES = {
    0: "You are Riri, a Bangla/Banglish mental health support assistant. Be safe and supportive.",
    1: "You are a culturally aware assistant for Bangladeshi youth. Use warm Banglish, non-judgmental tone.",
    2: "You are a calm, therapist-like assistant. Be structured, gentle, and practical.",
}


EMPATHY_LINES = {
    "low": [
        "বুঝলাম।",
        "I understand.",
    ],
    "mid": [
        "শুনে খারাপ লাগছে। I hear you.",
        "That sounds hard. আমি বুঝতে পারছি।",
        "It makes sense you’re feeling this way.",
        "It sounds like this has been weighing on you for a while.",
        "তোমার অনুভূতিটা valid, এবং এমন অনুভব করা অস্বাভাবিক না।",
    ],
    "high": [
        "আমি বুঝতে পারছি—এটা সত্যিই কষ্টের। You’re not alone in this.",
        "তোমার অনুভূতিটা valid. It makes sense, and you deserve support.",
        "This sounds overwhelming—আমি সত্যিই তোমার কষ্টটা বুঝতে পারছি।",
        "তুমি অনেক কিছু carry করছো মনে হচ্ছে—ধীরে ধীরে একসাথে দেখি।",
        "It makes sense that you feel exhausted after carrying this for so long.",
        "তুমি একা না—এমন অবস্থায় support চাওয়া একদম okay.",
    ],
}


REFLECTION_TEMPLATES = [
    "It makes sense that you feel this way.",
    "I can see why this would feel overwhelming.",
    "That sounds really difficult to go through.",
    "I hear you — this isn’t easy.",
    "শুনে মনে হচ্ছে এটা তোমার জন্য অনেক heavy লাগছে।",
    "তোমার অনুভূতিটা একদম valid — এমন লাগা স্বাভাবিক।",
    "মনে হচ্ছে অনেকদিন ধরে এটা তোমার উপর চাপ হয়ে আছে।",
    "তুমি একা না — এই feeling টা অনেকেই experience করে।",
    "It makes sense — তোমার জায়গায় থাকলে এমন লাগাই স্বাভাবিক।",
    "I hear you — এটা সত্যিই tough লাগতে পারে।",
    "It sounds like this has been emotionally heavy — তুমি একা না।",
]


STRUCTURE_PACK = {
    "low": {
        "grounding": [],
        "action": [],
        "question": [
            "আর একটু বিস্তারিত বলবে?",
            "What’s been going on lately?",
        ],
    },
    "mid": {
        "grounding": [
            "একটু গভীর শ্বাস নাও—slow breath, in…out…",
            "Let’s take one slow breath together.",
        ],
        "action": [
            "আজকে ছোট করে ১টা কাজ: পানি খাও বা ৫ মিনিট হাঁটো।",
            "Try one small step: drink water / short walk / message someone.",
        ],
        "question": [
            "এই অনুভূতিটা কখন বেশি বাড়ে?",
            "When does it feel worst?",
        ],
    },
    "high": {
        "grounding": [
            "চলো ৩০ সেকেন্ড grounding করি—একটু গভীর শ্বাস নাও, তারপর ৫টা জিনিস দেখো।",
            "Let’s do 5-4-3-2-1 grounding: 5 things you see, 4 you feel…",
        ],
        "action": [
            "আজকে একটা tiny step: কাউকে মেসেজ দাও (trusted friend/family).",
            "Write down the strongest thought in one line, then rate intensity 0–10.",
        ],
        "question": [
            "তুমি এখন সবচেয়ে বেশি কোন চিন্তাটায় আটকে আছো?",
            "What thought is looping the most right now?",
        ],
    },
}


SAFETY_LINES = {
    "low": [
        "Be careful and avoid harmful advice.",
    ],
    "mid": [
        "Avoid validating harmful actions. Encourage seeking support if risk signs appear.",
    ],
    "high": [
        "If self-harm/suicide risk is suspected: do NOT validate intent. Encourage immediate help and escalation to a human professional.",
    ],
}


ESCALATION_LINES = [
    "If you feel unsafe right now, please reach out to a trusted person immediately and consider contacting a mental health professional.",
    "If there’s any risk of harm, immediate help matters—talk to someone you trust or contact local emergency/helpline support.",
    "তুমি যদি এখন unsafe feel করো, দয়া করে এখনই বিশ্বাসযোগ্য কাউকে জানাও এবং প্রফেশনাল সাহায্য নাও।",
]


def weight_to_level(w: float) -> str:
    if w < 0.33:
        return "low"
    if w < 0.66:
        return "mid"
    return "high"


def generate_response(user_text: str, risk_label: str, g: Genome) -> str:
    trace = assemble_prompt_trace(user_text, risk_label, g)
    return trace["final_response"]


def assemble_prompt_trace(
    user_text: str,
    risk_label: str,
    g: Genome,
    rng: Optional[random.Random] = None,
) -> Dict[str, Any]:

    rnd = rng if rng is not None else random

    safety_level = weight_to_level(g.w_s)
    empathy_level = weight_to_level(g.w_e)
    structure_level = weight_to_level(g.w_c)

    risk_score = {"low": 0.2, "mid": 0.6, "high": 0.9}[risk_label]

    escalate = False
    if risk_score >= g.theta_high:
        escalate = True
    elif risk_score >= g.theta_mid and safety_level in ("mid", "high"):
        escalate = True

    empathy_lines_count = 1
    if g.w_e >= 0.20:
        empathy_lines_count = 2
    if g.w_e >= 0.35:
        empathy_lines_count = 3

    use_grounding = g.w_c >= 0.40
    use_action = g.w_c >= 0.40
    use_question = g.w_c >= 0.25

    add_extra_safety = g.w_s >= 0.75

    chosen_template = BASE_TEMPLATES[g.p_id]
    chosen_safety_line = rnd.choice(SAFETY_LINES[safety_level])

    parts: List[str] = []
    parts.append(f"[TEMPLATE] {chosen_template}")
    parts.append(f"[SAFETY] {chosen_safety_line}")

    emp_bank = EMPATHY_LINES[empathy_level]
    chosen_empathy_lines: List[str] = []

    for _ in range(empathy_lines_count):
        line = rnd.choice(emp_bank)
        chosen_empathy_lines.append(line)
        parts.append(line)

    if g.w_e >= 0.08:
        reflection_line = rnd.choice(REFLECTION_TEMPLATES)
        chosen_empathy_lines.append(reflection_line)
        parts.append(reflection_line)

    chosen_escalation_lines: List[str] = []

    if escalate and safety_level in ("mid", "high"):
        esc_line = rnd.choice(ESCALATION_LINES)
        chosen_escalation_lines.append(esc_line)
        parts.append(esc_line)

        if add_extra_safety:
            extra = "If you are in immediate danger, seek urgent local help right now."
            chosen_escalation_lines.append(extra)
            parts.append(extra)

    pack = STRUCTURE_PACK[structure_level]
    chosen_grounding = None
    chosen_action = None
    chosen_question = None

    if risk_label == "high":
        grounding_prob = 0.85
        action_prob = 0.60
        question_prob = 0.40

    elif risk_label == "mid":
        grounding_prob = 0.75
        action_prob = 0.65
        question_prob = 0.55

    else:
        grounding_prob = 0.50
        action_prob = 0.65
        question_prob = 0.75

    if use_grounding and pack["grounding"] and rnd.random() < grounding_prob:
        chosen_grounding = rnd.choice(pack["grounding"])
        parts.append(chosen_grounding)

    if use_action and pack["action"] and rnd.random() < action_prob:
        chosen_action = rnd.choice(pack["action"])
        parts.append(chosen_action)

    if use_question and pack["question"] and rnd.random() < question_prob:
        chosen_question = rnd.choice(pack["question"])
        parts.append(chosen_question)

    generated_parts = list(parts)

    truncated = g.memory_window <= 256 and len(parts) > 4
    if truncated:
        parts = parts[:4]

    visible_response = list(parts)
    final_text = "\n".join(visible_response)

    return {
        "user_text": user_text,
        "risk_label": risk_label,
        "template": chosen_template,
        "safety_level": safety_level,
        "empathy_level": empathy_level,
        "structure_level": structure_level,
        "escalate": escalate,
        "safety": chosen_safety_line,
        "empathy": chosen_empathy_lines,
        "escalation": chosen_escalation_lines,
        "grounding": chosen_grounding,
        "action": chosen_action,
        "question": chosen_question,
        "num_empathy_lines": len(chosen_empathy_lines),
        "generated_parts": generated_parts,
        "visible_response": visible_response,
        "truncated": truncated,
        "final_response": final_text,
    }