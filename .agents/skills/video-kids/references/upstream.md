# Optional Blender production sources

Read this when a story needs deeper rig validation, authored shape keys, animation loops, terrain or NPR beyond the staged `kids_stage.py` foundation. These MIT sources are pinned in [SOURCE.json](upstream/blender-skills/SOURCE.json); their [LICENSE](upstream/blender-skills/LICENSE) travels with adapted code. The original two story repositories were already inspected in the production refactor; no duplicate engine or Roblox assets were imported.

The collection contains the pack's nine Blender topics plus `blender-asset-qa`, which those topics depend on. Start with the relevant `skills/blender-TOPIC/UPSTREAM_SKILL.md` inside [the collection](upstream/blender-skills/). Archived upstream instructions retain their original version assumptions and references to optional, uninstalled topics; they are source references, not this project's execution contract.

## Actual compatibility

Upstream targets Blender 5.2+ / 5.3. This project has Blender 4.0.2 CPU and 4.5.16 LTS CUDA. Do not apply the upstream 5.x compositor, action/channelbag, Geometry Nodes or engine-name recipes without a job-local capability check. Do not upgrade images, install Rigify/add-ons or fetch assets as a side effect of reading a reference.

| Tool / scope | Verified locally |
|---|---|
| `blender-core/scripts/env_report.py` | Runs on both installed Blender versions |
| `blender-character-rigging/scripts/rig_check.py`, nonfix `game` profile | Both versions: eight-bone original cast passes; missing vertex weight is correctly rejected; body-root origin warning remains visible |
| `blender-facial-shapekeys/scripts/shapekeys.py`, create/report | 4.5: creates 15 viseme keys and correctly reports all as unsculpted. 4.0: blocked by missing NumPy. This does not create finished mouth shapes or lip sync |
| Other scripts, profiles, fix/retarget/export/driver paths | Source available; not runtime verified here |

Use the existing Docker/Omega workflow. To adapt a tool, copy only the necessary script, `_bpyx.py`, and license/provenance into `jobs/ID/scenes/` or `jobs/ID/qa/` before executing inside the selected container. The host skill path is not container-mounted. Keep generated files inside that job, and inspect actual frames before accepting visual changes. Existing `configure_renderer` and GPU verification remain authoritative for selecting the installed renderer.

Evidence: `video_docker_sandbox/workspace/jobs/7c231c5a/qa/skill_pack/blender_{4.0,4.5}.json` and the corresponding logs. The asset-QA and deformation tools are available for deliberate future use; their presence does not establish studio-ready character assets.
