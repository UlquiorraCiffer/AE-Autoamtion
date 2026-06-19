import logging

from app.exceptions import AppError
from app.models.schemas import (
    Beat,
    EditPlan,
    EffectTarget,
    GeneratePlanResponse,
    SceneSegment,
    TimelineEntry,
)
from app.services.analyzer import parse_prompt_locally

logger = logging.getLogger(__name__)


async def generate_plan(
    prompt: str,
    segments: list[SceneSegment],
    beats: list[Beat],
    bpm: float,
) -> GeneratePlanResponse:
    if not segments:
        raise AppError("At least one scene segment is required")

    actions = parse_prompt_locally(prompt)
    action_types = {a.type for a in actions}
    logger.info("Generating plan for prompt (actions=%s, segments=%d, beats=%d)", action_types, len(segments), bpm)

    resolved_bpm = bpm if bpm > 0 else _infer_bpm(beats)

    timeline = _build_timeline(segments, action_types)
    effects = _assign_effects(segments, beats, action_types, resolved_bpm, timeline)

    plan = EditPlan(
        prompt=prompt,
        bpm=resolved_bpm,
        timeline=timeline,
        effects=effects,
    )

    logger.info("Plan generated: %d timeline entries, %d effects", len(timeline), len(effects))
    return GeneratePlanResponse(plan=plan)


def _infer_bpm(beats: list[Beat]) -> float:
    if not beats:
        return 120.0
    bpms = [b.bpm for b in beats if b.bpm > 0]
    if bpms:
        import statistics
        return round(statistics.median(bpms), 1)
    return 120.0


def _build_timeline(
    segments: list[SceneSegment],
    action_types: set[str],
) -> list[TimelineEntry]:
    timeline: list[TimelineEntry] = []
    motion_threshold = _dynamic_motion_threshold(segments)

    keep_all = "keep_all" in action_types
    remove_low = "remove_low_energy" in action_types or "remove_low_motion" in action_types

    kept_order = 0

    for idx, seg in enumerate(segments):
        keep = True

        if remove_low and seg.motion_score < motion_threshold:
            keep = False

        duration = seg.end_time - seg.start_time
        if not keep_all and duration < 0.5 and idx > 0:
            keep = False

        if keep:
            timeline.append(TimelineEntry(segment_index=idx, keep=True, order=kept_order))
            kept_order += 1
        else:
            timeline.append(TimelineEntry(segment_index=idx, keep=False, order=-1))

    return timeline


def _dynamic_motion_threshold(segments: list[SceneSegment]) -> float:
    scores = [s.motion_score for s in segments]
    if not scores:
        return 10.0
    import statistics
    median = statistics.median(scores)
    return max(median * 0.5, 1.0)


def _assign_effects(
    segments: list[SceneSegment],
    beats: list[Beat],
    action_types: set[str],
    bpm: float,
    timeline: list[TimelineEntry],
) -> list[EffectTarget]:
    effects: list[EffectTarget] = []
    kept_indices = {e.segment_index for e in timeline if e.keep}
    if not kept_indices:
        return effects

    beat_interval = 60.0 / bpm if bpm > 0 else 0.5

    if "zoom" in action_types:
        effects += _assign_zoom(segments, beats, kept_indices, bpm, beat_interval)

    if "shake" in action_types:
        effects += _assign_shake(segments, beats, kept_indices, beat_interval)

    if "flash" in action_types:
        effects += _assign_flash(beats, kept_indices, beat_interval)

    if "glow" in action_types:
        effects += _assign_glow(segments, beats, kept_indices, beat_interval)

    if "velocity_ramp" in action_types or "speed_ramp" in action_types:
        effects += _assign_velocity_ramp(segments, kept_indices)

    return effects


def _assign_zoom(
    segments: list[SceneSegment],
    beats: list[Beat],
    kept_indices: set[int],
    bpm: float,
    beat_interval: float,
) -> list[EffectTarget]:
    effects: list[EffectTarget] = []

    for seg_idx in sorted(kept_indices):
        seg = segments[seg_idx]
        if seg.motion_score > _dynamic_motion_threshold(segments) * 1.5:
            effects.append(
                EffectTarget(
                    type="zoom",
                    segment_index=seg_idx,
                    params={"magnitude": 1.3, "direction": "in"},
                )
            )

    for i, beat in enumerate(beats):
        if i % 4 == 0 and beat.drop_intensity > 0.4:
            effects.append(
                EffectTarget(
                    type="zoom",
                    beat_index=i,
                    params={"magnitude": 1.2, "direction": "out"},
                )
            )

    return effects


def _assign_shake(
    segments: list[SceneSegment],
    beats: list[Beat],
    kept_indices: set[int],
    beat_interval: float,
) -> list[EffectTarget]:
    effects: list[EffectTarget] = []

    for seg_idx in sorted(kept_indices):
        seg = segments[seg_idx]
        if seg.motion_score > _dynamic_motion_threshold(segments) * 1.2:
            intensity = min(seg.motion_score / 50.0, 1.0)
            effects.append(
                EffectTarget(
                    type="shake",
                    segment_index=seg_idx,
                    params={"intensity": round(intensity, 2), "frequency": 15},
                )
            )

    for i, beat in enumerate(beats):
        if beat.drop_intensity > 0.6:
            effects.append(
                EffectTarget(
                    type="shake",
                    beat_index=i,
                    params={"intensity": round(beat.drop_intensity, 2), "frequency": 20},
                )
            )

    return effects


def _assign_flash(
    beats: list[Beat],
    kept_indices: set[int],
    beat_interval: float,
) -> list[EffectTarget]:
    effects: list[EffectTarget] = []

    for i, beat in enumerate(beats):
        if i % 2 == 0 and beat.confidence > 0.5:
            effects.append(
                EffectTarget(
                    type="flash",
                    beat_index=i,
                    params={"opacity": 0.8, "duration_seconds": 0.05},
                )
            )

    return effects


def _assign_glow(
    segments: list[SceneSegment],
    beats: list[Beat],
    kept_indices: set[int],
    beat_interval: float,
) -> list[EffectTarget]:
    effects: list[EffectTarget] = []
    threshold = _dynamic_motion_threshold(segments)

    for seg_idx in sorted(kept_indices):
        seg = segments[seg_idx]
        if threshold * 0.5 < seg.motion_score < threshold * 1.5:
            effects.append(
                EffectTarget(
                    type="glow",
                    segment_index=seg_idx,
                    params={"intensity": 0.5, "radius": 30},
                )
            )

    for i, beat in enumerate(beats):
        if i % 8 == 0:
            effects.append(
                EffectTarget(
                    type="glow",
                    beat_index=i,
                    params={"intensity": 0.3, "radius": 20},
                )
            )

    return effects


def _assign_velocity_ramp(
    segments: list[SceneSegment],
    kept_indices: set[int],
) -> list[EffectTarget]:
    effects: list[EffectTarget] = []

    for seg_idx in sorted(kept_indices):
        if seg_idx % 3 == 0:
            effects.append(
                EffectTarget(
                    type="velocity_ramp",
                    segment_index=seg_idx,
                    params={"speed": 1.5, "ramp_in": 0.2, "ramp_out": 0.3},
                )
            )

    return effects
