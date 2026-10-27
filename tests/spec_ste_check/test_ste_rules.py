"""Behavior tests for the spec_ste_check sentence model."""

from spec_ste_check import rules


class TestProseSentences:
    def test_two_sentences_on_one_line_split_at_the_period(self):
        sentences = rules.prose_sentences("The server starts. The server stops.")
        assert [s.text for s in sentences] == [
            "The server starts.",
            "The server stops.",
        ]

    def test_sentences_carry_their_line_number(self):
        sentences = rules.prose_sentences("First line.\nSecond line.")
        assert [s.line for s in sentences] == [1, 2]

    def test_a_heading_line_is_not_prose(self):
        sentences = rules.prose_sentences("# The Title\nA body sentence.")
        assert [s.text for s in sentences] == ["A body sentence."]

    def test_a_list_marker_strips_off(self):
        sentences = rules.prose_sentences("- **WHEN** the command runs")
        assert [s.text for s in sentences] == ["WHEN the command runs"]

    def test_a_blockquote_marker_strips_off(self):
        sentences = rules.prose_sentences("> **CAUTION:** Do not delete the file.")
        assert [s.text for s in sentences] == ["CAUTION: Do not delete the file."]

    def test_a_fenced_block_hides_its_lines(self):
        text = "Before.\n```bash\nnpm run this; and that\n```\nAfter."
        sentences = rules.prose_sentences(text)
        assert [s.text for s in sentences] == ["Before.", "After."]

    def test_a_code_span_hides_its_content(self):
        sentences = rules.prose_sentences("Use `npm; install` now.")
        assert [s.text for s in sentences] == ["Use CODE now."]

    def test_a_trailing_fragment_without_a_period_is_still_a_sentence(self):
        sentences = rules.prose_sentences("The server starts.\nThe server stops")
        assert [s.text for s in sentences] == ["The server starts.", "The server stops"]

    def test_bold_markers_strip_off_in_body_text(self):
        sentences = rules.prose_sentences("The **gate** fails the suite.")
        assert [s.text for s in sentences] == ["The gate fails the suite."]


class TestWordCount:
    def test_a_hyphenated_group_is_one_word(self):
        assert rules.word_count("Write a three-word list.") == 4

    def test_a_code_token_is_one_word(self):
        assert rules.word_count("Use CODE now.") == 3

    def test_a_number_with_its_unit_is_one_word(self):
        assert rules.word_count("It runs 20 seconds.") == 3


class TestImperative:
    def test_an_imperative_start_verb_is_true(self):
        assert rules.is_imperative("Run the tests.") is True

    def test_a_subject_first_sentence_is_false(self):
        assert rules.is_imperative("The suite runs.") is False

    def test_the_first_word_compares_in_lowercase(self):
        assert rules.is_imperative("Examine the report.") is True


class TestSentenceCap:
    LONG_IMPERATIVE = (
        "Run the full suite on a clean clone of the repository before you "
        "push the branch to the remote server today now."
    )
    SHORT_IMPERATIVE = "Run the suite on a clean clone before the push."
    LONG_DESCRIPTIVE = (
        "The gate on the remote server runs the whole suite on every pull "
        "request that touches the harness surface before the merge window "
        "opens."
    )
    SHORT_DESCRIPTIVE = "The gate runs the suite on every pull request."

    def test_a_22_word_imperative_sentence_is_an_error(self):
        assert rules.word_count(self.LONG_IMPERATIVE) == 22
        violation = rules.check_cap(rules.Sentence(4, self.LONG_IMPERATIVE))
        assert violation["rule"] == "sentence-length"
        assert violation["severity"] == "error"
        assert violation["line"] == 4

    def test_a_short_imperative_sentence_is_clean(self):
        assert rules.check_cap(rules.Sentence(1, self.SHORT_IMPERATIVE)) is None

    def test_a_24_word_descriptive_sentence_is_clean(self):
        assert rules.word_count(self.LONG_DESCRIPTIVE) == 24
        assert rules.check_cap(rules.Sentence(2, self.LONG_DESCRIPTIVE)) is None

    def test_a_short_descriptive_sentence_is_clean(self):
        assert rules.check_cap(rules.Sentence(1, self.SHORT_DESCRIPTIVE)) is None


class TestSemicolon:
    def test_a_semicolon_is_an_error(self):
        hits = rules.check_sentence(rules.Sentence(7, "Run it; then stop."))
        assert [v["rule"] for v in hits] == ["semicolon"]
        assert hits[0]["line"] == 7
        assert hits[0]["severity"] == "error"

    def test_a_clean_sentence_gives_nothing(self):
        assert rules.check_sentence(rules.Sentence(1, "Run it now.")) == []


class TestContraction:
    def test_an_nt_contraction_is_an_error(self):
        hits = rules.check_sentence(rules.Sentence(1, "The job doesn't run."))
        assert [v["rule"] for v in hits] == ["contraction"]

    def test_an_s_contraction_is_an_error(self):
        hits = rules.check_sentence(rules.Sentence(1, "It's ready."))
        assert [v["rule"] for v in hits] == ["contraction"]

    def test_a_possessive_is_clean(self):
        assert rules.check_sentence(rules.Sentence(1, "The job's output.")) == []


class TestBannedWords:
    def test_provide_is_banned(self):
        hits = rules.check_sentence(rules.Sentence(1, "The CLI shall provide a report."))
        assert [v["rule"] for v in hits] == ["banned-word"]

    def test_the_inflections_are_banned(self):
        for word in ("ensures", "performed", "utilizes"):
            hits = rules.check_sentence(rules.Sentence(1, f"It {word} the state."))
            assert [v["rule"] for v in hits] == ["banned-word"], word

    def test_a_bare_check_verb_is_banned(self):
        hits = rules.check_sentence(rules.Sentence(1, "Check the logs."))
        assert [v["rule"] for v in hits] == ["banned-word"]

    def test_a_third_person_check_is_banned(self):
        hits = rules.check_sentence(rules.Sentence(1, "The tool checks the state."))
        assert [v["rule"] for v in hits] == ["banned-word"]

    def test_check_after_a_determiner_is_a_clean_noun(self):
        assert rules.check_sentence(rules.Sentence(1, "Examine the check.")) == []
        assert rules.check_sentence(rules.Sentence(1, "The check runs first.")) == []

    def test_an_allowlisted_noun_phrase_is_clean(self):
        assert rules.check_sentence(
            rules.Sentence(1, "Network checks stay opt-in.")
        ) == []


class TestTenses:
    def test_a_progressive_tense_is_an_error(self):
        hits = rules.check_sentence(rules.Sentence(1, "The job is running."))
        assert [(v["rule"], v["severity"]) for v in hits] == [
            ("progressive-tense", "error")
        ]

    def test_a_perfect_tense_is_a_warning(self):
        hits = rules.check_sentence(rules.Sentence(1, "The job has finished."))
        assert [(v["rule"], v["severity"]) for v in hits] == [
            ("perfect-tense", "warning")
        ]

    def test_a_technical_noun_in_ing_is_clean(self):
        assert rules.check_sentence(rules.Sentence(1, "The logging is verbose.")) == []

    def test_has_before_a_noun_is_clean(self):
        assert rules.check_sentence(rules.Sentence(1, "The report has one error.")) == []


class TestCheckText:
    def test_violations_carry_the_file_name(self):
        hits = rules.check_text("Run it; then stop.", "specs/a.md")
        assert hits
        assert all(v["file"] == "specs/a.md" for v in hits)
        assert hits[0]["line"] == 1

    def test_line_numbers_follow_the_source(self):
        hits = rules.check_text("Fine.\nRun it; stop it.", "a.md")
        assert [v["line"] for v in hits] == [2]

    def test_clean_text_gives_nothing(self):
        assert rules.check_text("Run it now.", "a.md") == []


class TestFalsePositives:
    def test_an_adjectival_participle_is_clean(self):
        hits = rules.check_sentence(
            rules.Sentence(1, "The action exits when the ledger is missing.")
        )
        assert hits == []

    def test_check_inside_a_hyphenated_compound_is_clean(self):
        hits = rules.check_sentence(
            rules.Sentence(1, "Examine the builder-check rules.")
        )
        assert hits == []

    def test_a_spaced_noun_phrase_from_the_allowlist_is_clean(self):
        hits = rules.check_sentence(
            rules.Sentence(1, "The flow holds a builder check.")
        )
        assert hits == []


class TestGaps:
    def test_a_blank_line_gives_nothing(self):
        assert [s.text for s in rules.prose_sentences("A line.\n\nAnother line.")] == [
            "A line.",
            "Another line.",
        ]

    def test_an_empty_sentence_is_not_imperative(self):
        assert rules.is_imperative("") is False
