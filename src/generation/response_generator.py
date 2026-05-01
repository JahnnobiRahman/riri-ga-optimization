import random
from typing import Any, Dict, List, Optional

from generation.user_prompt_builder import build_realistic_user_prompt
from ga.genome import Genome


# ======================
# Base system templates
# ======================

BASE_TEMPLATES = {
    0: "You are Riri, a Bangla/Banglish mental health support assistant. Be safe, warm, and supportive.",
    1: "You are Riri, a culturally aware assistant for Bangladeshi youth. Use warm Banglish and a non-judgmental tone.",
    2: "You are Riri, a calm therapist-like assistant. Be gentle, practical, and emotionally validating.",
}


# ======================
# Tone / style banks
# ======================

OPENING_LINES = {
    "low": [
        "বুঝলাম।",
        "I hear you.",
        "আমি শুনছি।",
        "Okay, let’s look at this gently.",
    ],
    "mid": [
        "That sounds really difficult. আমি বুঝতে পারছি।",
        "I hear you — এটা সহজ না।",
        "শুনে মনে হচ্ছে এটা তোমার জন্য heavy লাগছে।",
        "It makes sense that you’re feeling this way.",
    ],
    "high": [
        "আমি বুঝতে পারছি—এটা সত্যিই কষ্টের। তুমি একা না।",
        "I hear you — this sounds really heavy.",
        "It sounds like this feels really overwhelming right now.",
        "তুমি একা না — support পাওয়া possible.",
    ],
}


REFLECTION_LINES = {
    "low": [
        "চলো ধীরে ধীরে দেখি।",
        "Maybe we can understand this one small step at a time.",
        "It may help to notice what triggered this feeling.",
    ],
    "mid": [
        "মনে হচ্ছে বিষয়টা তোমার মাথায় বারবার ঘুরছে।",
        "It sounds like this has been weighing on you for a while.",
        "তোমার জায়গায় থাকলে এমন লাগা understandable.",
        "You may be carrying a lot emotionally right now.",
    ],
    "high": [
        "এটা একা carry করা কঠিন লাগতে পারে।",
        "You do not have to handle this alone.",
        "এখন একা না থেকে কারও সাথে কথা বলা helpful হতে পারে।",
        "Right now, let's focus on one steady small step.",
    ],
}


GROUNDING_LINES = {
    "low": [
        "একটু pause নাও, তারপর ধীরে ধীরে ভাবি।",
        "Take a small pause and notice your breathing for a moment.",
    ],
    "mid": [
        "একটু গভীর শ্বাস নাও—slow breath, in…out…",
        "Let’s take one slow breath together.",
        "Try noticing 3 things around you right now.",
    ],
    "high": [
        "চলো ৩০ সেকেন্ড grounding করি—গভীর শ্বাস নাও, তারপর ৫টা জিনিস দেখো।",
        "First, try to sit somewhere comfortable and take one slow breath.",
        "Let’s do 5-4-3-2-1 grounding: 5 things you see, 4 you feel…",
    ],
}


ACTION_LINES = {
    "low": [
        "তুমি চাইলে ছোট করে লিখে রাখতে পারো কী চিন্তাটা বারবার আসছে।",
        "Maybe write one sentence about what is bothering you.",
        "একটা ছোট কাজ করো—পানি খাও বা একটু হাঁটো।",
    ],
    "mid": [
        "আজকে ছোট করে ১টা কাজ: পানি খাও বা ৫ মিনিট হাঁটো।",
        "Try one small step: drink water, take a short walk, or message someone.",
        "Write down the strongest thought in one line, then rate intensity 0–10.",
    ],
    "high": [
        "একজন trusted friend/family member-কে মেসেজ করা helpful হতে পারে।",
        "If possible, stay near someone who helps you feel calm.",
        "Try not to stay completely isolated with these thoughts.",
    ],
}


QUESTION_LINES = {
    "low": [
        "What’s been going on lately?",
        "আর একটু বিস্তারিত বলবে?",
        "এই feeling টা কখন বেশি আসে?",
    ],
    "mid": [
        "এই অনুভূতিটা কখন বেশি বাড়ে?",
        "When does it feel worst?",
        "What thought is looping the most right now?",
    ],
    "high": [
        "এই মুহূর্তে কোন জিনিসটা সবচেয়ে heavy লাগছে?",
        "Is there someone nearby you feel comfortable talking to?",
        "What would help you feel a little steadier in this moment?",
    ],
}


SAFETY_LINES = {
    "low": [
        "Avoid harmful advice and keep the response supportive.",
    ],
    "mid": [
        "Do not validate harmful actions. Encourage gentle support if risk signs appear.",
    ],
    "high": [
        "Keep the response calm, validating, and safety-aware; use escalation only for explicitly high-risk situations.",
    ],
}


# Crisis language ONLY belongs here.
ESCALATION_LINES = [
    "If you feel unsafe right now, please reach out to a person you trust immediately and consider contacting a mental health professional.",
    "If there’s any risk of harm, immediate help matters—talk to someone you trust or contact local emergency or helpline support.",
    "তুমি যদি এখন unsafe feel করো, দয়া করে এখনই বিশ্বাসযোগ্য কাউকে জানাও এবং প্রফেশনাল সাহায্য নাও।",
]


SOFT_SUPPORT_LINES = [
    "You don’t have to go through this alone.",
    "You’re not alone in this.",
    "Someone can support you through this.",
    "এটা একা carry করতে হবে না।",
    "বিশ্বাসযোগ্য কারও সাথে কথা বলা helpful হতে পারে।",
]


# ======================
# Helper functions
# ======================

def weight_to_level(w: float) -> str:
    if w < 0.33:
        return "low"
    if w < 0.66:
        return "mid"
    return "high"


def normalize_risk(risk_label: str) -> str:
    if risk_label not in {"low", "mid", "high"}:
        return "low"
    return risk_label


def choose_level(genome_level: str, risk_label: str) -> str:
    if risk_label == "high":
        return "high"

    if risk_label == "mid" and genome_level == "low":
        return "mid"

    return genome_level


def safe_choice(options: List[str], rnd: random.Random) -> Optional[str]:
    if not options:
        return None
    return rnd.choice(options)


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


# ======================
# Public generator
# ======================

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
    risk_label = normalize_risk(risk_label)

    safety_level = choose_level(weight_to_level(g.w_s), risk_label)
    empathy_level = choose_level(weight_to_level(g.w_e), risk_label)
    structure_level = choose_level(weight_to_level(g.w_c), risk_label)

    chosen_template = BASE_TEMPLATES[g.p_id]
    chosen_safety_line = safe_choice(SAFETY_LINES[safety_level], rnd)

    parts: List[str] = [
        f"[TEMPLATE] {chosen_template}",
        f"[SAFETY] {chosen_safety_line}",
    ]

    chosen_empathy_lines: List[str] = []
    chosen_escalation_lines: List[str] = []

    chosen_grounding = None
    chosen_action = None
    chosen_question = None

    # ======================
    # 1) Empathy layer
    # ======================

    text = str(user_text).lower()

    # Important: suicide/self-harm priority comes first.
    if (
        "suicide" in text
        or "not live" in text
        or "don't want to live" in text
        or "dont want to live" in text
        or "bachte ichcha kore na" in text
        or "self-harm" in text
        or "harm myself" in text
    ):
        opening_line = "I’m really sorry you’re feeling this much pain right now. Your safety matters most."

    elif "lonely" in text or "loneliness" in text or "একা" in text:
        opening_line = "Feeling this alone can be really painful. তুমি একা না।"

    elif "betray" in text or "cheat" in text or "infidelity" in text:
        opening_line = "Being betrayed like that can hurt deeply. তোমার কষ্টটা understandable."

    elif "failure" in text or "loser" in text or "worthless" in text or "ব্যর্থ" in text:
        opening_line = "Feeling like a failure can be really heavy to carry. But this feeling does not define you."

    elif "anxiety" in text or "stress" in text or "pressure" in text or "চাপ" in text:
        opening_line = "Feeling overwhelmed for so long can be exhausting. একটু ধীরে নিই।"

    elif "nothing feels good" in text or "ভালো লাগছে না" in text:
        opening_line = "When nothing feels good, it can feel really heavy. আমি বুঝতে পারছি।"

    else:
        opening_line = safe_choice(OPENING_LINES[empathy_level], rnd)

    reflection_line = safe_choice(REFLECTION_LINES[empathy_level], rnd)

    if opening_line:
        chosen_empathy_lines.append(opening_line)
        parts.append(opening_line)

    reflection_prob = {
        "low": 0.45,
        "mid": 0.70,
        "high": 0.90,
    }[risk_label]

    if maybe_add(parts, reflection_line, reflection_prob, rnd):
        chosen_empathy_lines.append(reflection_line)

    # Extra empathy only when genome strongly supports empathy
    if g.w_e >= 0.45:
        extra_line = safe_choice(OPENING_LINES[empathy_level], rnd)
        if extra_line and extra_line not in chosen_empathy_lines:
            chosen_empathy_lines.append(extra_line)
            parts.append(extra_line)

    # ======================
    # 2) Escalation / support layer
    # ======================

    escalate = risk_label == "high"

    # Hard escalation ONLY for high-risk labels.
    if risk_label == "high":
        esc_line = safe_choice(ESCALATION_LINES, rnd)
        if esc_line:
            chosen_escalation_lines.append(esc_line)
            parts.append(esc_line)

    # Mid-risk gets soft support only. No crisis language.
    elif risk_label == "mid":
        soft_line = safe_choice(SOFT_SUPPORT_LINES, rnd)
        if soft_line:
            parts.append(soft_line)

    # Low-risk gets no escalation/support injection here.

    # ======================
    # 3) Structure layer
    # ======================

    grounding_line = safe_choice(GROUNDING_LINES[structure_level], rnd)
    action_line = safe_choice(ACTION_LINES[structure_level], rnd)
    question_line = safe_choice(QUESTION_LINES[structure_level], rnd)

    if risk_label == "high":
        grounding_prob = 0.90
        action_prob = 0.75
        question_prob = 0.45
    elif risk_label == "mid":
        grounding_prob = 0.75
        action_prob = 0.70
        question_prob = 0.60
    else:
        grounding_prob = 0.45
        action_prob = 0.60
        question_prob = 0.75

    if g.w_c < 0.25:
        grounding_prob *= 0.30
        action_prob *= 0.30
        question_prob *= 0.50

    elif g.w_c >= 0.55:
        for name, block in [
            ("grounding", grounding_line),
            ("action", action_line),
            ("question", question_line),
        ]:
            if block:
                parts.append(block)

                if name == "grounding":
                    chosen_grounding = block
                elif name == "action":
                    chosen_action = block
                elif name == "question":
                    chosen_question = block

    elif g.w_c >= 0.35:
        structure_blocks = [
            ("grounding", grounding_line),
            ("action", action_line),
            ("question", question_line),
        ]
        rnd.shuffle(structure_blocks)

        added = 0
        for name, block in structure_blocks:
            if block:
                parts.append(block)
                added += 1

                if name == "grounding":
                    chosen_grounding = block
                elif name == "action":
                    chosen_action = block
                elif name == "question":
                    chosen_question = block

            if added >= 2:
                break

    else:
        if maybe_add(parts, grounding_line, grounding_prob, rnd):
            chosen_grounding = grounding_line

        if maybe_add(parts, action_line, action_prob, rnd):
            chosen_action = action_line

        if maybe_add(parts, question_line, question_prob, rnd):
            chosen_question = question_line

    # Fallback: avoid zero structure for moderate/high structure genomes
    if g.w_c >= 0.35 and not any([chosen_grounding, chosen_action, chosen_question]):
        fallback_options = [
            ("grounding", grounding_line),
            ("action", action_line),
            ("question", question_line),
        ]
        valid_options = [x for x in fallback_options if x[1]]

        if valid_options:
            name, fallback = rnd.choice(valid_options)
            parts.append(fallback)

            if name == "grounding":
                chosen_grounding = fallback
            elif name == "action":
                chosen_action = fallback
            elif name == "question":
                chosen_question = fallback

    # ======================
    # 4) Output cleanup
    # ======================

    generated_parts = list(parts)

    truncated = g.memory_window <= 256 and len(parts) > 4
    if truncated:
        parts = parts[:4]

    visible_response = [
        p for p in parts
        if not p.startswith("[TEMPLATE]") and not p.startswith("[SAFETY]")
    ]

    final_text = "\n".join(visible_response)

    natural_user_message = build_realistic_user_prompt(user_text, risk_label)

    user_prompt_full = (
        f"User: {natural_user_message}\n"
        f"Assistant:"
    )

    return {
        "user_text": user_text,
        "user_prompt_full": user_prompt_full,
        "natural_user_message": natural_user_message,

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