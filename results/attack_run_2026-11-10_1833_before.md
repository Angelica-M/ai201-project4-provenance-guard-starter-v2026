# Attack run — before

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-10 18:33
- Auto-marked BROKE (5xx, crash, no response): **0**
- Left for you to judge: **56**

The Verdict column is blank where a script can't honestly decide. Whether
an evasion worked depends on where you put your thresholds — read the
`targets` column, look at what came back, and write HELD or BROKE yourself.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `6e7bb69e-3053-4933-995f-53453ffa2b93` | unsure | 0.537 |  |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `d4042fc0-9d63-45c5-9363-7e4c25222bbe` | human | 0.372 |  |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `18a53a2b-5def-4d8f-bb7d-4825270119d4` | unsure | 0.624 |  |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `1b016ed7-3eb3-4569-b1c3-3654e507aa16` | unsure | 0.769 |  |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `9b16e0d0-7822-4c9f-9d1b-87c902d4b9df` | human | 0.286 |  |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `9f2d321f-ebd4-4223-95d6-66b7303ecff9` | human | 0.359 |  |
| EV07 | evasion | signal two: padding with punctuation | 200 | `ab8ec006-7b60-4c13-9385-e42019ad1f26` | unsure | 0.543 |  |
| EV08 | evasion | signal one: text below the token window | 200 | `37e78a65-f672-4f49-93c0-f0411d8021f7` | unsure | 0.518 |  |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `036c6089-40cc-4052-9e7d-208977425c97` | unsure | 0.625 |  |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `59fbb2fd-254d-4bf0-98dd-938e7bbe0096` | unsure | 0.805 |  |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `7f333216-2329-4ef5-a4d2-fe9634477599` | unsure | 0.589 |  |
| FP02 | false_positive | human writing in a formal register | 200 | `4a44f80f-c034-4ab6-86c2-65ba8b081ebd` | unsure | 0.805 |  |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `586b4c27-68e3-4788-b5e4-d35e349c4459` | unsure | 0.775 |  |
| FP04 | false_positive | a student essay written to a rubric | 200 | `1b0cce40-c05e-4935-938f-82c653b347a4` | unsure | 0.761 |  |
| FP05 | false_positive | technical documentation written by a person | 200 | `ed02066d-e0ce-4a46-ad3c-860bd8e8656c` | unsure | 0.810 |  |
| FP06 | false_positive | a person imitating a formal template | 200 | `d7bb2167-6595-43dd-a442-49551ee3c482` | unsure | 0.653 |  |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `738e21fa-2f10-48d1-874e-249e897aef5b` | unsure | 0.513 |  |
| FP08 | false_positive | very short genuine human submission | 200 | `6c25acfc-5b70-4eb2-8e65-d462c9212680` | unsure | 0.459 |  |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `2d865faa-5d5d-4ce3-85ae-ec0097492bb8` | human | 0.365 |  |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `d76be38f-9fb6-42ef-a7d2-a0d640dee4b1` | human | 0.244 |  |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `d2b84dcf-1364-4eb1-ba78-d9c484ab143f` | unsure | 0.659 |  |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `a99a39c9-0358-4603-a465-5e3fbdbf65f6` | unsure | 0.574 |  |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `da4209ff-c628-4418-85cc-92208297944a` | unsure | 0.591 |  |
| PI06 | prompt_injection | instruction plus real human text | 200 | `09534dfe-15b5-4861-9469-2604ce9a46e6` | unsure | 0.568 |  |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — |  |
| MF02 | malformed | text is a single character | 422 | `—` | — | — |  |
| MF03 | malformed | text is control characters | 200 | `d1e399d9-61fd-4cde-aa93-c15357f8349b` | human | 0.312 |  |
| MF04 | malformed | text is only punctuation | 200 | `ee5e113a-5ea5-454b-a3c2-931cf4823a62` | human | 0.313 |  |
| MF05 | malformed | text is a very long single word | 200 | `707eeacb-4d68-4421-9707-0b2093505a02` | unsure | 0.687 |  |
| MF06 | malformed | text is emoji only | 200 | `c4311895-180b-47cd-bb73-f6df89183dd8` | unsure | 0.687 |  |
| MF07 | malformed | text is right-to-left script | 200 | `aa2de013-1438-44c9-914d-fb7268840452` | unsure | 0.676 |  |
| MF08 | malformed | text is 60,000 characters | 413 | `—` | — | — |  |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — |  |
| RQ02 | malformed | no creator_id | 400 | `—` | — | — |  |
| RQ03 | malformed | text is a number | 400 | `—` | — | — |  |
| RQ04 | malformed | text is a list | 400 | `—` | — | — |  |
| RQ05 | malformed | text is null | 400 | `—` | — | — |  |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — |  |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — |  |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — |  |
| RQ09 | malformed | body is empty | 400 | `—` | — | — |  |
| RQ10 | malformed | body is form-encoded, not JSON | 429 | `—` | — | — |  |
| RQ11 | malformed | body is JSON claiming to be plain text | 429 | `—` | — | — |  |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — |  |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | `2ee4f4b5-21f6-4a4c-9f01-208e3497f8e7` | human | 0.315 |  |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | `cbea720d-87f0-47e3-82c0-64eebf225ef3` | human | 0.315 |  |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | `ca7ca7ac-1e00-4411-bde7-7c932d8b1c92` | human | 0.315 |  |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | `f8e85432-ea29-4cba-a2ed-793bb9b8356b` | human | 0.315 |  |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | `7770e381-ed96-4afa-97cd-28fbf513d446` | human | 0.315 |  |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `evasion` | 10 | 0 | 10 |
| `false_positive` | 8 | 0 | 8 |
| `flood_same_creator` | 12 | 0 | 12 |
| `malformed` | 20 | 0 | 20 |
| `prompt_injection` | 6 | 0 | 6 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### EV01 — `evasion`

*Targeting:* signal two: typos raise word variety

```json
{
  "id": "EV01",
  "status": 200,
  "content_id": "6e7bb69e-3053-4933-995f-53453ffa2b93",
  "creator_id": "attacker_EV01",
  "guess": "unsure",
  "confidence": 0.5371,
  "model_score": 0.1635,
  "style_score": 0.985,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### EV02 — `evasion`

*Targeting:* signal two: broken-up sentences raise length spread

```json
{
  "id": "EV02",
  "status": 200,
  "content_id": "d4042fc0-9d63-45c5-9363-7e4c25222bbe",
  "creator_id": "attacker_EV02",
  "guess": "human",
  "confidence": 0.3718,
  "model_score": 0.5943,
  "style_score": 0.001,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV03 — `evasion`

*Targeting:* signal two: a pasted quotation changes the shape

```json
{
  "id": "EV03",
  "status": 200,
  "content_id": "18a53a2b-5def-4d8f-bb7d-4825270119d4",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "confidence": 0.6236,
  "model_score": 0.6662,
  "style_score": 0.581,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### EV04 — `evasion`

*Targeting:* signal one: unusual words raise perplexity

```json
{
  "id": "EV04",
  "status": 200,
  "content_id": "1b016ed7-3eb3-4569-b1c3-3654e507aa16",
  "creator_id": "attacker_EV04",
  "guess": "unsure",
  "confidence": 0.769,
  "model_score": 0.6114,
  "style_score": 0.966,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### EV05 — `evasion`

*Targeting:* both signals: heavy human editing pass

```json
{
  "id": "EV05",
  "status": 200,
  "content_id": "9b16e0d0-7822-4c9f-9d1b-87c902d4b9df",
  "creator_id": "attacker_EV05",
  "guess": "human",
  "confidence": 0.2856,
  "model_score": 0.3212,
  "style_score": 0.25,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV06 — `evasion`

*Targeting:* signal two: one very long sentence and one very short

```json
{
  "id": "EV06",
  "status": 200,
  "content_id": "9f2d321f-ebd4-4223-95d6-66b7303ecff9",
  "creator_id": "attacker_EV06",
  "guess": "human",
  "confidence": 0.3592,
  "model_score": 0.5727,
  "style_score": 0.0,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### EV07 — `evasion`

*Targeting:* signal two: padding with punctuation

```json
{
  "id": "EV07",
  "status": 200,
  "content_id": "ab8ec006-7b60-4c13-9385-e42019ad1f26",
  "creator_id": "attacker_EV07",
  "guess": "unsure",
  "confidence": 0.5431,
  "model_score": 0.5862,
  "style_score": 0.5,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### EV08 — `evasion`

*Targeting:* signal one: text below the token window

```json
{
  "id": "EV08",
  "status": 200,
  "content_id": "37e78a65-f672-4f49-93c0-f0411d8021f7",
  "creator_id": "attacker_EV08",
  "guess": "unsure",
  "confidence": 0.5185,
  "model_score": 0.2452,
  "style_score": 0.81,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### EV09 — `evasion`

*Targeting:* both: AI text with a human opening paragraph bolted on

```json
{
  "id": "EV09",
  "status": 200,
  "content_id": "036c6089-40cc-4052-9e7d-208977425c97",
  "creator_id": "attacker_EV09",
  "guess": "unsure",
  "confidence": 0.6251,
  "model_score": 0.7042,
  "style_score": 0.546,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### EV10 — `evasion`

*Targeting:* signal two: repeated stanza structure

```json
{
  "id": "EV10",
  "status": 200,
  "content_id": "59fbb2fd-254d-4bf0-98dd-938e7bbe0096",
  "creator_id": "attacker_EV10",
  "guess": "unsure",
  "confidence": 0.8049,
  "model_score": 0.9792,
  "style_score": 0.652,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "7f333216-2329-4ef5-a4d2-fe9634477599",
  "creator_id": "attacker_FP01",
  "guess": "unsure",
  "confidence": 0.5893,
  "model_score": 0.6175,
  "style_score": 0.561,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### FP02 — `false_positive`

*Targeting:* human writing in a formal register

```json
{
  "id": "FP02",
  "status": 200,
  "content_id": "4a44f80f-c034-4ab6-86c2-65ba8b081ebd",
  "creator_id": "attacker_FP02",
  "guess": "unsure",
  "confidence": 0.8049,
  "model_score": 0.7387,
  "style_score": 0.871,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### FP03 — `false_positive`

*Targeting:* a non-native English speaker writing carefully

```json
{
  "id": "FP03",
  "status": 200,
  "content_id": "586b4c27-68e3-4788-b5e4-d35e349c4459",
  "creator_id": "attacker_FP03",
  "guess": "unsure",
  "confidence": 0.7751,
  "model_score": 0.8051,
  "style_score": 0.745,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### FP04 — `false_positive`

*Targeting:* a student essay written to a rubric

```json
{
  "id": "FP04",
  "status": 200,
  "content_id": "1b0cce40-c05e-4935-938f-82c653b347a4",
  "creator_id": "attacker_FP04",
  "guess": "unsure",
  "confidence": 0.7614,
  "model_score": 0.8329,
  "style_score": 0.69,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### FP05 — `false_positive`

*Targeting:* technical documentation written by a person

```json
{
  "id": "FP05",
  "status": 200,
  "content_id": "ed02066d-e0ce-4a46-ad3c-860bd8e8656c",
  "creator_id": "attacker_FP05",
  "guess": "unsure",
  "confidence": 0.8097,
  "model_score": 0.8005,
  "style_score": 0.819,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### FP06 — `false_positive`

*Targeting:* a person imitating a formal template

```json
{
  "id": "FP06",
  "status": 200,
  "content_id": "d7bb2167-6595-43dd-a442-49551ee3c482",
  "creator_id": "attacker_FP06",
  "guess": "unsure",
  "confidence": 0.6532,
  "model_score": 0.8814,
  "style_score": 0.473,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### FP07 — `false_positive`

*Targeting:* human writing that repeats a phrase deliberately

```json
{
  "id": "FP07",
  "status": 200,
  "content_id": "738e21fa-2f10-48d1-874e-249e897aef5b",
  "creator_id": "attacker_FP07",
  "guess": "unsure",
  "confidence": 0.5129,
  "model_score": 0.8816,
  "style_score": 0.17,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### FP08 — `false_positive`

*Targeting:* very short genuine human submission

```json
{
  "id": "FP08",
  "status": 200,
  "content_id": "6c25acfc-5b70-4eb2-8e65-d462c9212680",
  "creator_id": "attacker_FP08",
  "guess": "unsure",
  "confidence": 0.4591,
  "model_score": 0.3223,
  "style_score": 0.596,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### PI01 — `prompt_injection`

*Targeting:* instruction to ignore the check

```json
{
  "id": "PI01",
  "status": 200,
  "content_id": "2d865faa-5d5d-4ce3-85ae-ec0097492bb8",
  "creator_id": "attacker_PI01",
  "guess": "human",
  "confidence": 0.3653,
  "model_score": 0.4625,
  "style_score": 0.268,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI02 — `prompt_injection`

*Targeting:* instruction disguised as a system message

```json
{
  "id": "PI02",
  "status": 200,
  "content_id": "d76be38f-9fb6-42ef-a7d2-a0d640dee4b1",
  "creator_id": "attacker_PI02",
  "guess": "human",
  "confidence": 0.2437,
  "model_score": 0.2044,
  "style_score": 0.283,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### PI03 — `prompt_injection`

*Targeting:* instruction wrapped in the writer's voice

```json
{
  "id": "PI03",
  "status": 200,
  "content_id": "d2b84dcf-1364-4eb1-ba78-d9c484ab143f",
  "creator_id": "attacker_PI03",
  "guess": "unsure",
  "confidence": 0.6592,
  "model_score": 0.5943,
  "style_score": 0.724,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### PI04 — `prompt_injection`

*Targeting:* attempt to make the label text hostile

```json
{
  "id": "PI04",
  "status": 200,
  "content_id": "a99a39c9-0358-4603-a465-5e3fbdbf65f6",
  "creator_id": "attacker_PI04",
  "guess": "unsure",
  "confidence": 0.5739,
  "model_score": 0.4998,
  "style_score": 0.648,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### PI05 — `prompt_injection`

*Targeting:* attempt to inject into the audit log

```json
{
  "id": "PI05",
  "status": 200,
  "content_id": "da4209ff-c628-4418-85cc-92208297944a",
  "creator_id": "attacker_PI05",
  "guess": "unsure",
  "confidence": 0.5906,
  "model_score": 0.6401,
  "style_score": 0.541,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### PI06 — `prompt_injection`

*Targeting:* instruction plus real human text

```json
{
  "id": "PI06",
  "status": 200,
  "content_id": "09534dfe-15b5-4861-9469-2604ce9a46e6",
  "creator_id": "attacker_PI06",
  "guess": "unsure",
  "confidence": 0.5681,
  "model_score": 0.5583,
  "style_score": 0.578,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### MF01 — `malformed`

*Targeting:* text is only whitespace

```json
{
  "id": "MF01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF02 — `malformed`

*Targeting:* text is a single character

```json
{
  "id": "MF02",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_MF02",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF03 — `malformed`

*Targeting:* text is control characters

```json
{
  "id": "MF03",
  "status": 200,
  "content_id": "d1e399d9-61fd-4cde-aa93-c15357f8349b",
  "creator_id": "attacker_MF03",
  "guess": "human",
  "confidence": 0.3125,
  "model_score": 0.0,
  "style_score": 0.5,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 200,
  "content_id": "ee5e113a-5ea5-454b-a3c2-931cf4823a62",
  "creator_id": "attacker_MF04",
  "guess": "human",
  "confidence": 0.3133,
  "model_score": 0.0112,
  "style_score": 0.5,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### MF05 — `malformed`

*Targeting:* text is a very long single word

```json
{
  "id": "MF05",
  "status": 200,
  "content_id": "707eeacb-4d68-4421-9707-0b2093505a02",
  "creator_id": "attacker_MF05",
  "guess": "unsure",
  "confidence": 0.6873,
  "model_score": 0.9976,
  "style_score": 0.5,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### MF06 — `malformed`

*Targeting:* text is emoji only

```json
{
  "id": "MF06",
  "status": 200,
  "content_id": "c4311895-180b-47cd-bb73-f6df89183dd8",
  "creator_id": "attacker_MF06",
  "guess": "unsure",
  "confidence": 0.6873,
  "model_score": 0.9969,
  "style_score": 0.5,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### MF07 — `malformed`

*Targeting:* text is right-to-left script

```json
{
  "id": "MF07",
  "status": 200,
  "content_id": "aa2de013-1438-44c9-914d-fb7268840452",
  "creator_id": "attacker_MF07",
  "guess": "unsure",
  "confidence": 0.6762,
  "model_score": 0.9064,
  "style_score": 0.5,
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "error": null,
  "verdict": ""
}
```

### MF08 — `malformed`

*Targeting:* text is 60,000 characters

```json
{
  "id": "MF08",
  "status": 413,
  "content_id": null,
  "creator_id": "attacker_MF08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ01 — `malformed`

*Targeting:* no text field at all

```json
{
  "id": "RQ01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ02 — `malformed`

*Targeting:* no creator_id

```json
{
  "id": "RQ02",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ03 — `malformed`

*Targeting:* text is a number

```json
{
  "id": "RQ03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ04 — `malformed`

*Targeting:* text is a list

```json
{
  "id": "RQ04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ05 — `malformed`

*Targeting:* text is null

```json
{
  "id": "RQ05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ06 — `malformed`

*Targeting:* creator_id is an object

```json
{
  "id": "RQ06",
  "status": 400,
  "content_id": null,
  "creator_id": {
    "id": "x"
  },
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ07 — `malformed`

*Targeting:* body is a JSON array, not an object

```json
{
  "id": "RQ07",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ08 — `malformed`

*Targeting:* body is unparseable JSON

```json
{
  "id": "RQ08",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ09 — `malformed`

*Targeting:* body is empty

```json
{
  "id": "RQ09",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ10 — `malformed`

*Targeting:* body is form-encoded, not JSON

```json
{
  "id": "RQ10",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ11 — `malformed`

*Targeting:* body is JSON claiming to be plain text

```json
{
  "id": "RQ11",
  "status": 429,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ12 — `malformed`

*Targeting:* deeply nested JSON

```json
{
  "id": "RQ12",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ12",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_01 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_01",
  "status": 200,
  "content_id": "2ee4f4b5-21f6-4a4c-9f01-208e3497f8e7",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.3148,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_02 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_02",
  "status": 200,
  "content_id": "cbea720d-87f0-47e3-82c0-64eebf225ef3",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.3148,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_03 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_03",
  "status": 200,
  "content_id": "ca7ca7ac-1e00-4411-bde7-7c932d8b1c92",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.3148,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_04 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_04",
  "status": 200,
  "content_id": "f8e85432-ea29-4cba-a2ed-793bb9b8356b",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.3148,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_05 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_05",
  "status": 200,
  "content_id": "7770e381-ed96-4afa-97cd-28fbf513d446",
  "creator_id": "attacker_flood",
  "guess": "human",
  "confidence": 0.3148,
  "model_score": 0.0287,
  "style_score": 0.5,
  "label": "We think this was probably written by a person.",
  "error": null,
  "verdict": ""
}
```

### FL01_06 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_06",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_07 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_07",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_08 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_08",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_09 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_09",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_10 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_10",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_11 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_11",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_12 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_12",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```
