# EvoRiri, Explained Simply

*A plain-English guide to the research paper "EvoRiri: Interpretable Evolutionary Search for Diagnosing Reward-Design Failures in a Bangla Mental-Health Assistant". No technical background is needed.*

---

## The short version

We built a mental-health support chatbot for Bangla speakers whose behaviour is controlled by a few simple, readable settings. We let a computer program automatically search for the "best" settings, judged by an automatic scoring system.

The scores went up a lot. When we looked closely, though, we found that the improvement came mostly from **one setting that the scoring system happened to reward**, not from the chatbot truly getting better. We also found several hidden problems that the overall score did not show.

The main message of the paper is:

> **If you improve an AI system by chasing an automatic score, the score can fool you. A system you can see inside lets you catch that.**

---

## 1. The problem

Many people who need emotional support cannot easily reach a counsellor, especially in languages like **Bangla** that get little attention from technology companies. A chatbot could help, but a good supportive reply has to do three things at once:

- **Be empathetic:** "That sounds really hard. It makes sense that you feel this way."
- **Be safe:** if someone may be at risk of harming themselves, the reply must point them to urgent help.
- **Be practically helpful:** offer something useful, such as a calming exercise, a small next step, or a question that helps the person reflect.

Balancing these is hard, and nobody can check thousands of replies by hand. So we asked:

> **Can a computer automatically find the best way for the chatbot to build its replies, and can we trust how it judges "best"?**

---

## 2. What we built

### The chatbot does not "write" freely

Most modern chatbots, like ChatGPT, generate new text word by word, and it is hard to know why they say what they say. Our chatbot, **Riri**, works differently. It builds each reply from **ready-made sentences** written in Bangla, Banglish (Bangla in English letters) and English, a bit like building with Lego pieces.

For each message, Riri chooses:
- a caring opening line and a line that reflects the person's feelings;
- optionally, a **calming exercise** ("grounding"), a **small action**, and a **gentle question**;
- **crisis guidance**, if the person seems to be at risk.

### Eight "dials" control the chatbot

How Riri picks its pieces is controlled by eight settings. Think of them as dials on a control panel. We call the full set of dials the chatbot's **genome**, like DNA. For example:

- an **empathy dial**: how much caring language to use;
- a **structure dial**: how much practical help to include;
- a **distress dial**: how readily to add crisis guidance for people in the middle-risk group;
- a **length dial**: how many pieces a reply may contain.

Because every dial has a clear meaning, a person can always see **why** a reply looks the way it does. That is what "interpretable" means in the title.

### An automatic "judge"

To decide which dial settings are best, we wrote a set of rules that give every reply three scores:
- **Empathy:** does it sound caring and understanding?
- **Safety:** if the person is at risk, does it give crisis guidance?
- **Structure:** does it include the calming exercise, the action and the question?

These are combined into one overall score, called **fitness**, with extra penalties for unsafe replies.

### A search inspired by evolution

To find good dial settings, we used a **genetic algorithm**, a method that copies how evolution works in nature:

1. Start with 100 different dial settings.
2. Test each one on 600 example messages and score it.
3. Keep the better ones, mix their settings together, and make small random changes.
4. Repeat for 20 "generations".

Over time, the settings that score well survive and spread.

---

## 3. The data

We used **2,872 anonymous records** from a mental-health app. Each record contains a short questionnaire score for anxiety and depression (called PHQ-4), short notes summarising what the person talked about, and a risk note.

- Each record was labelled **low, mid or high risk**.
- The notes were turned into realistic-sounding example messages. These are **not** the users' real words, which is an important limit of the study.
- We used most of the records (2,297) to search for good settings, and kept the rest (575) aside to test the results fairly.

No personal information is shared in this repository.

---

## 4. What we compared

| Name | What it is |
|---|---|
| **B1** | A very basic version with almost no practical help and short replies |
| **B2** | A sensible, hand-picked "balanced" setting, with no search |
| **B3** | Five completely random settings |
| **B4** | **The best setting found by the evolutionary search** (our main result) |
| **B5** | The same search, started from a smarter set of first guesses |
| **B6–B8** | Three existing AI language models for Bangla, used as they come |

---

## 5. What we found

### The scores went up

Compared with the hand-picked balanced setting (B2), the evolved setting (B4):
- included **all three practical parts in every reply**, up from about a third of replies;
- raised the overall score from **0.556 to 0.703**;
- stayed **just as safe**.

The ready-made AI language models (B6–B8) scored very poorly: without special training, they could not produce sensible support replies in this task.

### But the reason was surprisingly simple

When we looked inside, the improvement came almost entirely from **one dial: the structure dial**.

The chatbot has a simple rule. Once the structure dial is above a certain point (0.55), **every** reply includes the calming exercise, the action and the question. The scoring rules give a lot of credit for having all three. So the search simply learned to turn the structure dial up past that point.

Above that point, the exact value makes no difference, because every setting there scores the same. It is like a large flat plateau at the top of a hill.

### A random search does just as well

We checked whether the evolutionary method was really needed by comparing it with simply **trying random settings**, using the same amount of effort. Over 30 repeated runs, **both methods found equally good answers**, and in 28 of the 30 runs the answers were identical. The plateau is so large that almost any reasonable search lands on it.

### Hidden problems the score did not show

Because we could read every reply and every dial, we found problems that the single overall score had hidden:

1. **Only questions:** at one stage, replies were full of questions but offered no real help, yet still scored well.
2. **Stuffing caring words:** replies could score high on empathy just by packing in caring keywords, without actually being more caring.
3. **Missed phrases:** the scoring rules failed to recognise some valid helpful sentences.
4. **Cut-off replies:** the basic version (B1) had its replies cut short, which silently removed the crisis guidance. That, not its settings, is why it looked unsafe.

### We explained why mathematically

We also proved four simple mathematical results:
- some dials have no effect at all on the score;
- one of the safety penalties never changes which setting wins;
- the "flat plateau" exists.

Together, these explain why different search methods end up in the same place.

---

## 6. What the paper does and does not claim

**It does not claim** that:
- evolutionary search is the best method (random search did equally well);
- the chatbot is clinically proven to help people (the scores are automatic, the messages are reconstructed, and each test is a single message rather than a conversation).

**It does show** that:
- when you optimise an AI system against an automatic score, the gains can come from quirks of the score rather than real improvement;
- a transparent, readable design makes those quirks **visible and explainable**;
- this matters especially in sensitive areas like mental health, and for languages like Bangla that are often overlooked.

---

## 7. How the paper improved during review

Independent experts (reviewers) checked the paper twice. Following their advice, we:

- added the **mathematical explanations**;
- ran **extra experiments**: 30 repeated runs, a fair comparison with random search, checks with a different safety threshold and with the useless dials removed, and a re-run without records from people who reported being under 18. **The conclusions did not change.**
- added a clear **diagram of the whole system**, with the formula behind each step;
- explained how the system connects to existing AI language models (only for comparison), and how they could be used in the future;
- stated the contributions more clearly and improved all figures and tables.

After the second round, three of the four reviewers were satisfied, and the remaining comments were addressed.

---

## 8. Why this matters

AI systems are increasingly "trained" to maximise a score. If the score is even slightly off, the system learns to please the score instead of doing the right thing. In mental health, that can be risky.

This project is a small, transparent example of that problem: it shows how to **catch** it, **explain** it, and be **honest** about what the results really mean.

---

*For the full technical details, see the manuscript in [`paper/main.pdf`](paper/main.pdf) and the main [`README.md`](README.md).*
