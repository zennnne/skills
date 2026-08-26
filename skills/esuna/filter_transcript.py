"""Condense a Claude Code transcript into the signals a retrospective needs.

Usage:
  python filter_transcript.py <transcript.jsonl>            condense one session
  python filter_transcript.py <transcript.jsonl> --row N     print row N in full
  python filter_transcript.py <path> --row N --tail          ... last 2000 chars only
  python filter_transcript.py <transcript.jsonl> --context   measured window report
  python filter_transcript.py --day <YYYY-MM-DD> [more...]   list those days' sessions
  python filter_transcript.py --day <YYYY-MM-DD..YYYY-MM-DD> list a range of days
  python filter_transcript.py --help                         print that list

Condensing emits an interleaved timeline of turns and tool calls, each row
carrying the time elapsed since the row before it, followed by per-tool totals.
Full transcripts run from tens of KB into the megabytes; most of that bulk is
conversation, so the timeline keeps every turn but truncates each one. --row
prints one row untruncated, which is how you open the raw record without
wading through megabytes of single-line JSON.

A call costs what it sends plus what it gets back, both in estimated tokens
rather than characters. The input side is the half that gets forgotten and
usually the larger one: a Write charged for its result alone prints as 48tok
and sorts last, when the file it wrote is the biggest thing in the window.
An image result is base64 in the transcript, so its character count overstates
its cost by two orders of magnitude. Its real size only arrives if the harness
announced the displayed dimensions, which happens for about one image in ten;
the rest are priced at the cap, where every announced image lands anyway.

Listing scans ~/.claude/projects/*/*.jsonl and prints, per session that started
on a given day: local start and end time, duration, project, path, tool-call
count, and the first thing the user asked for. A session starting within a
minute of a previous session's end in the same project is marked (cont.):
those are one episode split across a boundary, not alternatives to pick between.
"""
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Windows consoles default to cp1252, which cannot encode non-ASCII text or the
# ellipsis this script emits.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MAX_VALUE_CHARS = 80
MAX_TURN_CHARS = 400

# The keys that carry the decision a row made - the shell script, the brief a
# subagent was dispatched with. Clipping these to MAX_VALUE_CHARS spends the
# budget on a leading `cd` and hides the only thing worth reading.
WIDE_KEYS = {"command", "prompt", "content", "new_string", "old_string"}
MAX_WIDE_CHARS = 300

# A path identifies itself at its end - the filename - and shares its head with
# every other path in the project. Clipping the tail off leaves rows that write
# different files looking identical, so these clip from the middle instead.
PATH_KEYS = {"file_path", "path", "notebook_path", "filePath"}

# Sessions this far apart in one project are one episode split across a
# boundary rather than two separate asks.
CONTINUATION_SECONDS = 90

# One task fits in this much context. Not a session and not a turn - see the
# skill's step 2.
CONTEXT_BUDGET = 150_000

CHARS_PER_TOKEN = 4
IMAGE_PIXELS_PER_TOKEN = 750
IMAGE_TOKEN_CAP = 1600
# An image whose dimensions never arrived. Around nine in ten images are this
# case, and every one of the 86 that did report dimensions across 239 local
# transcripts priced out at the cap - so the cap is the honest guess, and 1000
# only made the same screenshot cost less when the harness said less about it.
IMAGE_TOKENS_UNKNOWN = IMAGE_TOKEN_CAP


def clip(text, limit):
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + "…"


def clip_path(text, limit):
    """Keep both ends of a path, dropping the middle."""
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    tail = max(limit // 2, limit - 30)
    return text[:limit - tail] + "…" + text[-tail:]


def strip_cd(command):
    """Drop a leading `cd <path> &&` so the budget lands on the real command."""
    stripped = command.lstrip()
    if not stripped.startswith("cd "):
        return command
    marker = stripped.find("&&")
    return stripped[marker + 2:].lstrip() if marker != -1 else command


def describe_input(value):
    """Render every key of a tool input, clipping values rather than the whole.

    Clipping the serialised input as one string spends the whole budget on
    whichever key sorts first and drops the rest, which is how flags like
    run_in_background or a git pathspec disappear from the timeline.
    """
    if not isinstance(value, dict):
        return clip(value, MAX_VALUE_CHARS)
    parts = []
    for key, raw in value.items():
        text = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False)
        if key == "command" and isinstance(raw, str):
            text = strip_cd(text)
        limit = MAX_WIDE_CHARS if key in WIDE_KEYS else MAX_VALUE_CHARS
        shorten = clip_path if key in PATH_KEYS else clip
        parts.append(f"{key}={shorten(text, limit)}")
    return "  ".join(parts)


def context_size(entry):
    """The context window the API saw for this entry, in real tokens.

    Every assistant entry carries the usage the API reported. Summed, its three
    input fields are the exact size of the window at that moment - the only
    measured number in the transcript, and the one a context-bloat
    retrospective is actually about.
    """
    usage = (entry.get("message") or {}).get("usage")
    if not isinstance(usage, dict) or entry.get("isSidechain"):
        return None
    total = (usage.get("input_tokens", 0)
             + usage.get("cache_read_input_tokens", 0)
             + usage.get("cache_creation_input_tokens", 0))
    return total or None


def blocks(entry):
    message = entry.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return content if isinstance(content, list) else []


def parse_time(entry):
    stamp = entry.get("timestamp")
    if not stamp:
        return None
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def local(moment):
    return moment.astimezone().strftime("%H:%M:%S")


def local_end(start, end):
    """Clock time, dated when the session ran past midnight.

    A session resumed the next day ends at an earlier clock time than it
    started, which reads as a broken timestamp unless the date is shown.
    """
    start, end = start.astimezone(), end.astimezone()
    if start.date() == end.date():
        return local(end)
    return end.strftime("%d %b %H:%M:%S")


def gap(previous, moment):
    if previous is None or moment is None:
        return "      "
    seconds = (moment - previous).total_seconds()
    if seconds < 60:
        return f"{seconds:5.1f}s"
    if seconds < 3600:
        return f"{seconds / 60:5.1f}m"
    return f"{seconds / 3600:5.1f}h"


def read_entries(path):
    if not Path(path).is_file():
        sys.exit(f"no transcript at {path}\n"
                 "List a day with --day YYYY-MM-DD to get the path to copy.")
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


# --- harness plumbing -------------------------------------------------------
#
# A user turn wrapped in angle brackets was written by the harness, not by the
# human - except for the slash command the human typed, which is the highest
# signal turn in the file. Dropping the whole class takes that with it, along
# with the recalled memory files a No-ops candidate is built from.

def unwrap(tag, text):
    open_tag, close_tag = f"<{tag}>", f"</{tag}>"
    start = text.find(open_tag)
    if start == -1:
        return None
    end = text.find(close_tag, start)
    if end == -1:
        return None
    return text[start + len(open_tag):end].strip()


# Text the harness writes into a user turn without wrapping it in a tag. It is
# addressed to the agent, so billing it to the human hides who said what.
HARNESS_PREFIXES = (
    "Base directory for this skill:",
    "Your claude.ai usage limit",
    "[Request interrupted",
    "This session is being continued from a previous conversation",
    "Caveat: The messages below were generated by the user while running",
)


def classify_harness_text(text):
    """Return (speaker, text) for a bracketed user block, or None to drop it."""
    name = unwrap("command-name", text)
    if name:
        args = unwrap("command-args", text) or ""
        return "user", f"{name} {args}".strip()

    reminder = unwrap("system-reminder", text)
    if reminder:
        # Steering that arrived mid-session: memory files, CLAUDE.md, skill
        # rules. A No-ops candidate is made of exactly these.
        if ".md" in reminder or "memory" in reminder.lower():
            return "sys", clip(reminder, MAX_TURN_CHARS)
        return None

    if text.startswith("<local-command-stdout>") or text.startswith("<local-command-caveat>"):
        return None
    return "sys", clip(text, MAX_TURN_CHARS)


def image_tokens(dimensions):
    if not dimensions:
        return IMAGE_TOKENS_UNKNOWN
    width, height = dimensions
    return min(IMAGE_TOKEN_CAP, max(1, (width * height) // IMAGE_PIXELS_PER_TOKEN))


def parse_image_notice(text):
    """Pull the displayed dimensions out of `[Image: original AxB, displayed at CxD…]`."""
    if not text.startswith("[Image:"):
        return None
    marker = "displayed at "
    start = text.find(marker)
    if start == -1:
        return None
    piece = text[start + len(marker):].split(".")[0].split(",")[0].strip()
    try:
        width, height = piece.split("x")
        return int(width), int(height)
    except ValueError:
        return None


def measure_input(value):
    """Cost of one tool input, in estimated tokens.

    A Write's content and a Bash heredoc enter the window exactly as a result
    does. Charging the result alone prints a 40,000-character file write as
    48tok and sorts the session's largest cost to the bottom of the totals -
    which points a context-bloat retrospective at whatever tool happened to
    return the most text.
    """
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return len(text) // CHARS_PER_TOKEN


def measure_result(block):
    """Cost of one tool result, in estimated tokens, plus whether it is an image."""
    content = block.get("content")
    if isinstance(content, list):
        images = [item for item in content
                  if isinstance(item, dict) and item.get("type") == "image"]
        if images:
            return {"images": len(images), "tokens": 0, "text": "", "pending": True}
    text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
    return {"images": 0, "tokens": len(text) // CHARS_PER_TOKEN, "text": text,
            "pending": False}


def build(path, keep_text=False):
    """Walk the transcript once, returning the timeline rows and their results."""
    rows = []
    results = {}
    prompts = []
    awaiting_dimensions = []

    for entry in read_entries(path):
        role = (entry.get("message") or {}).get("role")
        moment = parse_time(entry)
        side = "»" if entry.get("isSidechain") else " "
        ctx = context_size(entry)

        if entry.get("type") == "last-prompt":
            prompt = entry.get("lastPrompt", "").strip()
            if prompt and prompt not in prompts:
                prompts.append(prompt)
            continue

        for block in blocks(entry):
            if not isinstance(block, dict):
                continue
            kind = block.get("type")

            if kind == "tool_use":
                rows.append({"kind": "call", "time": moment, "side": side, "ctx": ctx,
                             "id": block.get("id"), "name": block.get("name", "?"),
                             "in_tokens": measure_input(block.get("input", {})),
                             "input": describe_input(block.get("input", {})),
                             "raw_input": block.get("input", {})})
            elif kind == "tool_result":
                measured = measure_result(block)
                if not keep_text:
                    measured["text"] = ""
                measured["error"] = bool(block.get("is_error"))
                results[block.get("tool_use_id")] = measured
                if measured["pending"]:
                    awaiting_dimensions.append(measured)
            elif kind == "text" and block.get("text", "").strip():
                text = block["text"].strip()

                dimensions = parse_image_notice(text)
                if dimensions is not None and awaiting_dimensions:
                    # The harness announces an image's displayed size in the
                    # turn after the read that produced it. That size, not the
                    # base64 length, is what the model paid for.
                    awaiting_dimensions.pop(0)["tokens"] = image_tokens(dimensions)
                    continue

                speaker = role
                if role == "user" and text.startswith("<"):
                    classified = classify_harness_text(text)
                    if classified is None:
                        continue
                    speaker, text = classified
                elif text.startswith("[Image:"):
                    continue
                elif role == "user" and text.startswith(HARNESS_PREFIXES):
                    speaker = "sys"

                rows.append({"kind": speaker or "text", "time": moment, "side": side,
                             "ctx": ctx,
                             "text": text if keep_text else clip(text, MAX_TURN_CHARS),
                             "full": text})

    for measured in awaiting_dimensions:
        if measured["tokens"] == 0:
            measured["tokens"] = measured["images"] * IMAGE_TOKENS_UNKNOWN

    return rows, results, prompts


SPEAKERS = {"user": "USER", "assistant": "ASST", "sys": "SYS "}


def condense(path):
    rows, results, prompts = build(path)
    calls = [row for row in rows if row["kind"] == "call"]
    span = sorted(row["time"] for row in rows if row["time"])

    print(f"# {path}")
    if span:
        print(f"# {local(span[0])} - {local_end(span[0], span[-1])} local, "
              f"{(span[-1] - span[0]).total_seconds() / 60:.0f} min")
    print(f"# {len(calls)} tool calls, {len(rows) - len(calls)} turns")

    marks = checkpoints(rows)
    if marks:
        peak_row, peak = max(marks, key=lambda mark: mark[1])
        over = " OVER BUDGET" if peak > CONTEXT_BUDGET else ""
        print(f"# context: {marks[0][1]:,} at the first call, peaking at {peak:,} "
              f"at row {peak_row}{over}  (`--context` for the breakdown)")

    sidechains = sum(1 for row in calls if row["side"] == "»")
    if sidechains:
        print(f"# {sidechains} of those calls ran in a sidechain (subagent)")

    if prompts:
        print("\n## What the user asked\n")
        for prompt in prompts:
            print(f"- {clip(prompt, MAX_TURN_CHARS)}")

    print("\n## Timeline\n")
    print("The gap column is time since the row above. A long gap on a user row"
          " is the human away, not the agent working.")
    print("USER rows are the human. SYS rows are the harness. A call's cost is"
          " its input plus its result,\nboth in estimated tokens - a Write pays"
          " for the file it writes; img marks an image result.")
    print("Re-run with `--row N` to print any row untruncated.\n")

    totals = defaultdict(lambda: {"calls": 0, "sent": 0, "back": 0,
                                  "images": 0, "errors": 0})
    previous = None
    for index, row in enumerate(rows, 1):
        elapsed = gap(previous, row["time"])
        previous = row["time"] or previous

        if row["kind"] == "call":
            result = results.get(row["id"], {"tokens": 0, "images": 0, "error": False})
            flag = " ERROR" if result["error"] else ""
            mark = f" {result['images']}img" if result["images"] else "     "
            cost = row["in_tokens"] + result["tokens"]
            print(f"{index:>3}.{row['side']}{elapsed} {row['name']:<22} "
                  f"{cost:>7}tok{mark}{flag}  {row['input']}")
            bucket = totals[row["name"]]
            bucket["calls"] += 1
            bucket["sent"] += row["in_tokens"]
            bucket["back"] += result["tokens"]
            bucket["images"] += result["images"]
            bucket["errors"] += int(result["error"])
        else:
            speaker = SPEAKERS.get(row["kind"], "TEXT")
            print(f"{index:>3}.{row['side']}{elapsed} {speaker}: {row['text']}")

    print("\n## Totals\n")
    print("~sent is what the agent put into the window (file contents, scripts,"
          " subagent briefs);\n~back is what came out of the tool. A tool heavy"
          " on ~sent is streamlined by writing less,\nnot by calling it less.\n")
    print(f"{'tool':<24} {'calls':>6} {'~sent':>10} {'~back':>10} "
          f"{'~total':>10} {'images':>7} {'errors':>7}")
    for name, bucket in sorted(totals.items(),
                               key=lambda item: -(item[1]["sent"] + item[1]["back"])):
        print(f"{name:<24} {bucket['calls']:>6} {bucket['sent']:>10} "
              f"{bucket['back']:>10} {bucket['sent'] + bucket['back']:>10} "
              f"{bucket['images']:>7} {bucket['errors']:>7}")


def checkpoints(rows):
    """(row number, context size) each time the measured window changed."""
    marks = []
    for index, row in enumerate(rows, 1):
        size = row.get("ctx")
        if size and (not marks or size != marks[-1][1]):
            marks.append((index, size))
    return marks


def describe_rows(rows, start, stop):
    """Name the calls between two checkpoints - what grew the window."""
    names = defaultdict(int)
    for row in rows[start:stop]:
        if row["kind"] == "call":
            names[row["name"]] += 1
    if not names:
        return "conversation"
    ranked = sorted(names.items(), key=lambda item: -item[1])
    return ", ".join(f"{count}x {name}" if count > 1 else name
                     for name, count in ranked[:3])


def context_report(path):
    rows, _, _ = build(path)
    marks = checkpoints(rows)

    print(f"# {path}\n")
    if not marks:
        print("# no usage data in this transcript - nothing measured to report")
        return

    baseline = marks[0][1]
    peak_row, peak = max(marks, key=lambda mark: mark[1])
    final = marks[-1][1]

    print("## Context\n")
    print(f"baseline  {baseline:>9,}   before the first tool call: system prompt,"
          " steering files, memory, tool definitions")
    print(f"peak      {peak:>9,}   at row {peak_row}")
    print(f"final     {final:>9,}")
    print(f"budget    {CONTEXT_BUDGET:>9,}   per task, and a transcript can hold"
          " more than one - find the task boundaries before reading the verdict")

    crossing = next((mark for mark in marks if mark[1] > CONTEXT_BUDGET), None)
    print()
    if crossing:
        index = marks.index(crossing)
        before = marks[index - 1] if index else (0, baseline)
        print(f"Crossed {CONTEXT_BUDGET:,} at row {crossing[0]} "
              f"({before[1]:,} -> {crossing[1]:,}), "
              f"{len(marks) - index} of {len(marks)} steps still to run.")
        print(f"Over budget by {peak - CONTEXT_BUDGET:,} at its worst.")
    else:
        print(f"This transcript stayed under {CONTEXT_BUDGET:,} throughout, peaking"
              f" at {peak * 100 // CONTEXT_BUDGET}% of budget. A transcript holding two"
              " tasks stays under it while both of them are cramped.")

    print("\n## Biggest jumps\n")
    print("Each jump is what the rows named added to the window.\n"
          "Open them with `--row N`.\n")
    jumps = []
    previous = (0, baseline)
    for mark in marks[1:]:
        jumps.append((mark[1] - previous[1], previous[0], mark[0]))
        previous = mark
    for size, start, stop in sorted(jumps, reverse=True)[:8]:
        if size <= 0:
            continue
        # A checkpoint row reports the window as it stood *before* that row's
        # own input and result entered it, so the growth measured at the next
        # checkpoint was caused by the checkpoint row itself and the rows after
        # it - not by the checkpoint that closes the interval. Naming the
        # closing row instead credits every large Write to whatever cheap call
        # happened to follow it.
        first = max(1, start)
        last = max(first, stop - 1)
        span = f"{first}" if first == last else f"{first}-{last}"
        print(f"+{size:>8,}  rows {span:<9}  {describe_rows(rows, first - 1, last)}")


def show_row(path, number, tail=0):
    rows, results, _ = build(path, keep_text=True)
    if not 1 <= number <= len(rows):
        sys.exit(f"row {number} is out of range: this transcript has {len(rows)} rows")

    row = rows[number - 1]
    print(f"# row {number} of {len(rows)} in {path}")
    if row["time"]:
        print(f"# {local(row['time'])} local")

    if row["kind"] != "call":
        print(f"# {SPEAKERS.get(row['kind'], 'TEXT')}\n")
        print(row["full"])
        return

    result = results.get(row["id"], {})
    print(f"# {row['name']}{'  ERROR' if result.get('error') else ''}\n")
    print("## Input\n")
    written = json.dumps(row["raw_input"], ensure_ascii=False, indent=2)
    if tail and len(written) > tail:
        print(f"[{len(written) - tail} chars of input omitted]")
        written = written[:tail]
    print(written)
    print("\n## Result\n")
    if result.get("images"):
        print(f"[{result['images']} image(s), ~{result['tokens']} tokens]")
    text = result.get("text", "")
    if tail and len(text) > tail:
        print(f"[first {len(text) - tail} chars omitted; --row alone prints all]")
        text = text[-tail:]
    print(text)


def first_moment(path):
    """The first timestamp in a transcript, read without parsing the whole file."""
    for entry in read_entries(path):
        moment = parse_time(entry)
        if moment:
            return moment
    return None


def summarise(path):
    start = end = None
    calls = 0
    opening = ""
    prompt = ""

    for entry in read_entries(path):
        moment = parse_time(entry)
        if moment:
            start = moment if start is None else min(start, moment)
            # Resumed and sidechain entries are not in file order, so the last
            # timestamp in the file is not the latest one.
            end = moment if end is None else max(end, moment)

        # last-prompt records what the human typed, slash command and all - the
        # only place the raw ask survives once the harness has expanded it, so
        # it outranks whatever text block happened to come first.
        if entry.get("type") == "last-prompt" and not prompt:
            prompt = clip(entry.get("lastPrompt", ""), 120)

        for block in blocks(entry):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                calls += 1
            elif (not opening and block.get("type") == "text"
                  and (entry.get("message") or {}).get("role") == "user"):
                text = block.get("text", "").strip()
                if text.startswith("<"):
                    classified = classify_harness_text(text)
                    if classified and classified[0] == "user":
                        opening = clip(classified[1], 120)
                elif text and not text.startswith(HARNESS_PREFIXES):
                    opening = clip(text, 120)

    return {"path": path, "start": start, "end": end, "calls": calls,
            "opening": prompt or opening}


def expand_days(arguments):
    days = []
    for argument in arguments:
        if ".." in argument:
            first, last = argument.split("..", 1)
            try:
                cursor = datetime.strptime(first, "%Y-%m-%d")
                stop = datetime.strptime(last, "%Y-%m-%d")
            except ValueError:
                sys.exit(f"not a date range: {argument}")
            while cursor <= stop:
                days.append(cursor.strftime("%Y-%m-%d"))
                cursor += timedelta(days=1)
        else:
            days.append(argument)
    return days


def list_days(arguments):
    days = set(expand_days(arguments))
    root = Path.home() / ".claude" / "projects"
    found = []
    for path in root.glob("*/*.jsonl"):
        try:
            # The first timestamp already decides whether the file is in scope,
            # so most transcripts never get parsed past their opening line.
            moment = first_moment(path)
            if not moment or moment.astimezone().strftime("%Y-%m-%d") not in days:
                continue
            info = summarise(path)
        except OSError:
            continue
        if info["start"]:
            found.append(info)

    label = ", ".join(sorted(days))
    if not found:
        print(f"# no session in {root} started on {label}")
        return

    print(f"# {len(found)} sessions on {label}\n")
    print("# (cont.) marks a session that began moments after the previous one"
          " in the same project:\n# one episode split across a boundary, not a"
          " separate ask.\n")

    previous_end = {}
    current_day = None
    for info in sorted(found, key=lambda item: item["start"]):
        path = Path(info["path"])
        project = path.parent.name

        # Rows carry a clock time only, so across a range the day a session
        # belongs to is otherwise recoverable only by watching the clock wrap
        # backwards. The weekday is here because the user names sessions
        # relative to today ("last Saturday"), never by date.
        day = info["start"].astimezone()
        if day.strftime("%Y-%m-%d") != current_day:
            current_day = day.strftime("%Y-%m-%d")
            print(f"## {current_day} ({day.strftime('%A')})\n")
        minutes = (info["end"] - info["start"]).total_seconds() / 60
        earlier = previous_end.get(project)
        carry = ""
        if earlier and 0 <= (info["start"] - earlier).total_seconds() <= CONTINUATION_SECONDS:
            carry = "  (cont.)"
        previous_end[project] = info["end"]

        print(f"{local(info['start'])}-{local_end(info['start'], info['end'])}  {minutes:>5.0f} min  "
              f"{info['calls']:>4} calls  {project}{carry}")
        print(f"    {path}")
        print(f"    {info['opening'] or '(no user prompt found)'}\n")


USAGE = ("usage: python filter_transcript.py <transcript.jsonl>"
         "               condense one session\n"
         "       python filter_transcript.py <transcript.jsonl> --row N"
         "       print row N in full\n"
         "       python filter_transcript.py <transcript.jsonl> --row N --tail"
         "  ... last 2000 chars of the result\n"
         "       python filter_transcript.py <transcript.jsonl> --context"
         "       measured window report\n"
         "       python filter_transcript.py --day <YYYY-MM-DD>[..<YYYY-MM-DD>]"
         " [more days]  list sessions\n"
         "\nThose are every mode there is.")

if __name__ == "__main__":
    arguments = sys.argv[1:]
    # Without this, a mistyped or invented flag is opened as a transcript path
    # and the run ends in a FileNotFoundError traceback.
    if not arguments or arguments[0] in ("--help", "-h", "help"):
        print(USAGE)
        sys.exit(0)
    if arguments[0].startswith("-") and arguments[0] != "--day":
        sys.exit(f"unknown flag: {arguments[0]}\n\n{USAGE}")
    if arguments[0] == "--day" and len(arguments) == 1:
        sys.exit(f"--day takes at least one YYYY-MM-DD\n\n{USAGE}")
    if arguments and arguments[0] == "--day" and len(arguments) > 1:
        list_days(arguments[1:])
    elif len(arguments) == 2 and arguments[1] == "--context":
        context_report(arguments[0])
    elif len(arguments) in (3, 4) and arguments[1] == "--row":
        if len(arguments) == 4 and arguments[3] != "--tail":
            sys.exit(f"unknown flag: {arguments[3]}\n\n{USAGE}")
        try:
            show_row(arguments[0], int(arguments[2]),
                     tail=2000 if len(arguments) == 4 else 0)
        except ValueError:
            sys.exit("--row takes a row number")
    elif len(arguments) == 1:
        condense(arguments[0])
    else:
        sys.exit(USAGE)
