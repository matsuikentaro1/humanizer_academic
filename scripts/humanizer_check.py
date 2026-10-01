#!/usr/bin/env python3
"""
humanizer_check.py - mechanical checks for the humanizer_academic skill.

Counts what a language model counts badly: words per sentence, em dashes,
curly quotes, repeated openers, and numbers that appear in the revision but
not in the original. Standard library only. Always exits 0.

Usage:
    python humanizer_check.py revised.txt
    python humanizer_check.py revised.txt --original original.txt
    python humanizer_check.py < revised.txt

A single stream can carry both texts when it contains the two marker lines:
    ===ORIGINAL===
    (original text)
    ===REVISED===
    (revised text)

The word list reports candidates to read in context. It does not report
violations, and the script gives no score.
"""

import argparse
import io
import re
import sys

ORIGINAL_MARK = "===ORIGINAL==="
REVISED_MARK = "===REVISED==="

# A period after these does not end a sentence.
ABBREVIATIONS = {
    "e.g", "i.e", "et al", "vs", "cf", "fig", "figs", "eq", "eqs", "ref", "refs",
    "no", "nos", "dr", "prof", "mr", "mrs", "ms", "st", "approx", "ca", "resp",
    "inc", "ltd", "co", "jr", "sr", "vol", "pp", "p", "al", "etc", "viz",
}

# Words and phrases that the skill's patterns name. Reported as candidates only.
CANDIDATES = [
    (r"\bdelv(?:e|es|ed|ing)\b", "Pattern 7"),
    (r"\btapestry\b", "Pattern 7"),
    (r"\btestament\b", "Pattern 1/7"),
    (r"\bpivotal\b", "Pattern 1/7"),
    (r"\bmultifaceted\b", "Pattern 7"),
    (r"\bintrica(?:te|cies|cy)\b", "Pattern 7"),
    (r"\binterplay\b", "Pattern 7"),
    (r"\b(?:evolving )?landscape\b", "Pattern 1/7"),
    (r"\bshowcas(?:e|es|ed|ing)\b", "Pattern 4/7"),
    (r"\bunderscor(?:e|es|ed|ing)\b", "Pattern 1/3/7"),
    (r"\bfoster(?:s|ed|ing)?\b", "Pattern 7"),
    (r"\bgarner(?:s|ed|ing)?\b", "Pattern 7"),
    (r"\bholistic\b", "Pattern 7"),
    (r"\bvibrant\b", "Pattern 4/7"),
    (r"\bgroundbreaking\b", "Pattern 4"),
    (r"\b(?:serves?|served|serving|stands?|stood|standing) as\b", "Pattern 8"),
    (r",\s+(?:highlighting|emphasizing|reflecting|symbolizing)\b", "Pattern 3"),
    (r"\b(?:markedly|remarkably|strikingly|dramatically|profoundly)\b", "Pattern 29"),
    (r"\blinked to\b", "Pattern 19"),
    (r"(?:^|(?<=[.!?]\s))Beyond\b", "Pattern 20"),
    (r"\bvia\b", "Pattern 21"),
    (r"\byield(?:s|ed|ing)?\b", "Pattern 25"),
    (r"\b(?:In other words|Put differently|To put it another way|Simply put)\b", "Pattern 32"),
    (r"\bIn order to\b", "Pattern 16"),
    (r"\bDue to the fact that\b", "Pattern 16"),
    (r"\bIt is important to note that\b", "Pattern 16"),
]

NUMBER = re.compile(r"(?<![A-Za-z])\d+(?:[.,]\d+)*")


def read_text(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def split_stream(text):
    """Return (original, revised) from a stream that may carry both."""
    if REVISED_MARK not in text:
        return None, text
    before, revised = text.split(REVISED_MARK, 1)
    original = before.split(ORIGINAL_MARK, 1)[1] if ORIGINAL_MARK in before else before
    return original, revised


def paragraphs(text):
    """Yield prose paragraphs, skipping headings, tables, and code blocks."""
    block, fenced = [], False
    for raw in text.replace("\r\n", "\n").split("\n") + [""]:
        line = raw.strip()
        if line.startswith("```"):
            fenced = not fenced
            line = ""
        if fenced:
            continue
        line = re.sub(r"^>\s?", "", line)
        if not line or line.startswith("#") or line.startswith("|"):
            if block:
                yield " ".join(block)
                block = []
            continue
        line = re.sub(r"^(?:[-*+]|\d+[.)])\s+", "", line)
        block.append(line)


def sentences(paragraph):
    """Split a paragraph into sentences, tolerating common abbreviations."""
    result, start = [], 0
    for match in re.finditer(r"[.!?][\"')\]]*\s+(?=[\"'(\[]?[A-Z0-9])", paragraph):
        head = paragraph[start:match.start()]
        last = re.split(r"[\s(]", head)[-1].lower().rstrip(".")
        two = " ".join(re.split(r"\s", head)[-2:]).lower().rstrip(".")
        if paragraph[match.start()] == "." and (
            last in ABBREVIATIONS or two in ABBREVIATIONS or re.fullmatch(r"[a-z]", last)
        ):
            continue
        result.append(paragraph[start:match.end()].strip())
        start = match.end()
    tail = paragraph[start:].strip()
    if tail:
        result.append(tail)
    return result


def word_count(sentence):
    return len(sentence.split())


def first_word(sentence):
    match = re.match(r"[\"'(\[]*([A-Za-z][A-Za-z'-]*)", sentence)
    return match.group(1).lower() if match else ""


def snippet(text, width=70):
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 3] + "..."


def normalize_number(token):
    token = token.rstrip(".,")
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", token):
        token = token.replace(",", "")
    return token


def numbers(text):
    return {normalize_number(m.group(0)) for m in NUMBER.finditer(text)}


def check(revised, original=None):
    out = []
    paras = list(paragraphs(revised))
    prose = "\n".join(paras)

    # 1. Em dashes and curly quotes: the rules allow none.
    dash_hits = [p for p in paras if "—" in p]
    out.append(f"Em dashes: {prose.count(chr(0x2014))}")
    for p in dash_hits:
        for m in re.finditer("—", p):
            out.append(f"  - {snippet(p[max(0, m.start() - 35): m.end() + 35])}")
    curly = len(re.findall("[“”‘’]", prose))
    out.append(f"Curly quotes: {curly}")

    # 2. Sentence rhythm (Pattern 34): all sentences within a 5-word range.
    out.append("")
    out.append("Sentence lengths by paragraph (words):")
    uniform = 0
    para_sentences = []
    for index, p in enumerate(paras, 1):
        sents = sentences(p)
        para_sentences.append(sents)
        counts = [word_count(s) for s in sents]
        flag = ""
        if len(counts) >= 3 and max(counts) - min(counts) <= 5:
            flag = "  <- too uniform (all within a 5-word range)"
            uniform += 1
        listing = ", ".join(str(c) for c in counts)
        out.append(f"  P{index} [{listing}]{flag}  {snippet(p, 45)}")
    out.append(f"Paragraphs that fail the rhythm criterion: {uniform}")

    # 3. Repeated openers.
    out.append("")
    opener_lines = []
    for index, sents in enumerate(para_sentences, 1):
        firsts = [first_word(s) for s in sents]
        for i in range(len(firsts) - 2):
            if firsts[i] and firsts[i] == firsts[i + 1] == firsts[i + 2]:
                opener_lines.append(
                    f"  - P{index}: sentences {i + 1}-{i + 3} all open with \"{firsts[i].capitalize()}\""
                )
                break
        extra = len(re.findall(r"\bAdditionally\b", " ".join(sents)))
        if extra > 1:
            opener_lines.append(f"  - P{index}: \"Additionally\" appears {extra} times (allowed once)")
    out.append(f"Repeated openers: {len(opener_lines)}")
    out.extend(opener_lines)

    # 4. Numbers (fidelity check).
    if original is not None:
        out.append("")
        before, after = numbers(original), numbers(revised)
        added = sorted(after - before)
        dropped = sorted(before - after)
        out.append(f"Numbers in the revision that are not in the original: {len(added)}")
        if added:
            out.append("  " + ", ".join(added))
        out.append(f"Numbers in the original that are missing from the revision: {len(dropped)}")
        if dropped:
            out.append("  " + ", ".join(dropped))

    # 5. Candidate words.
    out.append("")
    found = []
    for pattern, label in CANDIDATES:
        for m in re.finditer(pattern, prose):
            found.append(f"  - \"{m.group(0).strip(', ')}\" ({label})")
    out.append(f"Candidate words to read in context (not violations): {len(found)}")
    out.extend(found)

    out.append("")
    out.append("Fix em dashes, curly quotes, and uniform paragraphs.")
    out.append("Check each added number against the original; a number that the original spelled out is fine.")
    out.append("Judge the candidates in context. One revision round is enough.")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Mechanical checks for humanizer_academic.")
    parser.add_argument("file", nargs="?", help="revised text (default: standard input)")
    parser.add_argument("--original", help="original text, for the number comparison")
    args = parser.parse_args()

    try:
        if args.file:
            original, revised = split_stream(read_text(args.file))
        else:
            data = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8-sig").read()
            original, revised = split_stream(data)
        if args.original:
            original = read_text(args.original)
        report = check(revised, original)
    except Exception as error:  # never block the edit on a checker problem
        report = f"humanizer_check could not run ({error}). Do the checks by hand."

    sys.stdout.buffer.write((report + "\n").encode("utf-8"))
    sys.exit(0)


if __name__ == "__main__":
    main()
