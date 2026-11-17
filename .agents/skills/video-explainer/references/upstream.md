# Optional Three.js motion sources

When developing procedural surfaces, product lighting or time-driven geometry beyond the staged cinematic utilities, consult the MIT [Three.js API reference](upstream/threejs/references/three-api.md), [troubleshooting](upstream/threejs/references/troubleshooting.md) and `examples/{product-spin,wave-grid}.mjs`. The selected OSS subtree is pinned in [SOURCE.json](upstream/threejs/SOURCE.json), with its [LICENSE](upstream/threejs/LICENSE) and [license note](upstream/threejs/LICENSE.note). Separately licensed GSAP/Remotion skill buckets were not copied.

Both examples were evaluated using the installed **Three.js r175**: geometry and camera hashes matched at repeated out-of-order times `[0,2,1,0,2]` and changed with time. That check used a renderer stub and is not a pixel-rendering or standalone-browser-driver verification. GPU/pixel identity across machines is not established.

Adapt geometry/material/camera ideas to React Three Fiber/Remotion, driving state from `useCurrentFrame()/fps` and preserving the staged `cinematic.tsx` utilities. The archived `UPSTREAM_SKILL.md`, `scripts/render.mjs` and `preflight.mjs` describe a separate browser/Playwright renderer and `videos3d/` layout. They are reference-only here: do not invoke that driver, its dependency-install commands or its output layout for MCP jobs. It is not an installed Omega engine. A future adapter would need explicit work and browser/asset-loading checks.

Use the existing preview/final Docker adapter and `jobs/ID/` paths, shared narration/caption timeline and actual frame QA. Keep the MIT notice and provenance with adapted code. The current software-WebGL renderer remains as configured; importing a Three.js example does not establish GPU acceleration.

Evidence: `video_docker_sandbox/workspace/jobs/7c231c5a/qa/skill_pack/threejs_state_checks.json`.
