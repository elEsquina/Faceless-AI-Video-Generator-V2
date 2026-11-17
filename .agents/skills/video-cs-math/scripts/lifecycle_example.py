"""Executable Manim lifecycle and diagram smoke example, unrelated to acceptance topics."""
from manim import *
from _production.math_stage import replace_text, replace_equation, clear_group, graph, array, network, fit, replace_object, swap_cells, visit_indices

class LifecycleExample(Scene):
    def construct(self):
        title=Text('Lifecycle / layout',font_size=32).to_edge(UP)
        self.add(title)
        old=Text('Stage one',font_size=26).shift(UP*2)
        self.add(old)
        current=replace_text(self,old,Text('Stage two',font_size=26),run_time=.2)
        assert old not in self.mobjects and current in self.mobjects
        eq=MathTex('x','+','x','=','2x').shift(UP)
        self.add(eq)
        eq=replace_equation(self,eq,MathTex('2x','=','x','+','x'),run_time=.2)
        blocks=array([3,1,4],active=1).shift(DOWN*.2)
        self.add(blocks)
        single=MathTex('a+b').shift(DOWN*1.3)
        self.add(single)
        replaced=replace_equation(self,single,MathTex('b+a'),run_time=.2)
        assert single not in self.mobjects and replaced in self.mobjects
        self.remove(replaced)
        shape=Circle(.18).shift(DOWN*1.4);self.add(shape)
        changed=replace_object(self,shape,Square(.35),run_time=.2)
        assert shape not in self.mobjects and changed in self.mobjects
        self.remove(changed)
        swap_cells(self,blocks,0,2,run_time=.2)
        assert blocks[0][1].text=='4' and blocks[2][1].text=='3'
        assert blocks[0].get_center()[0] < blocks[2].get_center()[0]
        visit_indices(self,blocks,[0,1,2],run_time=.1)
        self.wait(.2)
        clear_group(self,VGroup(blocks,current,eq),run_time=.2)
        assert blocks not in self.mobjects and current not in self.mobjects
        tree=graph(['A','B','C'],[('A','B'),('A','C')],{'A':[0,1,0],'B':[-2,-.5,0],'C':[2,-.5,0]})
        self.add(fit(tree));self.wait(.2);clear_group(self,tree,run_time=.2)
        nn=fit(network((2,3,1)));self.add(nn);self.wait(.2)
