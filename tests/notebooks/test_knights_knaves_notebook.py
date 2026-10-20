"""Tests for the knights-and-knaves agent notebook.

The notebook is a Colab artifact. The tests read the .ipynb as JSON and run
its code cells against stubbed course dependencies, so the whole module stays
in the standard library and the default pytest run stays hermetic.
"""
import json
import re
import sys
import types
from pathlib import Path

import pytest

NOTEBOOK = Path(__file__).resolve().parents[2] / "notebooks" / "knights-and-knaves-agent.ipynb"
NOTEBOOKS_DIR = NOTEBOOK.parent

# The contribution checklist bans emojis. Only the middle dot and the em dash
# may appear as non-ASCII characters.
ALLOWED_NON_ASCII = {0xB7, 0x2014}

RIDDLE_ROWS = [
    {
        "quiz": "A says 'I am a knight.' B says 'A is a knave.'",
        "names": ["A", "B"],
        "solution": [True, False],
    },
    {
        "quiz": "C says 'D is a knave.'",
        "names": ["C", "D"],
        "solution": [False, True],
    },
]

def cell_text(cell):
    return "".join(cell["source"])


def flagged_chars(text):
    """Return every character that the emoji-free rule forbids."""
    return [ch for ch in text if ord(ch) > 127 and ord(ch) not in ALLOWED_NON_ASCII]


@pytest.fixture(scope="module")
def nb():
    with NOTEBOOK.open(encoding="utf-8") as fh:
        return json.load(fh)


def find_cell(nb, prefix):
    matches = [c for c in nb["cells"] if cell_text(c).startswith(prefix)]
    assert len(matches) == 1, f"expected one cell starting with {prefix!r}, found {len(matches)}"
    return matches[0]


def run_cells(nb, prefixes, ns, stop_marker=None):
    """Exec the named cells into ns. With stop_marker, exec only the part before it."""
    for prefix in prefixes:
        text = cell_text(find_cell(nb, prefix))
        if stop_marker:
            text = text.split(stop_marker)[0]
        code = compile(text, f"<{prefix[:24]}>", "exec")
        exec(code, ns)  # noqa: S102 - the suite runs repo content under stubs
    return ns


# --- fakes for the course dependencies -------------------------------


class FakeRiddles:
    def __init__(self, rows):
        self._rows = rows

    def __len__(self):
        return len(self._rows)

    def __getitem__(self, index):
        return self._rows[index]


class FakeOpenAI:
    def __init__(self, **kwargs):
        self.init_kwargs = kwargs
        self.scripted = []
        self.calls = []
        self.chat = types.SimpleNamespace(completions=self)

    def create(self, **kwargs):
        self.calls.append(kwargs)
        item = self.scripted.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class FakeHTTPError(Exception):
    def __init__(self, status_code):
        super().__init__(f"http {status_code}")
        self.status_code = status_code


def reply(text=None, tool_calls=None, model="fake-model"):
    message = types.SimpleNamespace(content=text, tool_calls=tool_calls)
    reason = "tool_calls" if tool_calls else "stop"
    choice = types.SimpleNamespace(message=message, finish_reason=reason)
    return types.SimpleNamespace(choices=[choice], model=model)


def tool_call(name, arguments, call_id="call_1"):
    function = types.SimpleNamespace(name=name, arguments=arguments)
    return types.SimpleNamespace(id=call_id, function=function)


def catalog_entry(model_id, prompt="0", completion="0", modality="text->text",
                  context=8000, created=0, intelligence=None, name=None):
    benchmarks = {}
    if intelligence is not None:
        benchmarks = {"artificial_analysis": {"intelligence_index": intelligence}}
    return {
        "id": model_id,
        "name": name or model_id,
        "pricing": {"prompt": prompt, "completion": completion},
        "architecture": {"modality": modality},
        "context_length": context,
        "created": created,
        "benchmarks": benchmarks,
    }


# Sort strength is (-intelligence, -context, -recency). A model with no
# benchmark entry falls back to -1, so it lands after every scored model.
FREE_CATALOG = [
    catalog_entry("slow/small:free", intelligence=70),
    catalog_entry("paid/model", prompt="1e-06", completion="2e-06"),
    catalog_entry("openrouter/free"),
    catalog_entry("draw/picture:free", modality="text->image"),
    catalog_entry("multi/modal:free", modality="text->text+image"),
    catalog_entry("safe/guard:free", name="Safety Guard"),
    {"id": "no/price:free"},
    catalog_entry("strong/big:free", intelligence=90, context=128000),
    catalog_entry("queued/small:free", intelligence=10),
    catalog_entry("no/bench:free", context=32000),
]

# Two scored models and a third: the runner's heat fills exactly.
RUN_CATALOG = [
    catalog_entry("a/one:free", intelligence=30),
    catalog_entry("b/two:free", intelligence=20),
    catalog_entry("c/three:free", intelligence=10),
]

# The strongest model refuses the ping, so the queued model steps up.
REFUSAL_CATALOG = [
    catalog_entry("gated/one:free", intelligence=40),
    catalog_entry("b/two:free", intelligence=30),
    catalog_entry("c/three:free", intelligence=20),
    catalog_entry("d/four:free", intelligence=10),
]


def install_stubs(monkeypatch, catalog=()):
    """Put stub course modules in sys.modules. Returns the capture dict."""
    cap = {"displayed": [], "catalog": list(catalog)}

    datasets = types.ModuleType("datasets")
    datasets.load_dataset = lambda *args, **kwargs: FakeRiddles(RIDDLE_ROWS)

    google = types.ModuleType("google")
    google_colab = types.ModuleType("google.colab")
    userdata = types.ModuleType("google.colab.userdata")
    userdata.get = lambda name: "sk-or-v1-faketoken"
    google.colab = google_colab
    google_colab.userdata = userdata

    ipython = types.ModuleType("IPython")
    ipython_display = types.ModuleType("IPython.display")
    ipython.HTML = lambda text: types.SimpleNamespace(html=text)
    ipython.Markdown = lambda text: types.SimpleNamespace(markdown=text)
    ipython_display.HTML = ipython.HTML
    ipython_display.Markdown = ipython.Markdown
    ipython_display.display = lambda obj: cap["displayed"].append(obj)
    ipython.display = ipython_display

    requests_stub = types.ModuleType("requests")
    requests_stub.get = lambda url, timeout=None: FakeResponse({"data": cap["catalog"]})

    openai_stub = types.ModuleType("openai")
    openai_stub.OpenAI = FakeOpenAI

    stubs = {
        "datasets": datasets,
        "google": google,
        "google.colab": google_colab,
        "google.colab.userdata": userdata,
        "IPython": ipython,
        "IPython.display": ipython_display,
        "requests": requests_stub,
        "openai": openai_stub,
    }
    for name, module in stubs.items():
        monkeypatch.setitem(sys.modules, name, module)
    return cap


def game_ns(nb, monkeypatch):
    """A namespace with the notebook's game cells executed against the stubs."""
    cap = install_stubs(monkeypatch)
    ns = {"__name__": "knights_knaves_cells", "_cap": cap}
    run_cells(nb, [
        "import json",
        "openrouter_api_key = userdata.get",
        "OPENROUTER_BASE_URL",
        "# 8 inhabitants per riddle",
        "GAME_CSS",
        "# What the island knows",
        "get_riddle_json = {",
        "TOOLS = {",
        "SYSTEM_PROMPT",
        "def run_agent",
    ], ns)
    return ns


def tournament_ns(nb, monkeypatch, catalog):
    """A namespace with the tournament setup cell and its helper defs executed."""
    cap = install_stubs(monkeypatch, catalog=catalog)
    ns = {"USAGE": {"requests": 0}, "_cap": cap}
    run_cells(nb, ["import json", "GAME_CSS", "# Nothing hardcoded"], ns)
    run_cells(nb, ["import time"], ns, stop_marker="results = []")
    return ns


def runner_ns(nb, monkeypatch, catalog):
    """A namespace with the game and tournament setup cells, ready for the runner cell."""
    ns = game_ns(nb, monkeypatch)
    ns["_cap"]["catalog"][:] = catalog
    run_cells(nb, ["# Nothing hardcoded"], ns)
    monkeypatch.setitem(sys.modules, "time", types.SimpleNamespace(sleep=lambda seconds: None))
    return ns


def roles_of(messages):
    """The role of each entry in a recorded messages list."""
    return [m["role"] if isinstance(m, dict) else "assistant" for m in messages]


# --- structure guards ------------------------------------------------


def test_notebook_is_valid_nbformat_4(nb):
    assert nb["nbformat"] == 4
    kinds = {c["cell_type"] for c in nb["cells"]}
    assert kinds == {"code", "markdown"}


def test_code_cells_carry_no_outputs(nb):
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            assert cell.get("outputs") == []
            assert cell.get("execution_count") is None


def test_notebook_is_emoji_free(nb):
    for cell in nb["cells"]:
        assert flagged_chars(cell_text(cell)) == []


def test_notebook_contains_no_api_key(nb):
    for cell in nb["cells"]:
        text = cell_text(cell)
        assert not re.search(r"sk-[A-Za-z0-9_-]{16,}", text)
        assert not re.search(r"Bearer\s+[A-Za-z0-9._-]{16,}", text)


def test_notebook_pins_the_dataset(nb):
    text = "".join(cell_text(c) for c in nb["cells"])
    assert "K-and-K/knights-and-knaves" in text


def test_notebooks_dir_holds_only_notebooks():
    for path in NOTEBOOKS_DIR.iterdir():
        assert path.suffix == ".ipynb", f"stray file in notebooks/: {path.name}"


# --- parse_assignment ------------------------------------------------


def test_parse_assignment_accepts_a_dict(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    verdict = {"A": "knight"}
    assert ns["parse_assignment"](verdict) is verdict


def test_parse_assignment_accepts_plain_text(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    parsed = ns["parse_assignment"]("Zoey: knave; Oliver: knight")
    assert parsed == {"Zoey": "knave", "Oliver": "knight"}


def test_parse_assignment_accepts_newlines_and_commas(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    parsed = ns["parse_assignment"]("A: knight\nB: knave, C: knight")
    assert parsed == {"A": "knight", "B": "knave", "C": "knight"}


def test_parse_assignment_strips_punctuation_and_lowercases(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    parsed = ns["parse_assignment"]("-A-. : -KNIGHT-")
    assert parsed == {"A": "knight"}


def test_parse_assignment_without_colons_gives_empty_dict(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    assert ns["parse_assignment"]("no roles here") == {}


# --- get_riddle and submit_answer ------------------------------------


def test_get_riddle_serves_the_riddle_and_hides_the_answer(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    served = ns["get_riddle"]()
    assert served["riddle_id"] == 1
    assert served["inhabitants"] == ["A", "B"]
    assert "solution" not in served
    assert ns["_solutions"][1] == {"A": True, "B": False}


def test_get_riddle_draws_the_island_card(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    ns["get_riddle"]()
    html = ns["_cap"]["displayed"][0].html
    assert "Riddle 1" in html
    assert "A" in html


def test_get_riddle_runs_dry(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    ns["get_riddle"]()
    ns["get_riddle"]()
    assert ns["get_riddle"]() == {"message": "The island has no riddles left."}


def test_submit_answer_names_the_wrong_and_whispers_one_hint(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    ns["get_riddle"]()
    result = ns["submit_answer"](1, {"A": "knave", "B": "knave"})
    assert result["solved"] is False
    assert result["judged_wrong"] == ["A"]
    assert result["hint"] == "The island elder whispers: A is a knight."
    assert ns["_score"] == {"solved": 0, "attempts": 1, "hints": 1}


def test_submit_answer_hints_run_dry_after_every_wrong_name_is_revealed(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    ns["get_riddle"]()
    first = ns["submit_answer"](1, {"A": "knave", "B": "knave"})
    second = ns["submit_answer"](1, {"A": "knight", "B": "knight"})
    assert second["hint"] == "The island elder whispers: B is a knave."
    third = ns["submit_answer"](1, {"A": "knight", "B": "knight"})
    assert "hint" not in third
    assert "no more hints" in third["message"]
    assert third["judged_wrong"] == ["B"]
    assert ns["_score"]["hints"] == 2


def test_submit_answer_accepts_a_win(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    ns["get_riddle"]()
    result = ns["submit_answer"](1, {"A": "knight", "B": "knave"})
    assert result["solved"] is True
    assert ns["_score"]["solved"] == 1


# --- handle_tool_call ------------------------------------------------


def test_handle_tool_call_returns_json_for_the_model(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    message = ns["handle_tool_call"](tool_call("get_riddle", "{}"))
    assert message["role"] == "tool"
    payload = json.loads(message["content"])
    assert payload["riddle_id"] == 1


def test_handle_tool_call_reports_failures_as_content(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    broken = tool_call("submit_answer", "not json")
    assert ns["handle_tool_call"](broken)["content"].startswith("The tool call failed")
    unknown = tool_call("no_such_tool", "{}")
    assert ns["handle_tool_call"](unknown)["content"].startswith("The tool call failed")


# --- run_agent -------------------------------------------------------


def test_run_agent_loops_until_the_final_answer(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    client = ns["openrouter"]
    verdict = json.dumps({"riddle_id": 1, "assignment": {"A": "knight", "B": "knave"}})
    client.scripted = [
        reply(tool_calls=[tool_call("get_riddle", "{}", "call_1")]),
        reply(tool_calls=[tool_call("submit_answer", verdict, "call_2")]),
        reply(text="The island is solved."),
    ]
    steps = ns["run_agent"]("Solve the island.", max_steps=5)
    assert steps == 3
    assert ns["_score"]["solved"] == 1
    assert len(client.calls) == 3
    final_roles = roles_of(client.calls[-1]["messages"])
    assert final_roles == ["system", "user", "assistant", "tool", "assistant", "tool"]


def test_run_agent_asks_again_after_an_empty_reply(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    ns["openrouter"].scripted = [reply(), reply(text="Done.")]
    assert ns["run_agent"]("Solve the island.", max_steps=5) == 2


def test_run_agent_gives_up_after_max_steps(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    ns["openrouter"].scripted = [reply(), reply()]
    assert ns["run_agent"]("Solve the island.", max_steps=2) is None


# --- tournament ------------------------------------------------------


def test_discover_keeps_chat_capable_free_models_strongest_first(nb, monkeypatch):
    ns = tournament_ns(nb, monkeypatch, FREE_CATALOG)
    assert ns["all_models"] == [
        "strong/big:free", "slow/small:free", "queued/small:free", "no/bench:free",
    ]


def test_setup_sizes_the_heat_to_the_budget(nb, monkeypatch):
    ns = tournament_ns(nb, monkeypatch, FREE_CATALOG)
    assert ns["square_cap"] == 7
    assert ns["heat"] == ["strong/big:free", "slow/small:free", "queued/small:free"]
    assert ns["queue"] == ["no/bench:free"]


def test_answers_directly_true_for_a_talking_model(nb, monkeypatch):
    ns = tournament_ns(nb, monkeypatch, FREE_CATALOG)
    ns["openrouter"] = FakeOpenAI()
    ns["openrouter"].scripted = [reply(text="ok")]
    assert ns["answers_directly"]("strong/big:free") is True


def test_answers_directly_false_for_a_harness_gated_model(nb, monkeypatch):
    ns = tournament_ns(nb, monkeypatch, FREE_CATALOG)

    def refuse(**kwargs):
        raise FakeHTTPError(403)

    ns["openrouter"] = FakeOpenAI()
    ns["openrouter"].create = refuse
    assert ns["answers_directly"]("gated/model:free") is False


def test_answers_directly_tolerates_a_busy_pool(nb, monkeypatch):
    ns = tournament_ns(nb, monkeypatch, FREE_CATALOG)

    def busy(**kwargs):
        raise FakeHTTPError(429)

    ns["openrouter"] = FakeOpenAI()
    ns["openrouter"].create = busy
    assert ns["answers_directly"]("busy/model:free") is True


def _rendered_board(ns, results):
    ns["leaderboard"](results)
    return ns["_cap"]["displayed"][-1].html


def test_leaderboard_ranks_solved_runs_first(nb, monkeypatch):
    ns = tournament_ns(nb, monkeypatch, FREE_CATALOG)
    html = _rendered_board(ns, [
        {"model": "second:free", "solved": True, "attempts": 2, "hints": 2, "steps": 8, "error": None},
        {"model": "first:free", "solved": True, "attempts": 1, "hints": 1, "steps": 6, "error": None},
        {"model": "lost:free", "solved": False, "attempts": 9, "hints": 5, "steps": 9, "error": None},
        {"model": "gated:free", "solved": False, "attempts": 0, "hints": 0, "steps": 0,
         "error": "403 - only available through agentic harnesses"},
    ])
    assert html.index("first:free") < html.index("second:free") < html.index("lost:free")
    assert html.index("gated:free") > html.index("lost:free")
    assert "1st" in html and "2nd" in html
    assert "only available through agentic harnesses" in html


def test_leaderboard_draws_a_plain_text_table(nb, monkeypatch):
    ns = tournament_ns(nb, monkeypatch, FREE_CATALOG)
    html = _rendered_board(ns, [
        {"model": "first:free", "solved": True, "attempts": 1, "hints": 1, "steps": 6, "error": None},
        {"model": "gated:free", "solved": False, "attempts": 0, "hints": 0, "steps": 0, "error": "403"},
    ])
    assert flagged_chars(html) == []
    assert "Rank</th>" in html
    assert "requests spent by the agent loop" in html


# --- review-round regressions ----------------------------------------


def test_submit_answer_matches_names_regardless_of_case(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    ns["get_riddle"]()
    result = ns["submit_answer"](1, "a: knave; B: knave")
    assert result["judged_wrong"] == ["A"]
    assert result["hint"] == "The island elder whispers: A is a knight."


def test_submit_answer_accepts_a_json_string_verdict(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    ns["get_riddle"]()
    result = ns["submit_answer"](1, '{"A": "knight", "B": "knave"}')
    assert result["solved"] is True


def test_submit_answer_counts_a_riddle_as_solved_once(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    ns["get_riddle"]()
    ns["submit_answer"](1, {"A": "knight", "B": "knave"})
    again = ns["submit_answer"](1, {"A": "knight", "B": "knave"})
    assert again["solved"] is True
    assert ns["_score"]["solved"] == 1
    assert ns["_score"]["attempts"] == 2


def test_esc_neutralizes_double_quotes(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    assert ns["esc"]('He said "no"') == "He said &quot;no&quot;"


def test_leaderboard_keeps_the_error_title_intact(nb, monkeypatch):
    ns = tournament_ns(nb, monkeypatch, FREE_CATALOG)
    html = _rendered_board(ns, [
        {"model": "gated:free", "solved": False, "attempts": 0, "hints": 0, "steps": 0,
         "error": 'The model said "no"'},
    ])
    assert 'title="The model said &quot;no&quot;"' in html


def test_the_agent_task_is_defined_once(nb):
    text = "".join(cell_text(c) for c in nb["cells"])
    assert text.count("Call get_riddle to hear the island's riddle") == 1
    assert "run_agent(TASK)" in text
    assert "run_agent(TASK, max_steps=STEPS_ALLOWED, model=name)" in text


def test_the_demo_loop_survives_a_text_reply(nb, monkeypatch):
    ns = game_ns(nb, monkeypatch)
    ns["openrouter"].scripted = [reply(text="I will call the tool soon."), reply(text="All set.")]
    run_cells(nb, [
        'messages = [{"role": "user", "content": "Please call get_riddle',
        "messages.append(message)",
    ], ns)
    assert ns["_cap"]["displayed"][-1].markdown == "All set."


def _script_one_solved_run(client, name):
    verdict = json.dumps({"riddle_id": 1, "assignment": {"A": "knight", "B": "knave"}})
    client.scripted += [
        reply(tool_calls=[tool_call("get_riddle", "{}")]),
        reply(tool_calls=[tool_call("submit_answer", verdict)]),
        reply(text="Solved.", model=name),
    ]


def test_tournament_runs_the_heat_and_spends_the_budget(nb, monkeypatch):
    ns = runner_ns(nb, monkeypatch, RUN_CATALOG)
    for _ in ns["heat"]:
        ns["openrouter"].scripted.append(reply(text="ok"))
    for name in ("a/one:free", "b/two:free", "c/three:free"):
        _script_one_solved_run(ns["openrouter"], name)
    run_cells(nb, ["import time"], ns)
    assert [r["model"] for r in ns["results"]] == ["a/one:free", "b/two:free", "c/three:free"]
    assert all(r["solved"] for r in ns["results"])
    assert ns["USAGE"]["requests"] == 12
    html = ns["_cap"]["displayed"][-1].html
    assert html.index("a/one:free") < html.index("b/two:free") < html.index("c/three:free")
    assert "1st" in html


def test_tournament_steps_up_when_a_model_refuses(nb, monkeypatch):
    ns = runner_ns(nb, monkeypatch, REFUSAL_CATALOG)
    ns["openrouter"].scripted.append(FakeHTTPError(403))
    for _ in range(3):
        ns["openrouter"].scripted.append(reply(text="ok"))
    for name in ("b/two:free", "c/three:free", "d/four:free"):
        _script_one_solved_run(ns["openrouter"], name)
    run_cells(nb, ["import time"], ns)
    assert ns["results"][0]["model"] == "gated/one:free"
    assert "403" in ns["results"][0]["error"]
    assert [r["model"] for r in ns["results"] if r["solved"]] == [
        "b/two:free", "c/three:free", "d/four:free",
    ]
    assert ns["USAGE"]["requests"] == 12


def test_tournament_stops_before_the_day_is_overdrawn(nb, monkeypatch):
    ns = runner_ns(nb, monkeypatch, RUN_CATALOG)
    ns["USAGE"]["requests"] = 36
    ns["openrouter"].scripted = [reply(text="ok")]
    run_cells(nb, ["import time"], ns)
    assert ns["USAGE"]["requests"] == 37
    assert ns["results"] == []
