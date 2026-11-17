from manim import *

class BinarySearchFound(Scene):
    def construct(self):
        title = Text("Step 2: Target Found!", font_size=36, color=GREEN).to_edge(UP)
        self.play(Write(title), run_time=1.5)
        
        values = [3, 8, 14, 27, 35, 49, 62]
        cells = VGroup()
        for i, val in enumerate(values):
            sq = Square(side_length=1.0, color=WHITE, fill_opacity=0.2, fill_color=BLUE)
            num = Text(str(val), font_size=28, color=WHITE)
            idx = Text(f"[{i}]", font_size=18, color=GRAY).next_to(sq, DOWN * 0.7)
            cells.add(VGroup(sq, num, idx))
            
        cells.arrange(RIGHT, buff=0.2).shift(DOWN * 0.2)
        for i in range(4):
            cells[i].set_opacity(0.25)
        self.add(cells)
        
        p_mid = Text("Mid (49)", font_size=22, color=GREEN).next_to(cells[5], UP * 0.8)
        self.play(FadeIn(p_mid), run_time=1.5)
        
        highlight_box = SurroundingRectangle(cells[5], color=GREEN, buff=0.1, stroke_width=4)
        match_text = MathTex(r"A[5] = 49 == T \quad \checkmark", font_size=30, color=GREEN).shift(DOWN * 1.8)
        self.play(Create(highlight_box), Write(match_text), run_time=2.0)
        
        complexity = MathTex(r"\text{Time Complexity: } \mathcal{O}(\log_2 n)", font_size=32, color=YELLOW).shift(DOWN * 2.6)
        self.play(Write(complexity), run_time=2.0)
        self.wait(3.0)
