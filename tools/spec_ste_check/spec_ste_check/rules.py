"""Pure STE rules over spec text.

The module turns markdown prose into sentences and checks each one
against the mechanical ASD-STE100 rule set. No I/O lives here; the CLI
and the hook import these functions, so the repo holds one rule
authority.
"""

import re
from collections import namedtuple

Sentence = namedtuple("Sentence", ["line", "text"])

_FENCE_MARKERS = ("```", "~~~")
_LIST_RE = re.compile(r"^(?:[-*+]|\d+[.)])\s+")
_BOLD_RE = re.compile(r"\*\*([^*]*)\*\*")
_SPAN_RE = re.compile(r"`[^`]*`")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_NUMBER_UNIT_RE = re.compile(r"\b(\d+(?:[.,]\d+)?)\s+(?=[A-Za-z])")

# Approved STE verbs that start an imperative sentence. A sentence whose
# first word sits here counts against the 20-word cap; every other
# sentence counts against the 25-word cap.
IMPERATIVE_VERBS = frozenset(
    """add ask build change clean clear collect compare complete copy
    create cut delete do draw enter examine exit find finish fix follow
    give hold install join keep list load lock log make map mark merge
    move name note open pick plan print pull push put read record
    register reload remove rename reopen replace report reset run save
    scroll select set sort split start stop switch tell turn update use
    wait walk write""".split()
)

PROCEDURAL_CAP = 20
DESCRIPTIVE_CAP = 25

_CONTRACTION_RE = re.compile(
    r"\b\w+(?:n't|'re|'ve|'ll|'m)\b|\b(?:it|that|there|what|let|who|he|she|one)'s\b",
    re.I,
)
_BANNED_RE = re.compile(
    r"\b(?:performs?|performed|performing|utilizes?|utilized|utilizing"
    r"|ensures?|ensured|ensuring|provides?|provided|providing)\b",
    re.I,
)
_CHECK_RE = re.compile(r"(?<![\w-])checks?\b", re.I)
_PROGRESSIVE_RE = re.compile(r"\b(?:is|are|was|were|be|been|being)\s+\w+ing\b", re.I)
_PERFECT_RE = re.compile(r"\b(?:has|have|had)\s+\w+(?:ed|en)\b", re.I)
_PREV_WORD_RE = re.compile(r"(\w+)\W+$")
_DETERMINERS = frozenset(
    "the a an this that these those another every each no one its his her "
    "their our your my".split()
)
# Attested noun phrases that the determiner heuristic cannot see.
_BANNED_NOUN_ALLOWLIST = frozenset(("network checks", "builder check"))
# Attested adjectival participles that the progressive pattern cannot
# tell from a verb.
_TENSE_ALLOWLIST = frozenset(("is missing", "are missing"))


def prose_sentences(text):
    """Split markdown prose into sentences with their line numbers.

    Headings, blank lines, and fenced blocks give nothing. A sentence
    never crosses a line boundary. A code span becomes one CODE token.
    """
    sentences = []
    in_fence = False
    for lineno, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if stripped.startswith(_FENCE_MARKERS):
            in_fence = not in_fence
            continue
        if in_fence or not stripped or stripped.startswith("#"):
            continue
        line = _LIST_RE.sub("", stripped)
        line = line.lstrip("> ").strip()
        line = _BOLD_RE.sub(r"\1", line)
        line = _SPAN_RE.sub("CODE", line)
        for piece in _SENTENCE_SPLIT_RE.split(line):
            piece = piece.strip()
            if piece:
                sentences.append(Sentence(lineno, piece))
    return sentences


def word_count(sentence_text):
    """Count words: one hyphenated group, one number with its unit, and
    one code element are one word each."""
    joined = _NUMBER_UNIT_RE.sub(r"\1-", sentence_text)
    return len(joined.split())


def is_imperative(sentence_text):
    """Tell an imperative sentence from a descriptive one by its first
    word."""
    tokens = sentence_text.split()
    if not tokens:
        return False
    return tokens[0].lower().strip(",;:.") in IMPERATIVE_VERBS


def check_cap(sentence):
    """Return a sentence-length violation over the cap, or None."""
    cap = PROCEDURAL_CAP if is_imperative(sentence.text) else DESCRIPTIVE_CAP
    if word_count(sentence.text) <= cap:
        return None
    return {
        "rule": "sentence-length",
        "line": sentence.line,
        "severity": "error",
        "text": sentence.text,
    }


def _violation(rule, sentence, severity="error"):
    return {
        "rule": rule,
        "line": sentence.line,
        "severity": severity,
        "text": sentence.text,
    }


def _check_word_hits(sentence):
    """Flag the word `check` only where the neighbors do not mark a
    noun: no determiner before it, and no allowlisted phrase."""
    hits = []
    text = sentence.text
    for match in _CHECK_RE.finditer(text):
        word = match.group(0).lower()
        prev = _PREV_WORD_RE.search(text[: match.start()])
        prev_word = prev.group(1).lower() if prev else ""
        if prev_word in _DETERMINERS:
            continue
        if f"{prev_word} {word}" in _BANNED_NOUN_ALLOWLIST:
            continue
        hits.append(_violation("banned-word", sentence))
    return hits


def check_tenses(sentence):
    """Progressive tenses are errors; perfect tenses are warnings. An
    allowlisted adjectival participle stays clean."""
    hits = []
    for match in _PROGRESSIVE_RE.finditer(sentence.text):
        if match.group(0).lower() not in _TENSE_ALLOWLIST:
            hits.append(_violation("progressive-tense", sentence))
            break
    if _PERFECT_RE.search(sentence.text):
        hits.append(_violation("perfect-tense", sentence, severity="warning"))
    return hits


def check_sentence(sentence):
    """Run every rule over one sentence and return its violations."""
    hits = []
    cap = check_cap(sentence)
    if cap:
        hits.append(cap)
    if ";" in sentence.text:
        hits.append(_violation("semicolon", sentence))
    if _CONTRACTION_RE.search(sentence.text):
        hits.append(_violation("contraction", sentence))
    if _BANNED_RE.search(sentence.text):
        hits.append(_violation("banned-word", sentence))
    hits.extend(_check_word_hits(sentence))
    hits.extend(check_tenses(sentence))
    return hits


def check_text(text, filename=""):
    """Run every rule over a text and name the file on each violation."""
    hits = []
    for sentence in prose_sentences(text):
        for violation in check_sentence(sentence):
            hits.append({"file": filename, **violation})
    return hits
