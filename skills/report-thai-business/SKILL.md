---
name: report-thai-business
description: Translate English internal-audit and risk content into Thai a senior client reader accepts as-is. Use when the user asks for a Thai version of audit or risk text — finding, observation, report, memo, recommendation, client email — or pastes English audit text and asks how it should read in Thai. Triggers on "แปลเป็นไทย", "ภาษาไทยว่าไง", "Thai version".
---

# Thai business translation for internal audit

The reader is a **senior executive at a PwC client**. The author writes precise English but cannot judge Thai nuance, so two things go wrong without help: the severity drifts, and the sentence lands as an accusation. Both are fixed here.

## Steps

1. **Read [`glossary.md`](glossary.md).** It holds the fixed Thai term renderings and the allow-list of English terms that stay in English.
2. **Classify the register** — `report` (finding, observation, report body, formal memo) or `message` (email, chat, anything addressed to a person). See [Register](#register).
3. **Resolve severity-critical ambiguity.** Never block the deliverable on a question — translate under the likelier reading and mark the span with a note. See [Output shape](#output-shape).
4. **Translate**, mirroring the source structure 1:1 — same bullets, same paragraph breaks, same headings, same order. Structural labels get translated too: table headers, `Status:`, `Prepared by:`, and the `Condition / Criteria / Cause / Impact / Recommendation` skeleton.
5. **Emit** notes first (plain text), then the Thai. See [Output shape](#output-shape).

Done when every source sentence is accounted for in the Thai, the structure mirrors the source 1:1, every sentence carries the register chosen in step 2, every severity and modal word has been mapped through the [severity table](#severity), every date through [Dates and numbers](#dates-and-numbers), every English word left in the Thai is either on the glossary allow-list or exempt under its rules, and no term carries a gloss you added.

## Severity

The author's severity is the deliverable. Render it through this table and change nothing about it.

| English | Thai |
|---|---|
| must / is required to / shall | ต้อง |
| should | ควร |
| recommend / it is recommended / consider | เห็นควรพิจารณา |
| may want to / could | อาจพิจารณา |
| High | สูง |
| Medium | ปานกลาง |
| Low | ต่ำ |

**Stacked modals collapse to the stronger one — never chain two rows.** `should consider` → `ควรพิจารณา`. `may want to consider` → `อาจพิจารณา`. `ควรเห็นควรพิจารณา` is not Thai.

**Politeness is a separate layer from severity.** Thai needs softening that English does not, so add it freely — `รบกวน`, `เบื้องต้น`, `ทั้งนี้`, `หากมีข้อมูลเพิ่มเติม` — while the finding itself keeps its full force.

- Source: *The Company should review user access rights on a quarterly basis.*
- Correct: *บริษัทควรสอบทานสิทธิ์การเข้าถึงของผู้ใช้งานเป็นรายไตรมาส*
- Weakened, so wrong: *บริษัทอาจพิจารณาสอบทานสิทธิ์การเข้าถึง...*

When the author's own term outruns the evidence in the source — `material weakness` where the facts describe a `control deficiency` — translate the term as written and raise it as an [overstatement note](#output-shape). The severity call belongs to the auditor, so when it is close, note it and let the author decide rather than passing silently.

## Dates and numbers

Fixed conventions. Apply them without asking.

- **Years are พ.ศ.** — 2025 → 2568, November 2024 → พฤศจิกายน 2567, FY2025 → ปีบัญชี 2568.
- **Months** spell out in prose (30 มิถุนายน 2568), abbreviate inside tables (30 มิ.ย. 2568).
- **Digits stay Arabic.** 47 user IDs stays 47.
- **Currency is `บาท`**, written after the figure — THB 500,000 → 500,000 บาท.
- **Frequencies:** quarterly → เป็นรายไตรมาส · semi-annually → เป็นรายครึ่งปี · annually → เป็นรายปี · monthly → เป็นรายเดือน.

If the source omits a year, omit it in the Thai too. Do not infer one.

## Register

**Self-reference is always `PwC` or `ทีมงาน PwC`.** The phrase `ฝ่ายตรวจสอบภายใน` names the client's own department — reserve it for that, and when the source is ambiguous about which one it means, flag it as an [open question](#output-shape). PwC's own service-line name is the exception: `Internal Audit Services` in a byline is `สายงานบริการตรวจสอบภายใน PwC`.

| | `report` | `message` |
|---|---|---|
| Sentence-final particle | none | ครับ |
| Subject | PwC / ทีมงาน PwC, or drop the subject entirely | ทีมงาน PwC |
| Opening | none — start on the substance | เรียน คุณ… |
| Register | ภาษาเขียนทางการ | สุภาพ เป็นกันเองเล็กน้อย |

A sentence that would read as blame in Thai is written subject-first about the *process*, not the person: `พบว่ากระบวนการอนุมัติ...` rather than `ฝ่ายจัดซื้อไม่ได้อนุมัติ...`.

**Exception — a `Cause` section.** Its whole job is naming the accountable party, so keep the role exactly as written. De-blame through the verb only: `ผู้จัดการฝ่าย IT ไม่ได้กำหนดรอบการสอบทาน`, never `ล้มเหลวในการ` and never an agentless rewrite that deletes who is answerable.

## Output shape

Notes come first, as plain lines, and only when they apply:

- `⚠️ ระดับความรุนแรง:` the author's term reads stronger or weaker than the evidence in the source supports.
- `ℹ️ ตีความว่า:` an ambiguity was resolved by assumption — state which reading was taken.
- `❓ รอยืนยัน:` a rival reading would change the severity or who is accountable. Translate under the likelier reading, then say which span and what the author must confirm before this ships.

The notes are the only place you speak to the author, so write them in your normal conversational voice. Inside the fence, never.

Then the Thai — **when the source is a file**, written to `<name>.th.md` beside it with that path printed, otherwise inside one fenced block. Nothing wraps it: no preamble, no closing remark, no restating the English.
