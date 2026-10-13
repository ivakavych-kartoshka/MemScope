from typing import Any

from memscope.experiments.negative_controls import run_negative_controls

SEEDS = (7, 11, 13)


def _controls() -> dict[str, Any]:
    controls, _ = run_negative_controls(
        seeds=SEEDS, apps=3, topics_per_app=4, decoys_per_topic=2
    )
    return controls


def test_all_four_controls_present() -> None:
    controls = _controls()
    for name in (
        "shadow_cache",
        "stale_token_replay",
        "always_accept_verifier",
        "authorized_copy_after_release",
    ):
        assert name in controls
    assert controls["summary"]["controls"] == 4


def test_shadow_cache_leaks_but_memscope_isolates() -> None:
    shadow = _controls()["shadow_cache"]
    assert shadow["mediated_unauthorized_returned"] == 0
    assert shadow["control_unauthorized_returned"] > 0
    assert shadow["control_defeats_guarantee"] is True
    assert shadow["mediated_guarantee_holds"] is True


def test_stale_token_replay_denied_when_mediated() -> None:
    stale = _controls()["stale_token_replay"]
    assert stale["mediated_stale_denied"] is True
    assert stale["mediated_expired_denied"] is True
    assert stale["mediated_replay_denied"] is True
    assert stale["control_stale_epoch_accepted"] is True
    assert stale["control_expired_accepted"] is True
    assert stale["control_replay_accepted"] is True
    assert stale["mediated_guarantee_holds"] is True


def test_always_accept_verifier_breaks_soundness() -> None:
    always = _controls()["always_accept_verifier"]
    assert always["mediated_false_acceptance_rate"] == 0.0
    assert always["control_false_acceptance_rate"] > 0.0
    assert always["mediated_guarantee_holds"] is True
    assert always["control_defeats_guarantee"] is True


def test_authorized_copy_is_out_of_scope_boundary() -> None:
    copy = _controls()["authorized_copy_after_release"]
    assert copy["plaintext_readable_after_release"] is True
    assert copy["post_release_exfiltration_possible"] is True
    assert copy["post_release_dlp_enforced"] is False
    assert copy["mediated_guarantee_holds"] is False
    assert "boundary" in copy
    assert _controls()["summary"]["out_of_scope_by_design"] == ["authorized_copy_after_release"]
