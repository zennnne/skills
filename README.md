# skills

Claude Code skills ที่ผมใช้จริงในงานประจำวัน — เขียนเอง / ปรับจากของคนอื่นจนเข้ามือ

แต่ละสกิลคือโฟลเดอร์ที่มี `SKILL.md` (frontmatter `name` + `description` แล้วตามด้วยขั้นตอน) บางตัวมีไฟล์ `reference.md` / `examples.md` / `templates.md` แยกไว้ให้โหลดตอนต้องใช้จริง

## Install

ก็อปเฉพาะตัวที่อยากใช้ไปวางใน skills directory ของตัวเอง:

```bash
git clone https://github.com/zennnne/skills.git
cp -r skills/skills/deep-research ~/.claude/skills/
```

- **ทั้งเครื่อง** → `~/.claude/skills/<name>/SKILL.md`
- **เฉพาะโปรเจกต์** → `<project>/.claude/skills/<name>/SKILL.md`

Claude จะหยิบมาใช้เองตาม `description` หรือเรียกตรงๆ ด้วย `/<skill-name>` ก็ได้

## Skills

### Coding

| Skill | ทำอะไร |
|---|---|
| [`implement-spec`](skills/implement-spec/SKILL.md) | Implement a specification in code. |
| [`karpathy-guidelines`](skills/karpathy-guidelines/SKILL.md) | Behavioral guidelines to reduce common LLM coding mistakes. |
| [`find-standards`](skills/find-standards/SKILL.md) | Find how this problem is already solved: standards we could adopt, and the industry's best practices. |
| [`flashlight`](skills/flashlight/SKILL.md) | Shine a light into a wayfinder map's fog — work one direction now, out of frontier order, or redraw the map itself. |
| [`grilling-frontend-prototyping`](skills/grilling-frontend-prototyping/SKILL.md) | Converge on a frontend look through rounds of prototypes and grilling verdicts. |
| [`using-git-worktrees`](skills/using-git-worktrees/SKILL.md) | Ensures an isolated workspace exists via native tools or git worktree fallback — ใช้ตอนเริ่มงาน feature ที่ต้องแยกจาก workspace ปัจจุบัน |
| [`finishing-a-development-branch`](skills/finishing-a-development-branch/SKILL.md) | ตอน implement เสร็จ เทสต์ผ่านหมด แล้วต้องตัดสินใจว่าจะ merge / PR / cleanup ยังไง |

### Research & writing

| Skill | ทำอะไร |
|---|---|
| [`deep-research`](skills/deep-research/SKILL.md) | Multi-pass research: สัมภาษณ์เพื่อหุบ scope ก่อน แล้วกระจาย sub-agent ไปขุดแต่ละคำถามย่อยพร้อมกัน จบด้วย synthesis เข้าคลังความรู้ |
| [`extracting-youtube-transcript`](skills/extracting-youtube-transcript/SKILL.md) | ดึง transcript เต็มของคลิป YouTube ผ่าน Playwright MCP (กดปุ่ม Show transcript แล้วอ่าน panel) |
| [`code-story`](skills/code-story/SKILL.md) | Build a wizard-style HTML page that teaches how and why a change works. |
| [`applying-3-act-structure`](skills/applying-3-act-structure/SKILL.md) | ใช้โครง 3 องก์ (Setup / Confrontation / Resolution) วางแผนหรือวินิจฉัยเรื่องเล่า — นิยาย บท คอนเทนต์ |
| [`report-thai-business`](skills/report-thai-business/SKILL.md) | แปลงาน internal-audit / risk จากอังกฤษเป็นไทยแบบที่ผู้บริหารลูกค้ารับได้เลยโดยไม่ต้องแก้ |

### Claude Code housekeeping

สกิลกลุ่มนี้ผูกกับ setup ส่วนตัวของผม (`~/.claude/session_log/YYYY/MM/`, memory layout, plugin marketplace) — เอาไปใช้ได้แต่ต้องแก้ path ให้ตรงกับของตัวเองก่อน

| Skill | ทำอะไร |
|---|---|
| [`auditing-claude-md`](skills/auditing-claude-md/SKILL.md) | ตรวจ CLAUDE.md ที่มีอยู่ แล้วจัดทุกบรรทัดเป็น keep / cut / move-to-skill |
| [`test-a-skill`](skills/test-a-skill/SKILL.md) | เทสต์สกิลภาคสนาม — รันสดใน agent session ที่ไม่มี context แล้วเอาสิ่งที่มันสะดุดมาแก้ |
| [`session-summary`](skills/session-summary/SKILL.md) | เติม placeholder ใน daily session log โดยอ่าน transcript `.jsonl` ของ session นั้นมาสรุป |
| [`session-index`](skills/session-index/SKILL.md) | ทำสารบัญรายเดือน — รวบ title / date / status / จำนวน mistake ของทุก session ในเดือนนั้นเป็นตาราง |
| [`cleaning-sessions`](skills/cleaning-sessions/SKILL.md) | ลบ transcript (JSONL) + โฟลเดอร์ tool-result ที่เก่ากว่า N วัน คืนพื้นที่ดิสก์ |
| [`updating-plugins`](skills/updating-plugins/SKILL.md) | อัปเดต plugin ทุกตัวให้เป็นล่าสุด หา plugin เองจาก `settings.json` |
| [`automating-afk-agent-queues`](skills/automating-afk-agent-queues/SKILL.md) | วิธีต่อ AFK coding agent เข้ากับ task queue ให้ทำงานตาม event แทนการวน idle loop |

## Notes

- สกิลบางตัวมีโฟลเดอร์ `agents/openai.yaml` ติดมาด้วย — เป็น export สำหรับ agent runner อื่น ไม่จำเป็นต่อการใช้กับ Claude Code
- อยากรู้วิธีเขียนสกิลให้ดี แนะนำ [`writing-for-agents`](https://github.com/mattpocock/skills) ของ Matt Pocock

## License

MIT — หยิบไปใช้ ไปแก้ ได้เลย ไม่ต้องขอ
