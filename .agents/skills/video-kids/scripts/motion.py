"""Pure pose sampling in seconds. No cumulative transforms or wall clock."""
import math
ACTIONS={'idle','walk','run','sit','jump','wave','look','talk','sad','joy','reach'}


def sample(action,t):
    if action not in ACTIONS: raise ValueError(f'Unknown action: {action}')
    p={k:0. for k in ('arm.L','arm.R','leg.L','leg.R','head','ear.L','ear.R','body','lift','mouth','look')}
    p['head']=.035*math.sin(t*2)
    if action in ('walk','run'):
        phase=t*(9 if action=='run' else 5)
        a=.7 if action=='run' else .42
        for side,sign in (('L',1),('R',-1)):
            p['leg.'+side]=sign*a*math.sin(phase);p['arm.'+side]=-sign*a*.7*math.sin(phase)
        p['lift']=(.12 if action=='run' else .045)*abs(math.sin(phase));p['body']=.1
        p['ear.L']=.12*math.sin(phase-.4);p['ear.R']=.12*math.sin(phase+.4)
    elif action=='sit': p.update({'leg.L':-1.1,'leg.R':-1.1,'arm.L':-.4,'arm.R':-.4,'body':.18})
    elif action=='jump':
        u=max(0,min(1,t));p['lift']=.7*4*u*(1-u);p['arm.L']=p['arm.R']=-.6*math.sin(math.pi*u)
    elif action=='wave': p['arm.R']=-2.2+.25*math.sin(t*9);p['head']=-.1
    elif action=='look': p['look']=.5*math.sin(t*1.8)
    elif action=='talk': p['mouth']=.45+.4*math.sin(t*15);p['arm.L']=-.35+.12*math.sin(t*4)
    elif action=='sad': p['head']=.32;p['body']=.13;p['ear.L']=p['ear.R']=.35
    elif action=='joy': p['arm.L']=p['arm.R']=-1.8;p['lift']=.07*abs(math.sin(t*7));p['head']=-.15
    elif action=='reach': p['arm.R']=-1.35;p['body']=.12;p['look']=-.15
    return p
