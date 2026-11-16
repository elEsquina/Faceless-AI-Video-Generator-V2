# AI Video Pipeline: Skill Routing (Codex / Antigravity)

Use the external coding agent as the LLM director, not an internal API. Read `prompt.md` and exactly one of `skills/kids_stories.md`, `skills/explanatory_videos.md`, or `skills/cs_math_videos.md` based on the requested type. The user selects content type, not the engine; the director chooses from installed capabilities per scene. Use `ai_video_pipeline/core/skills.py` only as a future Python locator interface; it is currently a scaffold.

When building animation code, prefer using existing adapters and templates; never claim a renderer is functional merely because its Python class exists. Generate job artifacts only in `jobs/<job_id>/`. Keep `request.json`, `plan.json`, `audio_plan.json`, and scene code synchronized using one timeline. Never call paid LLM APIs, fetch assets, install dependencies, run untrusted generated code, or begin long renders without explicit user authorization. For installation tasks, change only skill/instruction files and preserve Python scaffolds.

For job generation: read skill -> create job through available MCP interface (only if implemented) -> write plan and scenes -> validate -> run geometry/code QA -> draft frames -> inspect and fix specific scenes -> final render and audio mix. If MCP is still stubbed, state clearly that execution is unavailable; do not fabricate successful calls.

Source inspiration (adapted, not a copy):
- https://github.com/mromidev/claude-animated-shorts (Three.js+Remotion, style bible, measured still/frame review)
- https://github.com/nocodehack/nocodehack-roblox-engine (structured beats, Blender scene gates, preview-first iterative fixes)

The upstream repositories' character assets, reference frames, example scenes, and engine implementations are NOT installed in this bundle. Consult their licenses and any asset-specific terms before importing them.
