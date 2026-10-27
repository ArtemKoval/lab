"""Pin the apply-follows-merge default across the pipeline and propose surfaces."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE = REPO_ROOT / ".claude" / "skills" / "feature-pipeline" / "SKILL.md"
PROPOSE_FILES = (
    REPO_ROOT / ".claude" / "skills" / "openspec-propose" / "SKILL.md",
    REPO_ROOT / ".claude" / "commands" / "opsx" / "propose.md",
)
DEFAULT_PIN = "Apply follows the merge by default"
BOUNDARY_PIN = "apply-follows-merge"


def test_pipeline_skill_carries_the_default():
    text = PIPELINE.read_text(encoding="utf-8")
    assert DEFAULT_PIN in text
    assert "start `/opsx:apply` on the new" in text
    assert "without a second user request" in text


def test_pipeline_default_yields_the_propose_boundary():
    text = PIPELINE.read_text(encoding="utf-8")
    assert "propose workflow yields to this bullet" in text


def test_propose_surfaces_carry_the_exception():
    for path in PROPOSE_FILES:
        text = path.read_text(encoding="utf-8")
        assert BOUNDARY_PIN in text, path
        assert "creates planning artifacts only" in text, path
        assert "its apply-follows-merge default replaces the wait" in text, path
