# Generation Skill: Computer Science and Mathematics Educational Videos

This guide outlines rules, mathematical rigor, and code generation standards for Computer Science, engineering, and mathematics instructional videos.

---

## 1. Domain Profile

- **Target Audience**: Software engineers, university students, STEM learners.
- **Tone**: Rigorous, analytical, visual, intuitive, and lucid.
- **Pedagogical Arc**:
  1. *Problem Formulation* (15%): Clear mathematical or algorithmic problem statement.
  2. *Intuition / Geometric View* (30%): A visual illustration that builds geometric intuition.
  3. *Step-by-Step Transformation* (40%): Mathematical derivation, pseudocode step execution, or graph traversal.
  4. *Complexity / Takeaway* (15%): Time/space complexity ($O(V + E)$), edge cases, and recap.

---

## 2. Recommended Engine Selection

- **Primary**: **Manim (Community Edition)** for programmatic 2D/3D mathematical animations, LaTeX rendering, graph theory visualizers, and linear algebra transforms.

---

## 3. Script & Audio Pacing

- **Narration Speed**: Deliberate, measured (approx. 120–140 words per minute) to allow viewers to absorb formal definitions.
- **Voice Style**: Academic, calm, clear, and reassuring.
- **Sound Effects (SFX)**: Minimalist acoustic feedback (chalk sound, subtle click on state change, chime on proof step completion).
- **Background Music (BGM)**: Minimalist ambient electronic or classical piano ducked by -18dB.

---

## 4. Shared Timeline Guidelines

- Align narration pauses with formula transformations.
- Highlight specific equation symbols or graph nodes exactly when mentioned in the voiceover.
- Keep subtitle terminology aligned with standard notation.

---

## 5. Animation Code Scaffold (Manim Python Example)

When generating Manim code in `scenes/scene_XX/scene.py`:

```python
from manim import *

class MathCsScene(Scene):
    def construct(self):
        # 1. Title / Problem Statement
        title = Text("Dijkstra's Algorithm", font_size=40).to_edge(UP)
        self.play(Write(title), run_time=1.5)

        # 2. Mathematical formulation / Graph setup
        graph_nodes = [1, 2, 3, 4]
        graph_edges = [(1, 2), (2, 3), (3, 4), (1, 3)]
        graph = Graph(graph_nodes, graph_edges, layout="circular").scale(1.2)
        
        self.play(Create(graph), run_time=2.0)
        self.wait(1.0)

        # 3. Traversal / Transformation step
        self.play(graph[1].animate.set_color(YELLOW), run_time=1.0)
        self.wait(1.5)
```
