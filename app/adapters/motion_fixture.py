"""Explicit local synthetic qualification provider, never a creative-quality claim."""

import html
from typing import Any

from app.schemas.motion_plan import MotionPlan
from app.schemas.motion_production import HTMLMotionComposition, MotionAudio, MotionReview
from app.schemas.motion_scene_direction import MotionSceneDirection
from app.services.motion_creative import CREATIVE_CRITERIA
from app.services.motion_plan import requires_motion_plan, requires_scene_direction
from app.services.motion_protocols import MotionModelRequest, MotionModelResult
from app.services.motion_temporal import TEMPORAL_CRITERIA, temporal_payload


class FixtureMotionProvider:
    provider = "fake"
    model = "motion-qualification-v1"

    def build_request(self, request: MotionModelRequest) -> dict[str, Any]:
        return {"kind": request.kind, "context": request.context}

    async def count_input_tokens(self, request: MotionModelRequest, payload: dict[str, Any]) -> int:
        return 0

    async def submit(self, request: MotionModelRequest, payload: dict[str, Any]) -> MotionModelResult:
        if request.kind != "review":
            brand = html.escape(request.context["kit"]["overrides"]["brand_name"])
            composition = HTMLMotionComposition(
                html=f'<html><body style="margin:0;background:#fff"><video id="source" src="assets/source.mp4" muted '
                f'style="width:720px;height:1280px;object-fit:contain"></video>'
                f'<div id="brand" style="position:absolute;top:100px;left:70px;'
                f'background:#fff;color:#000;font:36px sans-serif">'
                f"{brand}</div></body></html>",
                scene_init="""window.seek=async(ms)=>{const v=document.getElementById('source');
                  if(v.readyState<1)await new Promise(r=>v.addEventListener('loadedmetadata',r,{once:true}));
                  const t=Math.min(ms/1000,Math.max(0,v.duration-0.04));
                  if(Math.abs(v.currentTime-t)>0.001){await new Promise(r=>{
                    v.addEventListener('seeked',r,{once:true});v.currentTime=t;});}};""",
                concept="Deterministic local qualification; not a creative benchmark.",
                source_usage="Original synthetic source recording, preserved audio.",
                audio=MotionAudio.model_validate(request.context["authorized_audio"]),
                motion_plan=self._plan(request) if requires_motion_plan(request.context) else None,
                scene_direction=self._direction() if requires_scene_direction(request.context) else None,
            )
            return MotionModelResult(composition=composition, estimated_usd_micros=0)
        evidence = [{"version": "current", "at_ms": frame.ms, "sha256": frame.sha256} for frame in request.frames[:1]]
        temporal = temporal_payload(
            request.context,
            request.composition,
            request.frames,
            request.incumbent_composition,
            request.incumbent_frames,
        )
        windows = temporal["current"]["events"] if temporal else []
        complete = bool(windows) and all(event["complete"] for event in windows)
        temporal_checks = (
            [
                {
                    "name": name,
                    "status": "pass" if complete else "uncertain",
                    "observation": "Synthetic fixture only; not a creative-quality judgment.",
                    "event_ids": [event["id"] for event in windows],
                    "evidence": [ref for event in windows for ref in event["evidence"]],
                    "issue_indices": [],
                }
                for name in TEMPORAL_CRITERIA
            ]
            if temporal
            else []
        )
        review = MotionReview.model_validate(
            {
                "verdict": "insufficient_evidence" if temporal and not complete else "adequate",
                "temporal_checks": temporal_checks,
                "creative_checks": [
                    {
                        "name": name,
                        "status": "met",
                        "brief_basis": "Synthetic fixture contract only.",
                        "observation": "Synthetic assertion; not a creative-quality judgment.",
                        "evidence": [
                            {"version": "current", "at_ms": frame.ms, "sha256": frame.sha256}
                            for frame in (request.frames[0], request.frames[-1])
                        ],
                    }
                    for name in CREATIVE_CRITERIA
                ]
                if request.context.get("creative_contract")
                else [],
                "preferred": "undetermined",
                "preference_reason": "Synthetic qualification only.",
                "preference_evidence": [],
                "issues": [],
                "limitations": ["Deterministic fixture, not quality assessment."],
                "criteria": [
                    {
                        "name": name,
                        "status": "uncertain" if name == "audio" else "pass",
                        "observation": "Synthetic fixture assertion; no human or model evaluation.",
                        "evidence": evidence if name != "audio" else [],
                    }
                    for name in ("factuality", "brand", "legibility", "composition", "motion", "technical", "audio")
                ],
            }
        )
        return MotionModelResult(review=review, estimated_usd_micros=0)

    @staticmethod
    def _direction() -> MotionSceneDirection:
        return MotionSceneDirection.model_validate(
            {
                "version": "scene-direction-v1",
                "scenes": [
                    {
                        "scene_id": "fixture",
                        "brief_basis": "Synthetic qualification only.",
                        "visual_representation": "Source and brand label; not a creative benchmark.",
                        "composition": "Full source with static brand label at top left.",
                        "narrative_action": "No narrative assertion: deterministic synthetic fixture.",
                        "attention_order": ["source", "brand"],
                        "elements": [
                            {
                                "element_id": name,
                                "depicts": depiction,
                                "appearance": appearance,
                                "construction": construction,
                            }
                            for name, depiction, appearance, construction in (
                                ("source", "Authorized source", "Contained video", "authorized_asset"),
                                ("brand", "Brand name", "Black text on white", "code"),
                            )
                        ],
                    }
                ],
            }
        )

    @staticmethod
    def _plan(request: MotionModelRequest) -> MotionPlan:
        duration = request.context["output"]["duration_ms"]
        return MotionPlan.model_validate(
            {
                "version": "motion-plan-v1",
                "identity_source": "business_kit",
                "duration_ms": duration,
                "style_id": None,
                "scenes": [
                    {
                        "id": "fixture",
                        "start_ms": 0,
                        "end_ms": duration,
                        "message": "Synthetic qualification, not a creative benchmark.",
                        "transition_to_next": "End of fixture.",
                        "elements": [
                            {
                                "id": identifier,
                                "role": role,
                                "asset_id": asset,
                                "purpose": "Synthetic qualification only.",
                                "related_element_ids": [],
                                "coordination": "Static title and source, no creative-quality assertion.",
                                "beats": [
                                    {
                                        "phase": "hold",
                                        "start_ms": 0,
                                        "end_ms": duration,
                                        "start_state": "Visible",
                                        "end_state": "Visible",
                                        "trajectory": "Static",
                                        "curve": {"kind": "linear", "parameters": []},
                                    }
                                ],
                            }
                            for identifier, role, asset in (
                                ("source", "video", "assets/source.mp4"),
                                ("brand", "text", None),
                            )
                        ],
                    }
                ],
            }
        )
