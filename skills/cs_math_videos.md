# CS & Math Explainers: Agent Generation Guide

Video type: `cs_math_educational`. The external agent chooses an installed engine. Manim Community is typically appropriate for equations, geometry, graphs and algorithms; Three.js/Remotion for interactive 3D or product-like explanation; hybrid shots are allowed.

## Correctness-first protocol
- Build a concept outline and a machine-checkable worked example before animation. For algorithms, specify input, invariant, state transitions and expected output. For math, verify each algebraic step and conditions on domain/notation.
- Present problem -> intuition -> step-by-step trace -> result -> complexity/limitations. Never animate an incorrect graph state or silently skip a prerequisite.
- Maintain a shared scene timeline, narration alignment, visible highlights and proof/trace steps. Allow reading time for formal expressions.
- Define aspect-safe zones for labels and equations. Do not let captions cover essential mathematical symbols.

## Manim recipe
Generate one independently renderable class per scene. Use explicit `self.play(..., run_time=...)` and `self.wait(...)`; separate visual primitives from data and computations. Keep stable IDs for graph vertices and equations between scenes. Choose graph layouts/transform origins deliberately. Validate Python syntax, imports and scene duration (only where Manim is installed), then render low-quality previews before final resolution.

## Borrowed iterative QA techniques
From mromidev: make keyframe stills / contact sheets and inspect legibility, camera, depth, color and framing against an original design brief. From nocodehack: use cheap pre-render gates to check object placement and collision where 3D geometry is involved; fix only scenes with concrete PASS/FAIL defects. Their upstream tooling is not automatically present.

## Checks
- Algorithm trace agrees with a reference implementation on the chosen input; test edge cases where feasible.
- Every symbolic transform is valid and notation consistent.
- No off-screen MathTex, occluded labels, excessive transitions, missing font/LaTeX dependency, invisible highlights or narration/scene overlap.
- Require implemented checks before reporting success. Keep diagnostics tied to scene IDs.
