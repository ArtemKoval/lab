"""The build planner's tests and the orchestrated build on doubles."""

from pathlib import Path

from slidecast import build, deck


def a_deck():
    return deck.Deck(
        title="Northgate",
        subtitle="one minute",
        slides=[
            deck.Slide("Northgate", [], "Hello from the library."),
            deck.Slide("Queue", ["ten requests"], "The queue holds ten requests."),
            deck.Slide("Loans", ["fourteen days"], "Every loan runs fourteen days."),
            deck.Slide("Sign-off", ["over fourteen"], "The lead signs off longer terms."),
        ],
    )


def test_speak_and_draw_speaks_every_slide_then_draws_it():
    steps = build.speak_and_draw(a_deck(), Path("/tmp/w"), "en-US-X")
    names = [s.name for s in steps]
    assert names == [
        "speak slide 0", "draw slide 0",
        "speak slide 1", "draw slide 1",
        "speak slide 2", "draw slide 2",
        "speak slide 3", "draw slide 3",
    ]
    assert steps[0].command[0] == "edge-tts"
    assert steps[1].command[0] == "ffmpeg"


def test_the_title_slide_draws_the_deck_title():
    steps = build.speak_and_draw(a_deck(), Path("/tmp/w"), "en-US-X")
    assert "Northgate" in " ".join(steps[1].command)


def test_clips_of_adds_the_tail():
    timings = build.clips_of(a_deck(), Path("/tmp/w"), [5.0, 6.0, 7.0, 8.0])
    assert [t.seconds for t in timings] == [5.8, 6.8, 7.8, 8.8]
    assert timings[2].clip == Path("/tmp/w/clip-2.mp4")


def test_clip_steps_end_with_the_join():
    timings = build.clips_of(a_deck(), Path("/tmp/w"), [5.0, 6.0, 7.0, 8.0])
    steps = build.clip_steps(timings, Path("/tmp/out.mp4"))
    assert steps[-1].name == "join the clips"
    assert len(steps) == 5
    assert "concat.txt" in " ".join(steps[-1].command)


def test_orchestrate_runs_the_whole_plan_in_order():
    ran = []

    def fake_run(step):
        ran.append(step.name)
        if step.name.startswith("speak"):
            Path(step.command[-1]).write_bytes(b"audio")

    def fake_probe(path):
        return 5.0

    timings = build.orchestrate(
        a_deck(), Path("/tmp/w2"), Path("/tmp/out2.mp4"), "en-US-X",
        run=fake_run, probe=fake_probe,
    )
    assert [t.seconds for t in timings] == [5.8] * 4
    assert ran[0] == "speak slide 0"
    assert ran[-1] == "join the clips"
    assert len(ran) == 4 * 2 + 4 + 1
