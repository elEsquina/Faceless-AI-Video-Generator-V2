from manim import *

class GradientDescentIntroScene(Scene):
    def construct(self):
        title = Text("Gradient Descent", font_size=42, color=BLUE).to_edge(UP)
        subtitle = Text("Optimization Algorithm", font_size=24, color=GRAY).next_to(title, DOWN)
        self.play(Write(title), FadeIn(subtitle), run_time=1.5)
        
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[0, 9, 2],
            x_length=6,
            y_length=3.5,
            axis_config={"color": WHITE},
        ).shift(DOWN * 0.5)
        
        parabola = axes.plot(lambda x: x**2, color=YELLOW)
        func_label = MathTex("L(\\theta) = \\theta^2", font_size=32, color=YELLOW).next_to(parabola, RIGHT)
        
        self.play(Create(axes), Create(parabola), Write(func_label), run_time=2.0)
        self.wait(1.5)
