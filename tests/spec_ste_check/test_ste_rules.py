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

    def test_a_leading_letter_x_survives_the_marker_strip(self):
        sentences = rules.prose_sentences("XHTML rules apply.")
        assert [s.text for s in sentences] == ["XHTML rules apply."]


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

    def test_a_comma_after_the_first_verb_still_counts_as_imperative(self):
        assert rules.is_imperative("Stop, look, and listen.") is True


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
    EXACT_IMPERATIVE = (
        "Run the full suite on a clean clone of the repository and push the "
        "branch to the remote server today."
    )
    EXACT_DESCRIPTIVE = (
        "The gate on the remote server runs the whole suite on every pull "
        "request that touches the harness surface before the merge window "
        "opens today."
    )

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

    def test_a_20_word_imperative_sentence_is_clean(self):
        assert rules.word_count(self.EXACT_IMPERATIVE) == 20
        assert rules.check_cap(rules.Sentence(1, self.EXACT_IMPERATIVE)) is None

    def test_a_25_word_descriptive_sentence_is_clean(self):
        assert rules.word_count(self.EXACT_DESCRIPTIVE) == 25
        assert rules.check_cap(rules.Sentence(1, self.EXACT_DESCRIPTIVE)) is None

    def test_the_cap_violation_carries_the_sentence_text(self):
        violation = rules.check_cap(rules.Sentence(4, self.LONG_IMPERATIVE))
        assert violation["text"] == self.LONG_IMPERATIVE


class TestCheckSentenceCap:
    def test_an_over_cap_sentence_reports_sentence_length(self):
        hits = rules.check_sentence(
            rules.Sentence(3, TestSentenceCap.LONG_IMPERATIVE)
        )
        assert [v["rule"] for v in hits] == ["sentence-length"]
        assert hits[0]["line"] == 3


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

    def test_a_hit_after_a_skipped_noun_check_is_still_reported(self):
        hits = rules.check_sentence(
            rules.Sentence(1, "Examine the check, and then check the logs.")
        )
        assert [v["rule"] for v in hits] == ["banned-word"]

    def test_a_hit_after_an_allowlisted_phrase_is_still_reported(self):
        hits = rules.check_sentence(
            rules.Sentence(1, "The builder check runs, then check the logs.")
        )
        assert [v["rule"] for v in hits] == ["banned-word"]


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
    def test_a_missing_file_name_defaults_to_an_empty_string(self):
        hits = rules.check_text("Run it; then stop.")
        assert hits
        assert all(v["file"] == "" for v in hits)

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


class TestSentenceSplitEdges:
    def test_a_punctuation_gap_becomes_its_own_fragment(self):
        assert [s.text for s in rules.prose_sentences("A. ? B.")] == [
            "A.",
            "?",
            "B.",
        ]


class TestQuotedText:
    def test_a_double_quoted_message_is_exempt(self):
        hits = rules.check_text(
            'It prints "Don\'t panic; run away" once.', "a.md"
        )
        assert hits == []

    def test_the_hidden_quote_becomes_one_code_token(self):
        sentences = rules.prose_sentences('It prints "x y" once.')
        assert [s.text for s in sentences] == ["It prints CODE once."]

    def test_the_hidden_curly_quote_becomes_one_code_token(self):
        sentences = rules.prose_sentences("The message says “x y” only.")
        assert [s.text for s in sentences] == ["The message says CODE only."]

    def test_curly_double_quotes_are_exempt(self):
        hits = rules.check_text(
            "The message says “ensure the state” only.", "a.md"
        )
        assert hits == []

    def test_an_unpaired_quote_stays_prose(self):
        hits = rules.check_text('He said "check it now, then leave.', "a.md")
        assert [v["rule"] for v in hits] == ["banned-word"]

    def test_single_quotes_stay_prose(self):
        hits = rules.check_text("It is a 'ensure' case.", "a.md")
        assert [v["rule"] for v in hits] == ["banned-word"]


class TestMultilineSpans:
    def test_a_span_across_lines_hides_its_content(self):
        hits = rules.check_text("Use `ensure\nit` now.", "a.md")
        assert hits == []

    def test_a_span_open_at_the_end_of_a_line_closes_later(self):
        sentences = rules.prose_sentences("The `run\nx` span hides one token.")
        assert [s.text for s in sentences] == [
            "The CODE",
            "span hides one token.",
        ]

    def test_prose_between_spans_stays_examined(self):
        hits = rules.check_text("Use `run x` and ensure y` z` now.", "a.md")
        assert [v["rule"] for v in hits] == ["banned-word"]


class TestBlockquoteProse:
    def test_a_blockquoted_fence_hides_its_lines(self):
        text = "> ```\n> ensure foo; perform bar\n> ```\nAfter."
        hits = rules.check_text(text, "a.md")
        assert hits == []
        assert [s.text for s in rules.prose_sentences(text)] == ["After."]

    def test_a_blockquoted_list_item_strips_both_markers(self):
        hits = rules.check_text(
            "> - " + "Run every test " * 10 + "today.",
            "a.md",
        )
        assert [v["rule"] for v in hits] == ["sentence-length"]


class TestContractionForms:
    def test_the_d_contraction_is_an_error(self):
        hits = rules.check_sentence(rules.Sentence(1, "They'd run it."))
        assert [v["rule"] for v in hits] == ["contraction"]

    def test_a_curly_apostrophe_contraction_is_an_error(self):
        hits = rules.check_sentence(rules.Sentence(1, "It’s ready."))
        assert [v["rule"] for v in hits] == ["contraction"]


class TestTenseAllowlist:
    def test_missing_agrees_with_every_auxiliary(self):
        for aux in ("is", "are", "was", "were"):
            hits = rules.check_sentence(rules.Sentence(1, f"The ledger {aux} missing."))
            assert hits == [], aux

    def test_a_real_progressive_still_fails(self):
        hits = rules.check_sentence(rules.Sentence(1, "The job is running."))
        assert [v["rule"] for v in hits] == ["progressive-tense"]


class TestNumberUnits:
    def test_a_number_before_a_non_unit_stays_two_words(self):
        assert rules.word_count("The 401 error stays.") == 4

    def test_a_number_before_a_unit_joins(self):
        assert rules.word_count("It runs 20 seconds.") == 3


class TestQuoteMarkerStripping:
    def test_a_marker_without_a_space_strips_cleanly(self):
        assert rules._strip_quote_markers(">quoted") == "quoted"

    def test_double_markers_strip_cleanly(self):
        assert rules._strip_quote_markers("> > quoted") == "quoted"
