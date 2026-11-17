from manim import *

class GradientDescentStepsScene(Scene):
    def construct(self):
        title = Text("Iterative Descent", font_size=36, color=BLUE).to_edge(UP)
        formula = MathTex("\\theta_{t+1} = \\theta_t - \\eta \\nabla L(\\theta_t)", font_size=30, color=GREEN).next_to(title, DOWN)
        self.add(title, formula)
        
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[0, 9, 2],
            x_length=6,
            y_length=3.5,
            axis_config={"color": WHITE},
        ).shift(DOWN * 0.5)
        
        parabola = axes.plot(lambda x: x**2, color=YELLOW)
        self.add(axes, parabola)
        
        dot = Dot(axes.coords_to_point(2.4, 2.4**2), color=RED, radius=0.1)
        label = MathTex("\\theta_0", font_size=28, color=RED).next_to(dot, RIGHT)
        self.play(FadeIn(dot), Write(label), run_time=1.0)
        
        steps = [1.5, 0.9, 0.4, 0.1]
        for theta in steps:
            target = axes.coords_to_point(theta, theta**2)
            self.play(dot.animate.move_to(target), run_time=0.8)
        
        self.wait(0.8)
