from manim import *

class BinarySearchIntro(Scene):
    def construct(self):
        title = Text("Binary Search Algorithm", font_size=40, color=BLUE).to_edge(UP)
        subtitle = Text("Efficient Search in a Sorted Array", font_size=24, color=GRAY).next_to(title, DOWN)
        self.play(Write(title), FadeIn(subtitle), run_time=2.0)
        
        target_label = MathTex(r"\text{Target: } T = 49", font_size=32, color=YELLOW).shift(UP * 1.5)
        self.play(Write(target_label), run_time=1.5)
        
        values = [3, 8, 14, 27, 35, 49, 62]
        cells = VGroup()
        for i, val in enumerate(values):
            sq = Square(side_length=1.0, color=WHITE, fill_opacity=0.2, fill_color=BLUE)
            num = Text(str(val), font_size=28, color=WHITE)
            idx = Text(f"[{i}]", font_size=18, color=GRAY).next_to(sq, DOWN * 0.7)
            cell = VGroup(sq, num, idx)
            cells.add(cell)
            
        cells.arrange(RIGHT, buff=0.2).shift(DOWN * 0.5)
        self.play(Create(cells), run_time=3.5)
        self.wait(3.0)
