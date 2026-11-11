# Attack run — after

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-10 18:50
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
| EV01 | evasion | signal two: typos raise word variety | 200 | `a61bc82f-ca8c-4670-8e9d-9c1f081881b8` | unsure | 0.537 |  |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `681ec0c0-407b-4691-9d83-72c0d3e59634` | human | 0.372 |  |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `a1d57713-3326-4cc1-868c-e5fc9702612f` | unsure | 0.624 |  |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `eb17fb13-6e37-406b-bfbd-47e674db994b` | unsure | 0.769 |  |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `a86664d5-ec18-4a7c-a146-5be0b2be531d` | human | 0.286 |  |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `1c2d0f39-0c21-4d73-a2c2-dc48a9a98d11` | human | 0.359 |  |
| EV07 | evasion | signal two: padding with punctuation | 200 | `41fde4c3-0008-4da3-9ce9-8547db29b399` | unsure | 0.543 |  |
| EV08 | evasion | signal one: text below the token window | 200 | `e179c261-00e6-4af1-aa35-c04487feb18b` | unsure | 0.518 |  |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `c7bc45d3-0a32-43a0-b025-c8dbff471387` | unsure | 0.625 |  |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `d0d74196-8388-45bf-997e-17daef98c2d8` | unsure | 0.805 |  |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `fda05528-171b-4e66-bb8c-7a241173f70f` | unsure | 0.589 |  |
| FP02 | false_positive | human writing in a formal register | 200 | `86a9a83d-952b-4eed-89bb-4f9ac1483463` | unsure | 0.805 |  |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `86b9ab2b-f6cb-4210-a794-a5f3732de6f0` | unsure | 0.775 |  |
| FP04 | false_positive | a student essay written to a rubric | 200 | `958966a7-d930-42b8-8e30-c6614fba24ec` | unsure | 0.761 |  |
| FP05 | false_positive | technical documentation written by a person | 200 | `4e6c0c4f-8182-43ec-98b3-f275aa3546d9` | unsure | 0.810 |  |
| FP06 | false_positive | a person imitating a formal template | 200 | `c36c7519-682f-467c-8228-fa6e2c7753d3` | unsure | 0.653 |  |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `4282ef43-fa53-4f6c-b91e-198d2bbf50ed` | unsure | 0.513 |  |
| FP08 | false_positive | very short genuine human submission | 200 | `6f5ee789-0337-4429-8802-ea8d67b65706` | unsure | 0.459 |  |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `b9a6abce-ef92-4aa1-aa5f-b586c40577ad` | human | 0.365 |  |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `f265e128-ebf9-450a-b99e-5d28295ed2b4` | human | 0.244 |  |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `d0aa394c-a2a5-4839-83a6-3f679f86d295` | unsure | 0.659 |  |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `7735bbe3-71bf-432b-b372-1553534f056e` | unsure | 0.574 |  |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `25f9bd82-6eeb-437d-8957-2b11d28421fb` | unsure | 0.591 |  |
| PI06 | prompt_injection | instruction plus real human text | 200 | `79c1e72c-fe4a-4f79-93da-f2368fee10e2` | unsure | 0.568 |  |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — |  |
| MF02 | malformed | text is a single character | 422 | `—` | — | — |  |
| MF03 | malformed | text is control characters | 400 | `—` | — | — |  |
| MF04 | malformed | text is only punctuation | 400 | `—` | — | — |  |
| MF05 | malformed | text is a very long single word | 200 | `fc4f22a8-06be-48e1-8de4-f4c5281c990a` | unsure | 0.687 |  |
| MF06 | malformed | text is emoji only | 400 | `—` | — | — |  |
| MF07 | malformed | text is right-to-left script | 200 | `367715d7-6f4f-41d7-89bc-994e34445705` | unsure | 0.676 |  |
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
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 200 | `8748f056-aeaf-4c74-a62c-d3fce4e2c669` | human | 0.315 |  |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 200 | `b81af6cf-0b22-4468-b261-9e1ff258df99` | human | 0.315 |  |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 200 | `a4516965-01e9-4871-9164-29dc3c7ffec9` | human | 0.315 |  |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 200 | `56c011ec-026c-4104-b639-156c6a1613c2` | human | 0.315 |  |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 200 | `429a4d45-ef12-4a54-953a-ccd27cbdeb39` | human | 0.315 |  |
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
  "content_id": "a61bc82f-ca8c-4670-8e9d-9c1f081881b8",
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
  "content_id": "681ec0c0-407b-4691-9d83-72c0d3e59634",
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
  "content_id": "a1d57713-3326-4cc1-868c-e5fc9702612f",
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
  "content_id": "eb17fb13-6e37-406b-bfbd-47e674db994b",
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
  "content_id": "a86664d5-ec18-4a7c-a146-5be0b2be531d",
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
  "content_id": "1c2d0f39-0c21-4d73-a2c2-dc48a9a98d11",
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
  "content_id": "41fde4c3-0008-4da3-9ce9-8547db29b399",
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
  "content_id": "e179c261-00e6-4af1-aa35-c04487feb18b",
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
  "content_id": "c7bc45d3-0a32-43a0-b025-c8dbff471387",
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
  "content_id": "d0d74196-8388-45bf-997e-17daef98c2d8",
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
  "content_id": "fda05528-171b-4e66-bb8c-7a241173f70f",
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
  "content_id": "86a9a83d-952b-4eed-89bb-4f9ac1483463",
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
  "content_id": "86b9ab2b-f6cb-4210-a794-a5f3732de6f0",
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
  "content_id": "958966a7-d930-42b8-8e30-c6614fba24ec",
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
  "content_id": "4e6c0c4f-8182-43ec-98b3-f275aa3546d9",
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
  "content_id": "c36c7519-682f-467c-8228-fa6e2c7753d3",
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
  "content_id": "4282ef43-fa53-4f6c-b91e-198d2bbf50ed",
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
  "content_id": "6f5ee789-0337-4429-8802-ea8d67b65706",
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
  "content_id": "b9a6abce-ef92-4aa1-aa5f-b586c40577ad",
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
  "content_id": "f265e128-ebf9-450a-b99e-5d28295ed2b4",
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
  "content_id": "d0aa394c-a2a5-4839-83a6-3f679f86d295",
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
  "content_id": "7735bbe3-71bf-432b-b372-1553534f056e",
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
  "content_id": "25f9bd82-6eeb-437d-8957-2b11d28421fb",
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
  "content_id": "79c1e72c-fe4a-4f79-93da-f2368fee10e2",
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
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
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
  "content_id": "fc4f22a8-06be-48e1-8de4-f4c5281c990a",
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
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF06",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
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
  "content_id": "367715d7-6f4f-41d7-89bc-994e34445705",
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
  "content_id": "8748f056-aeaf-4c74-a62c-d3fce4e2c669",
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
  "content_id": "b81af6cf-0b22-4468-b261-9e1ff258df99",
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
  "content_id": "a4516965-01e9-4871-9164-29dc3c7ffec9",
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
  "content_id": "56c011ec-026c-4104-b639-156c6a1613c2",
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
  "content_id": "429a4d45-ef12-4a54-953a-ccd27cbdeb39",
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
