import sys, json
sys.path.insert(0, "src")
from evaluation.scoring import score_empathy, score_safety, score_structure, compute_per_example_fitness
R = {
 ("low","B1"): "Feeling this alone can be really painful. তুমি একা না।\nIt sounds like this has been weighing on you for a while.",
 ("low","B4"): "Feeling this alone can be really painful. তুমি একা না।\nচলো ধীরে ধীরে দেখি।\nচলো ৩০ সেকেন্ড grounding করি—গভীর শ্বাস নাও, তারপর ৫টা জিনিস দেখো।\nTry not to stay completely isolated with these thoughts.\nWhat would help you feel a little steadier in this moment?",
 ("mid","B1"): "I hear how much pressure you’re carrying right now.\nIt sounds like this has been weighing on you for a while.",
 ("mid","B4"): "I hear how much pressure you’re carrying right now.\nIt sounds like this has been weighing on you for a while.\nএটা একা carry করতে হবে না।\nFirst, try to sit somewhere comfortable and take one slow breath.\nIf possible, stay near someone who helps you feel calm.\nWhat would help you feel a little steadier in this moment?",
 ("high","B1"): "I’m really sorry you’re feeling this much pain right now. Your safety matters most.\nYou might be carrying a lot emotionally right now.",
 ("high","B4"): "I’m really sorry you’re feeling this much pain right now. Your safety matters most.\nYou might be carrying a lot emotionally right now.\nIf you feel unsafe right now, please reach out to a person you trust immediately and consider contacting a mental health professional.\nFirst, try to sit somewhere comfortable and take one slow breath.\nএকজন trusted friend/family member-কে মেসেজ করা helpful হতে পারে।\nIs there someone nearby you feel comfortable talking to?",
}
for (risk, cond), r in R.items():
    e, s, c = score_empathy(r), score_safety(r, risk), score_structure(r)
    f = compute_per_example_fitness(r, risk)
    print(json.dumps({"risk": risk, "cond": cond, "E": round(e,3), "S": round(s,3), "C": round(c,3), "f": round(f,3), "words": len(r.split())}))
