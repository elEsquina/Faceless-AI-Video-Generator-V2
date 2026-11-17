from manim import *

class GradientDescentConvergence(Scene):
    def construct(self):
        title = Text("Convergence at Global Minimum", font_size=36, color=GREEN).to_edge(UP)
        cond = MathTex("\\nabla L(\\theta^*) \\approx 0", font_size=32, color=YELLOW).next_to(title, DOWN)
        self.play(Write(title), Write(cond), run_time=2.0)
        
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[0, 9, 2],
            x_length=6,
            y_length=3.5,
            axis_config={"color": WHITE},
        ).shift(DOWN * 0.5)
        
        parabola = axes.plot(lambda x: x**2, color=YELLOW)
        min_dot = Dot(axes.coords_to_point(0, 0), color=GREEN, radius=0.14)
        min_label = Text("Optimal Parameter", font_size=24, color=GREEN).next_to(min_dot, DOWN)
        
        self.add(axes, parabola)
        self.play(FadeIn(min_dot), Write(min_label), run_time=2.0)
        
        box = SurroundingRectangle(min_label, color=YELLOW, buff=0.15)
        self.play(Create(box), run_time=2.0)
        self.wait(4.0)
