"""The build plan of slidecast: the steps of one video, in order.

One build walks the deck once: it speaks each slide's narration, draws each
slide, measures each narration, turns each pair into one clip, and
concatenates the clips into the video. The planner gives the steps without
running anything, so the tests can examine a whole build. The runner
executes the steps, and takes its run and probe as arguments, so the tests
can drive it with doubles.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import render, scenes
from .deck import Deck


@dataclass(frozen=True)
class Timing:
    """One slide's place in the video: its index, its audio, its filters."""

    index: int
    audio: Path
    image: Path
    clip: Path
    seconds: float
    filters: str = ""


def speak_and_draw(deck: Deck, work: Path, voice: str) -> list[render.Step]:
    """Give the speak and draw steps of every slide, title slide first."""
    work.mkdir(parents=True, exist_ok=True)
    steps: list[render.Step] = []
    for index, slide in enumerate(deck.slides):
        audio = work / f"voice-{index}.mp3"
        steps.append(
            render.Step(
                f"speak slide {index}", render.speak(slide.narration, audio, voice)
            )
        )
        image = work / f"slide-{index}.png"
        if index == 0:
            draw = render.draw_title(deck.title, deck.subtitle)
        else:
            draw = render.draw_background()
        steps.append(render.Step(f"draw slide {index}", draw + [str(image)]))
    return steps


def clips_of(deck: Deck, work: Path, seconds: list[float]) -> list[Timing]:
    """Give each slide's timing from the measured narration lengths, with
    the scene filters of the slide beside it."""
    timings = []
    for index, one in enumerate(seconds):
        slide = deck.slides[index]
        scene = ""
        if index > 0:
            scene = ",".join(
                scenes.slide_filters(slide.heading, slide.bullets,
                                     list(slide.elements))
            )
        timings.append(
            Timing(
                index=index,
                audio=work / f"voice-{index}.mp3",
                image=work / f"slide-{index}.png",
                clip=work / f"clip-{index}.mp4",
                seconds=round(one + render.TAIL_SECONDS, 3),
                filters=scene,
            )
        )
    return timings


def clip_steps(timings: list[Timing], out: Path) -> list[render.Step]:
    """Give the clip steps and the final join step from the timings."""
    steps = [
        render.Step(
            f"assemble clip {one.index}",
            render.clip(one.image, one.audio, one.seconds, one.clip,
                        filters=one.filters or None),
        )
        for one in timings
    ]
    list_file = timings[0].clip.parent / f"{out.stem}-concat.txt"
    render.write_concat_list([one.clip for one in timings], list_file)
    steps.append(render.Step("join the clips", render.join(out, list_file)))
    return steps


def orchestrate(
    deck: Deck,
    work: Path,
    out: Path,
    voice: str,
    run=render.run,
    probe=render.probe_seconds,
    retries: int = 0,
) -> list[Timing]:
    """Run one build end to end, and give the timings it ran to.

    The voice step talks to a network service, so each speak step may run
    again up to `retries` times, and the step counts only when the audio
    file lands with content in it.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    for step in speak_and_draw(deck, work, voice):
        if step.name.startswith("speak"):
            _speak_with_retries(step, run, retries)
        else:
            run(step)
    lengths = [probe(work / f"voice-{index}.mp3") for index in range(len(deck.slides))]
    timings = clips_of(deck, work, lengths)
    for step in clip_steps(timings, out):
        run(step)
    return timings


def _speak_with_retries(step: render.Step, run, retries: int) -> None:
    """Run one speak step until its audio lands, up to the retry count."""
    audio = Path(step.command[-1])
    for attempt in range(retries + 1):
        try:
            run(step)
        except render.RenderError:
            if attempt == retries:
                raise
        if audio.is_file() and audio.stat().st_size > 0:
            return
    raise render.RenderError(
        f"the step {step.name} wrote no audio after {retries + 1} runs"
    )
