from manim import *

class GradientDescentIntro(Scene):
    def construct(self):
        title = Text("Gradient Descent", font_size=42, color=BLUE).to_edge(UP)
        subtitle = Text("First-Order Optimization", font_size=26, color=GRAY).next_to(title, DOWN)
        self.play(Write(title), FadeIn(subtitle), run_time=2.0)
        
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[0, 9, 2],
            x_length=6,
            y_length=3.5,
            axis_config={"color": WHITE},
        ).shift(DOWN * 0.5)
        
        parabola = axes.plot(lambda x: x**2, color=YELLOW)
        func_label = MathTex("L(\\theta) = \\theta^2", font_size=32, color=YELLOW).next_to(parabola, RIGHT)
        
        self.play(Create(axes), Create(parabola), Write(func_label), run_time=3.0)
        
        dot = Dot(axes.coords_to_point(2.5, 6.25), color=RED, radius=0.1)
        label = MathTex("\\theta_0", font_size=28, color=RED).next_to(dot, RIGHT)
        self.play(FadeIn(dot), Write(label), run_time=2.0)
        self.wait(3.0)
