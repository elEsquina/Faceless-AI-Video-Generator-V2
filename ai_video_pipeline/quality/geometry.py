"""Deterministic projected layout checks. Not an artistic quality classifier.

Input is sampled actual viewport geometry, normalized top-left coordinates.
Only declared collision peers are checked; containment (labels inside panels) is legal.
"""
import math


def overlap(a,b):
    return max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))


def check_layout(samples, caption_top=.82):
    if not isinstance(samples,list) or not samples:
        raise ValueError('Layout metadata needs nonempty rendered samples')
    issues=[]
    for sample in samples:
        objects=sample['objects']
        if not objects:issues.append('sample has no measured objects')
        ids=[o['id'] for o in objects]
        if len(ids)!=len(set(ids)):issues.append('duplicate object identities')
        for o in objects:
            b=o['bounds']
            if len(b)!=4 or not all(math.isfinite(v) for v in b) or b[2]<=b[0] or b[3]<=b[1]:
                issues.append(f"{o['id']}: invalid projected bounds");continue
            if o.get('important',True):
                if min(b[:2])<.015 or max(b[2:])>.985:issues.append(f"{o['id']}: camera clipping / unsafe framing")
                if b[3]>caption_top:issues.append(f"{o['id']}: caption obstruction")
                if (b[2]-b[0])*(b[3]-b[1])<o.get('min_area',.002):issues.append(f"{o['id']}: important object too small")
            if o.get('kind') in ('text','equation') and o.get('font_px',99)<22:
                issues.append(f"{o['id']}: unreadable text size")
        for i,a in enumerate(objects):
            for b in objects[i+1:]:
                if a.get('collision_group') and a.get('collision_group')==b.get('collision_group') and overlap(a['bounds'],b['bounds'])>.0001:
                    issues.append(f"{a['id']} / {b['id']}: layout collision at {sample.get('time',0)}s")
        subjects=[o for o in objects if o.get('role')=='subject']
        if subjects:
            union=[min(o['bounds'][0] for o in subjects),min(o['bounds'][1] for o in subjects),max(o['bounds'][2] for o in subjects),max(o['bounds'][3] for o in subjects)]
            if (union[2]-union[0])*(union[3]-union[1])<.09:issues.append('subject composition underuses viewport')
    return list(dict.fromkeys(issues))


def check_continuity(samples):
    """Check declared cast identities and measured interaction contacts across samples."""
    issues=[];identities={};styles=set()
    for frame in samples:
        if frame.get('style'):styles.add(frame['style'])
        for actor in frame.get('characters',[]):
            name=actor['id'];identity=actor.get('appearance_hash')
            if identity:
                if name in identities and identity!=identities[name]:issues.append(f'{name}: inconsistent character identity')
                identities[name]=identity
            if not actor.get('expression'):issues.append(f'{name}: missing declared expression')
        for contact in frame.get('interactions',[]):
            a,b=contact['hand'],contact['target']
            distance=math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
            if distance>contact.get('tolerance',.06):issues.append(f"{contact['id']}: broken interaction contact")
        if frame.get('camera_jump') and not frame.get('planned_cut'):
            issues.append('unplanned abrupt camera transition')
    if len(styles)>1:issues.append('inconsistent declared visual style')
    return list(dict.fromkeys(issues))
