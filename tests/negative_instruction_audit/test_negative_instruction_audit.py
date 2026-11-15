"""Behavior tests for the negative instruction audit tool."""

import json

import pytest
from negative_instruction_audit import (
    extract_sentences,
    is_negative,
    is_pinned,
    iter_harness_files,
    load_pin_literals,
    main,
    run,
    scan_file,
)

FAKE_REPO_FILES = {
    "CLAUDE.md": "Never guess the path. Build the tool first.\n",
    ".claude/skills/b-skill/SKILL.md": (
        "Do not run two scans at once.\nSome prose sentence here.\n"
    ),
    ".claude/skills/a-skill/SKILL.md": "Avoid silent refactors.\n",
    ".claude/agents/worker.md": "Never push to main alone.\n",
    ".claude/agents/reviewer.md": "Run the gates in order.\n",
    ".claude/hooks/harness-charter.sh": (
        'printf "Never work without a branch\\n"\n'
    ),
    "tests/claude_infra/test_pin.py": (
        'SENTENCE = "Never guess the path."\n'
        'assert "Never guess the path." in text\n'
    ),
}


@pytest.fixture()
def repo(tmp_path):
    for relative, text in FAKE_REPO_FILES.items():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return tmp_path


def test_iter_harness_files_orders_the_surfaces(repo):
    files = iter_harness_files(repo)
    names = [str(path.relative_to(repo)) for path in files]
    assert names[0] == "CLAUDE.md"
    assert "tests/claude_infra/test_pin.py" not in names
    skills = [name for name in names if "skills" in name]
    assert skills == sorted(skills)
    agents = [name for name in names if "agents" in name]
    assert agents == sorted(agents)
    assert any("worker.md" in name for name in names)
    assert any("reviewer.md" in name for name in names)
    assert any("harness-charter.sh" in name for name in names)


def test_iter_harness_files_skips_missing_surfaces(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("x", encoding="utf-8")
    files = iter_harness_files(tmp_path)
    assert [str(path) for path in files] == [str(tmp_path / "CLAUDE.md")]


def test_extract_sentences_joins_wrapped_lines_and_drops_short():
    text = "A first sentence that\nwraps across two physical\nlines. Ok.\n"
    assert extract_sentences(text) == [
        "A first sentence that wraps across two physical lines.",
    ]


def test_extract_sentences_splits_bullets_and_strips_markers():
    text = "- Never guess the path.\n* Do not rush.\n2. Avoid silence.\n3) No new debts.\n"
    assert extract_sentences(text) == [
        "Never guess the path.",
        "Do not rush.",
        "Avoid silence.",
        "No new debts.",
    ]


def test_extract_sentences_drops_code_fences():
    text = "Keep this rule.\n```\nnever = compile()\n```\nEnd here.\n"
    sentences = extract_sentences(text)
    assert not any("compile" in sentence for sentence in sentences)
    assert any("Keep this rule." in sentence for sentence in sentences)


def test_extract_sentences_drops_very_short_lines():
    assert extract_sentences("ok\n") == []


def test_extract_sentences_pins_the_twelve_char_floor():
    assert extract_sentences("x" * 11) == []
    assert extract_sentences("x" * 12) == ["x" * 12]


def test_load_pin_literals_reads_only_long_strings(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    edge = "x" * 20  # exactly MIN_PIN_LEN
    under = "x" * 19
    (tests / "test_pins.py").write_text(
        f'LONG = "a pin literal long enough to count"\n'
        f'EDGE = "{edge}"\n'
        f'UNDER = "{under}"\n'
        f'SHORT = "tiny"\n',
        encoding="utf-8",
    )
    (tests / "test_broken.py").write_text("def (:", encoding="utf-8")
    pins = load_pin_literals(tests)
    assert pins == [
        "a pin literal long enough to count",
        edge,
    ]


def test_is_pinned_matches_in_both_directions():
    pins = ["a pin literal long enough to count"]
    assert is_pinned("text with a pin literal long enough to count here.", pins)
    assert is_pinned("a pin literal long enough to count", pins)
    assert not is_pinned("An unrelated sentence about tools.", pins)


def test_is_negative_covers_the_marker_set():
    assert is_negative("Never guess the path.")
    assert is_negative("we should not do this")
    assert is_negative("Do not rush the scan.")
    assert is_negative("the gate must not open")
    assert is_negative("it cannot run offline")
    assert is_negative("No files were touched.")
    assert is_negative("Avoid silent refactors.")
    assert is_negative("No. is the answer.")
    assert is_negative("Don't guess the path.")
    assert is_negative("The branch shall not merge red.")
    assert not is_negative("Guess the path instead.")
    assert not is_negative("The branch merges green.")
    assert not is_negative("Build the tool first.")
    assert not is_negative("Run the gates in order.")


def test_is_negative_requires_the_sentence_start_for_no():
    assert is_negative("No tests were skipped.")
    assert not is_negative("The run touched no files.")


def test_scan_file_classifies_pinned_and_candidates(repo):
    pins = load_pin_literals(repo / "tests")
    record = scan_file(repo / "CLAUDE.md", pins)
    assert record["path"].endswith("CLAUDE.md")
    assert record["negative"] == 1
    assert record["pinned"] == 1
    assert record["candidates"] == []
    assert record["sentences"] >= 2


def test_run_aggregates_the_totals(repo):
    payload = run(repo)
    assert payload["totals"]["files"] >= 4
    assert payload["totals"]["negative"] >= 3
    assert payload["totals"]["pinned"] >= 1
    assert payload["totals"]["candidates"] == (
        payload["totals"]["negative"] - payload["totals"]["pinned"]
    )


def test_main_prints_the_text_report(repo, capsys):
    code = main(["--repo-root", str(repo)])
    out = capsys.readouterr().out
    assert code == 0
    assert "negative" in out
    assert "[cand   ]" in out or "[pinned ]" in out


def test_main_json_output(repo, capsys):
    code = main(["--repo-root", str(repo), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["totals"]["files"] >= 4
    assert isinstance(payload["files"], list)


def test_main_exits_two_without_a_tests_dir(tmp_path, capsys):
    code = main(["--repo-root", str(tmp_path)])
    err = capsys.readouterr().err
    assert code == 2
    assert "no tests/" in err
    assert "--repo-root" in err


def test_iter_harness_files_drops_a_missing_claude_md(tmp_path):
    (tmp_path / ".claude" / "agents").mkdir(parents=True)
    (tmp_path / ".claude" / "agents" / "worker.md").write_text(
        "Never guess.\n", encoding="utf-8"
    )
    files = iter_harness_files(tmp_path)
    assert [path.name for path in files] == ["worker.md"]


def test_iter_harness_files_excludes_output_styles(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("x", encoding="utf-8")
    styles = tmp_path / ".claude" / "output_styles"
    styles.mkdir(parents=True)
    (styles / "asd-ste100.md").write_text("Never guess.\n", encoding="utf-8")
    files = iter_harness_files(tmp_path)
    assert [path.name for path in files] == ["CLAUDE.md"]


def test_iter_harness_files_puts_the_charter_hook_last(repo):
    files = iter_harness_files(repo)
    assert files[-1].name == "harness-charter.sh"


def test_is_negative_matches_marker_words_on_word_boundaries():
    assert not is_negative("I avoided the topic entirely.")
    assert not is_negative("The north wind blows.")
    assert is_negative("Avoid the topic.")


def test_is_negative_leaves_the_documented_miss_classes_out():
    assert not is_negative(
        "Reply in the review thread, not as a top-level comment."
    )
    assert not is_negative("Post no progress comment before the result.")
    assert not is_negative("Stay silent while the work runs.")
    assert not is_negative(
        "An accepted ADR changes only through a superseding ADR."
    )
    assert not is_negative(
        "Remove secrets before you put artifacts in the issue."
    )


def test_load_pin_literals_measures_the_floor_before_the_collapse(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    runs = "a" + "\n" * 10 + "b" + "\n" * 10 + "c"
    assert len(runs) >= 20
    source = 'RUNS = "' + runs.replace("\n", "\\n") + '"\n'
    (tests / "test_runs.py").write_text(source, encoding="utf-8")
    pins = load_pin_literals(tests)
    assert pins == ["a b c"]


def test_is_pinned_collapses_whitespace_on_both_sides(tmp_path):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_pins.py").write_text(
        'KEY = "alpha\\n\\nbeta\\t\\tgamma delta epsilon"\n',
        encoding="utf-8",
    )
    pins = load_pin_literals(tests)
    assert is_pinned("alpha\n\nbeta\t\tgamma delta epsilon here.", pins)
    assert is_pinned("alpha  beta  gamma delta epsilon", pins)


def test_is_pinned_matches_a_candidate_inside_a_longer_pin():
    pins = ["a pin literal long enough to count"]
    assert is_pinned("pin literal long", pins)


def test_scan_file_reports_unpinned_candidates(repo):
    pins = load_pin_literals(repo / "tests")
    record = scan_file(repo / ".claude" / "agents" / "worker.md", pins)
    assert record["pinned"] == 0
    assert record["candidates"] == [
        {"sentence": "Never push to main alone.", "pinned": False}
    ]
    assert record["findings"] == [
        {"sentence": "Never push to main alone.", "pinned": False}
    ]


def test_run_totals_carry_all_five_counts(repo):
    totals = run(repo)["totals"]
    assert set(totals) == {"files", "sentences", "negative", "pinned", "candidates"}
    assert totals["sentences"] > 0
    assert totals["files"] >= 4


def test_main_json_payload_carries_the_root(repo, capsys):
    code = main(["--repo-root", str(repo), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["root"] == str(repo)


def test_main_json_carries_a_record_for_a_findings_free_file(repo, capsys):
    code = main(["--repo-root", str(repo), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    paths = [record["path"] for record in payload["files"]]
    assert any(path.endswith("reviewer.md") for path in paths)
    record = next(r for r in payload["files"] if r["path"].endswith("reviewer.md"))
    assert record["negative"] == 0


def test_main_text_skips_a_findings_free_file(repo, capsys):
    code = main(["--repo-root", str(repo)])
    out = capsys.readouterr().out
    assert code == 0
    assert "reviewer.md" not in out


def test_main_text_cuts_the_sentence_at_110_characters(repo, capsys):
    sentence = "Never " + "x" * 150 + "."
    agents = repo / ".claude" / "agents"
    (agents / "long.md").write_text(sentence + "\n", encoding="utf-8")
    code = main(["--repo-root", str(repo)])
    out = capsys.readouterr().out
    assert code == 0
    assert sentence[:110] in out
    assert sentence[:111] not in out


def test_main_leaves_the_tree_read_only(repo, capsys):
    before = {
        str(path): path.read_bytes()
        for path in sorted(repo.rglob("*"))
        if path.is_file()
    }
    assert main(["--repo-root", str(repo)]) == 0
    assert main(["--repo-root", str(repo), "--json"]) == 0
    capsys.readouterr()
    after = {
        str(path): path.read_bytes()
        for path in sorted(repo.rglob("*"))
        if path.is_file()
    }
    assert after == before


def test_main_defaults_the_root_to_the_working_directory(repo, capsys, monkeypatch):
    monkeypatch.chdir(repo)
    code = main([])
    out = capsys.readouterr().out
    assert code == 0
    assert "candidates" in out

