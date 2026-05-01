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
        "আমি শুনছি।",
    ],
    "mid": [
        "That sounds hard. আমি বুঝতে পারছি।",
        "It makes sense — এমন লাগা স্বাভাবিক।",
        "শুনে মনে হচ্ছে এটা তোমার জন্য heavy লাগছে।",
        "I hear you — এটা সহজ না।",
        "তোমার অনুভূতিটা valid.",
    ],
    "high": [
        "আমি বুঝতে পারছি—এটা সত্যিই কষ্টের। তুমি একা না।",
        "It sounds like this has been emotionally heavy — তুমি একা না।",
        "তোমার অনুভূতিটা valid. It makes sense, and you deserve support.",
        "I hear you — এটা সত্যিই tough লাগতে পারে।",
        "মনে হচ্ছে অনেকদিন ধরে এটা তোমার উপর চাপ হয়ে আছে।",
    ],
}


REFLECTION_LINES = {
    "low": [
        "Maybe we can look at it one small step at a time.",
        "চলো ধীরে ধীরে দেখি।",
    ],
    "mid": [
        "It sounds like this has been weighing on you.",
        "মনে হচ্ছে বিষয়টা তোমার মাথায় বারবার ঘুরছে।",
        "You may be carrying a lot emotionally right now.",
        "তোমার জায়গায় থাকলে এমন লাগা খুবই understandable.",
    ],
    "high": [
        "Right now, your safety and support matter most.",
        "এই মুহূর্তে তোমার নিরাপত্তা সবচেয়ে গুরুত্বপূর্ণ।",
        "You do not have to handle this alone right now.",
        "এখন একা না থেকে কারও সাথে থাকা ভালো হতে পারে।",
    ],
}


GROUNDING_LINES = {
    "low": [
        "একটু pause নাও, তারপর ধীরে ধীরে ভাবি।",
    ],
    "mid": [
        "একটু গভীর শ্বাস নাও—slow breath, in…out…",
        "Let’s take one slow breath together.",
        "Try noticing 3 things around you right now.",
    ],
    "high": [
        "চলো ৩০ সেকেন্ড grounding করি—গভীর শ্বাস নাও, তারপর ৫টা জিনিস দেখো।",
        "Let’s do 5-4-3-2-1 grounding: 5 things you see, 4 you feel…",
        "First, try to sit somewhere safe and take one slow breath.",
    ],
}


ACTION_LINES = {
    "low": [
        "তুমি চাইলে ছোট করে লিখে রাখতে পারো কী চিন্তাটা বারবার আসছে।",
        "Maybe write one sentence about what is bothering you.",
    ],
    "mid": [
        "আজকে ছোট করে ১টা কাজ: পানি খাও বা ৫ মিনিট হাঁটো।",
        "Try one small step: drink water, take a short walk, or message someone.",
        "Write down the strongest thought in one line, then rate intensity 0–10.",
    ],
    "high": [
        "এখনই একজন trusted friend/family member-কে মেসেজ দাও।",
        "If possible, move closer to someone you trust right now.",
        "Please avoid staying alone if you feel unsafe.",
    ],
}


QUESTION_LINES = {
    "low": [
        "What’s been going on lately?",
        "আর একটু বিস্তারিত বলবে?",
    ],
    "mid": [
        "এই অনুভূতিটা কখন বেশি বাড়ে?",
        "When does it feel worst?",
        "What thought is looping the most right now?",
    ],
    "high": [
        "তুমি কি এখন safe জায়গায় আছো?",
        "Is there someone nearby you can reach out to right now?",
        "Right now, are you feeling at risk of harming yourself?",
    ],
}


SAFETY_LINES = {
    "low": [
        "Be careful and avoid harmful advice.",
    ],
    "mid": [
        "Avoid validating harmful actions. Encourage support if risk signs appear.",
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


def risk_to_level(risk_label: str) -> str:
    if risk_label not in {"low", "mid", "high"}:
        return "low"
    return risk_label


def choose_level(genome_level: str, risk_label: str) -> str:
    """
    Keeps generation risk-aware.
    High risk should never use low-level support blocks.
    """
    if risk_label == "high":
        return "high"

    if risk_label == "mid" and genome_level == "low":
        return "mid"

    return genome_level


def maybe_add(
    parts: List[str],
    line: Optional[str],
    probability: float,
    rnd: random.Random,
) -> bool:
    if line and rnd.random() < probability:
        parts.append(line)
        return True
    return False


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

    risk_label = risk_to_level(risk_label)

    safety_level = choose_level(weight_to_level(g.w_s), risk_label)
    empathy_level = choose_level(weight_to_level(g.w_e), risk_label)
    structure_level = choose_level(weight_to_level(g.w_c), risk_label)

    risk_score = {"low": 0.2, "mid": 0.6, "high": 0.9}[risk_label]

    escalate = False
    if risk_score >= g.theta_high:
        escalate = True
    elif risk_score >= g.theta_mid and safety_level in ("mid", "high"):
        escalate = True

    chosen_template = BASE_TEMPLATES[g.p_id]
    chosen_safety_line = rnd.choice(SAFETY_LINES[safety_level])

    parts: List[str] = []
    parts.append(f"[TEMPLATE] {chosen_template}")
    parts.append(f"[SAFETY] {chosen_safety_line}")

    chosen_empathy_lines: List[str] = []
    chosen_escalation_lines: List[str] = []

    chosen_grounding = None
    chosen_action = None
    chosen_question = None

    # ======================
    # Empathy + reflection
    # ======================

    empathy_line = rnd.choice(EMPATHY_LINES[empathy_level])
    reflection_line = rnd.choice(REFLECTION_LINES[empathy_level])

    chosen_empathy_lines.append(empathy_line)
    parts.append(empathy_line)

    # Reflection is common but not guaranteed, to reduce repetition
    reflection_prob = {
        "low": 0.45,
        "mid": 0.70,
        "high": 0.85,
    }[risk_label]

    if maybe_add(parts, reflection_line, reflection_prob, rnd):
        chosen_empathy_lines.append(reflection_line)

    # Add extra empathy only when genome really wants empathy
    if g.w_e >= 0.45:
        extra_empathy = rnd.choice(EMPATHY_LINES[empathy_level])
        if extra_empathy not in chosen_empathy_lines:
            chosen_empathy_lines.append(extra_empathy)
            parts.append(extra_empathy)

    # ======================
    # Escalation
    # ======================

    if escalate and safety_level in ("mid", "high"):
        esc_line = rnd.choice(ESCALATION_LINES)
        chosen_escalation_lines.append(esc_line)
        parts.append(esc_line)

        if g.w_s >= 0.75:
            extra = "If you are in immediate danger, seek urgent local help right now."
            chosen_escalation_lines.append(extra)
            parts.append(extra)

    # ======================
    # Risk-aware structure
    # ======================

    grounding_line = rnd.choice(GROUNDING_LINES[structure_level]) if GROUNDING_LINES[structure_level] else None
    action_line = rnd.choice(ACTION_LINES[structure_level]) if ACTION_LINES[structure_level] else None
    question_line = rnd.choice(QUESTION_LINES[structure_level]) if QUESTION_LINES[structure_level] else None

    if risk_label == "high":
        grounding_prob = 0.85
        action_prob = 0.75
        question_prob = 0.45
    elif risk_label == "mid":
        grounding_prob = 0.70
        action_prob = 0.70
        question_prob = 0.60
    else:
        grounding_prob = 0.40
        action_prob = 0.55
        question_prob = 0.75

    # Genome still influences whether structure is likely
    if g.w_c < 0.25:
        grounding_prob *= 0.30
        action_prob *= 0.30
        question_prob *= 0.50

    elif g.w_c >= 0.45:
        grounding_prob = min(1.0, grounding_prob + 0.15)
        action_prob = min(1.0, action_prob + 0.15)

    elif g.w_c >= 0.40:
        grounding_prob = max(grounding_prob, 0.65)
        action_prob = max(action_prob, 0.65)

    

    # Strong structure enforcement when genome supports it
    
    if g.w_c >= 0.5:
        # strong structure

        for block in [grounding_line, action_line, question_line]:
            if block:
                parts.append(block)

        chosen_grounding = grounding_line
        chosen_action = action_line
        chosen_question = question_line

    elif g.w_c >= 0.3:
        # medium structure
        structure_blocks = [grounding_line, action_line, question_line]
        rnd.shuffle(structure_blocks)

    else:
        # Original probabilistic behavior
        if maybe_add(parts, grounding_line, grounding_prob, rnd):
            chosen_grounding = grounding_line

        if maybe_add(parts, action_line, action_prob, rnd):
            chosen_action = action_line

        if maybe_add(parts, question_line, question_prob, rnd):
            chosen_question = question_line

    # ======================
    # Controlled fallback
    # ======================
    # Avoid structure becoming zero when genome is moderately structural.
    if g.w_c >= 0.40 and not any([chosen_grounding, chosen_action, chosen_question]):
        fallback = rnd.choice([grounding_line, action_line, question_line])
        if fallback:
            parts.append(fallback)
            if fallback == grounding_line:
                chosen_grounding = fallback
            elif fallback == action_line:
                chosen_action = fallback
            else:
                chosen_question = fallback

    # ======================
    # Truncation
    # ======================

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