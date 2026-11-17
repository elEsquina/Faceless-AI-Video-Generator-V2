from manim import *

class GradientDescentSteps(Scene):
    def construct(self):
        title = Text("Iterative Descent Steps", font_size=36, color=BLUE).to_edge(UP)
        formula = MathTex("\\theta_{t+1} = \\theta_t - \\eta \\nabla L(\\theta_t)", font_size=30, color=GREEN).next_to(title, DOWN)
        self.play(Write(title), Write(formula), run_time=2.0)
        
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[0, 9, 2],
            x_length=6,
            y_length=3.5,
            axis_config={"color": WHITE},
        ).shift(DOWN * 0.5)
        
        parabola = axes.plot(lambda x: x**2, color=YELLOW)
        self.play(Create(axes), Create(parabola), run_time=2.0)
        
        dot = Dot(axes.coords_to_point(2.5, 6.25), color=RED, radius=0.12)
        self.play(FadeIn(dot), run_time=1.0)
        
        steps = [1.8, 1.3, 0.9, 0.55, 0.25, 0.08]
        for theta in steps:
            target = axes.coords_to_point(theta, theta**2)
            self.play(dot.animate.move_to(target), run_time=0.7)
        
        self.wait(0.8)
