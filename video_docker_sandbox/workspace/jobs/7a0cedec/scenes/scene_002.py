from manim import *

class BinarySearchFirstStep(Scene):
    def construct(self):
        title = Text("Step 1: Check the Midpoint", font_size=36, color=BLUE).to_edge(UP)
        self.play(Write(title), run_time=1.5)
        
        target_label = MathTex(r"T = 49 \quad (\text{Target})", font_size=28, color=YELLOW).next_to(title, DOWN)
        self.play(FadeIn(target_label), run_time=1.0)
        
        values = [3, 8, 14, 27, 35, 49, 62]
        cells = VGroup()
        for i, val in enumerate(values):
            sq = Square(side_length=1.0, color=WHITE, fill_opacity=0.2, fill_color=BLUE)
            num = Text(str(val), font_size=28, color=WHITE)
            idx = Text(f"[{i}]", font_size=18, color=GRAY).next_to(sq, DOWN * 0.7)
            cells.add(VGroup(sq, num, idx))
            
        cells.arrange(RIGHT, buff=0.2).shift(DOWN * 0.2)
        self.add(cells)
        
        p_low = Text("Low", font_size=20, color=GREEN).next_to(cells[0], UP * 0.8)
        p_high = Text("High", font_size=20, color=RED).next_to(cells[6], UP * 0.8)
        p_mid = Text("Mid (27)", font_size=20, color=YELLOW).next_to(cells[3], UP * 0.8)
        self.play(FadeIn(p_low), FadeIn(p_high), FadeIn(p_mid), run_time=1.5)
        
        box = SurroundingRectangle(cells[3], color=YELLOW, buff=0.08)
        comp_text = MathTex(r"49 > 27 \implies \text{Search Right}", font_size=26, color=YELLOW).shift(DOWN * 2.2)
        self.play(Create(box), Write(comp_text), run_time=2.0)
        
        left_half = VGroup(cells[0], cells[1], cells[2], cells[3], p_low, p_mid, box)
        self.play(left_half.animate.set_opacity(0.25), run_time=1.5)
        
        new_low = Text("New Low", font_size=20, color=GREEN).next_to(cells[4], UP * 0.8)
        self.play(FadeIn(new_low), run_time=1.0)
        self.wait(1.5)
