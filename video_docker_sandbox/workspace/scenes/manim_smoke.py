from manim import *

class ManimSmoke(Scene):
    def construct(self):
        title = Text("CS + Math", font_size=54)
        circle = Circle(color=BLUE)
        self.play(Write(title))
        self.play(Transform(title, circle))
        self.wait(0.2)
