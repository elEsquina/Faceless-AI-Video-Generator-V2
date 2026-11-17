"""Manim CE production building blocks. Reserve bottom 18% for captions."""
from manim import *
INK, ACCENT, GOLD, BACKGROUND = '#EAF2FF', '#5DE4C7', '#FFD275', '#101D32'


def fit(mob, width=12.4, height=5.0, center=UP * .45):
    return mob.scale(min(1, width/max(mob.width,.001), height/max(mob.height,.001))).move_to(center)


def heading(text, subtitle=None):
    title = Text(text, font_size=38, color=INK).to_edge(UP, buff=.32)
    if subtitle is None: return title
    sub = Text(subtitle, font_size=22, color=ACCENT).next_to(title, DOWN, buff=.12)
    return VGroup(title, sub)


def _fade_replace(scene,old,new,**kwargs):
    duration=kwargs.pop('run_time',1)
    frames=max(2,int(round(duration*config.frame_rate)))
    first=frames//2
    scene.play(FadeOut(old),run_time=first/config.frame_rate,**kwargs)
    scene.remove(old)
    scene.play(FadeIn(new),run_time=(frames-first)/config.frame_rate,**kwargs)


def replace_text(scene,old,new,**kwargs):
    """Disjoint fades avoid unreadable text morphs; return the new identity."""
    new.move_to(old)
    _fade_replace(scene,old,new,**kwargs)
    return new


def replace_object(scene,old,new,**kwargs):
    """ReplacementTransform for shapes; do not use whole-string glyph morphs."""
    new.move_to(old)
    scene.play(ReplacementTransform(old,new),**kwargs)
    scene.remove(old)
    return new


def replace_equation(scene,old,new,match=None,**kwargs):
    """Match explicit tokens; use disjoint fades for unstructured whole strings."""
    new.move_to(old)
    if match is None:
        match=len(getattr(old,'tex_strings',[]))>1 and len(getattr(new,'tex_strings',[]))>1
    if match:
        scene.play(TransformMatchingTex(old,new),**kwargs)
    else:
        _fade_replace(scene,old,new,**kwargs)
    scene.remove(old)
    return new


def clear_group(scene, group, **kwargs):
    scene.play(FadeOut(group), **kwargs)
    scene.remove(group, *group.submobjects)


def array(values, active=None, cell=.75):
    cells = VGroup()
    for i, value in enumerate(values):
        box = RoundedRectangle(width=cell,height=cell,corner_radius=.10,color=ACCENT if i==active else '#59728F')
        box.set_fill(ACCENT if i==active else '#1D3550',opacity=.22)
        cells.add(VGroup(box,Text(str(value),font_size=26,color=INK).move_to(box)))
    return cells.arrange(RIGHT,buff=.10)


def network(layers=(3,4,2),width=9.5,height=3.4):
    nodes=VGroup()
    for i,n in enumerate(layers):
        column=VGroup(*[Circle(.13,color=ACCENT,fill_opacity=.6) for _ in range(n)])
        column.arrange(DOWN,buff=max(.18,height/max(n,1)-.26))
        column.move_to([(i/max(1,len(layers)-1)-.5)*width,.3,0]);nodes.add(column)
    edges=VGroup(*[Line(a.get_center(),b.get_center(),color='#4F6987',stroke_width=1.4)
                   for l,r in zip(nodes,nodes[1:]) for a in l for b in r])
    return VGroup(edges,nodes)


def graph(labels,edges,positions):
    vertices=VGroup(*[VGroup(Circle(.25,color=ACCENT,fill_color=BACKGROUND,fill_opacity=1),
                        Text(str(label),font_size=22)).move_to(positions[label]) for label in labels])
    lookup=dict(zip(labels,vertices))
    links=VGroup(*[Line(lookup[a].get_center(),lookup[b].get_center(),color='#6C8DA9') for a,b in edges])
    return VGroup(links,vertices)


def emphasize(scene,obj,color=GOLD,**kwargs):
    scene.play(Circumscribe(obj,color=color,fade_out=True),**kwargs)


def descent(x,rate=.22):
    """L(x)=x², derivative 2x; convergence requires 0<rate<1."""
    if not 0<rate<1: raise ValueError('Use 0 < learning rate < 1 for this quadratic')
    return x-rate*2*x


def bounds(mob,camera_frame=None):
    w,h,c=(config.frame_width,config.frame_height,ORIGIN) if camera_frame is None else (camera_frame.width,camera_frame.height,camera_frame.get_center())
    return [(mob.get_left()[0]-c[0])/w+.5,.5-(mob.get_top()[1]-c[1])/h,
            (mob.get_right()[0]-c[0])/w+.5,.5-(mob.get_bottom()[1]-c[1])/h]


def swap_cells(scene,cells,i,j,run_time=.6):
    """Animate an algorithmic swap and update logical index order as well as positions."""
    if not (0<=i<len(cells) and 0<=j<len(cells)):raise IndexError('Array index out of range')
    if i==j:return cells
    a,b=cells[i],cells[j]
    scene.play(Swap(a,b,path_arc=PI/2),run_time=run_time)
    cells.submobjects[i],cells.submobjects[j]=b,a
    return cells


def visit_indices(scene,cells,indices,run_time=.3):
    """Explicit visit order is supplied by the independently verified algorithm."""
    for index in indices:
        if not 0<=index<len(cells):raise IndexError('Array index out of range')
        scene.play(Indicate(cells[index],color=GOLD),run_time=run_time)
