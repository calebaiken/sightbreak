"""UNEXECUTED construction proposal; not imported by production or old tests.

Compile the synthetic constructor's required producer operations in source order.
This is generated format data, not a driver run, physical history or gameplay
proof. Keep original 0f478 constructor/results exact. Pending independent review.
"""
import copy


def producer_action_plan(result, old_actions, ocr_commands, started):
    """Replacement construction step before the fresh fixture serializes JSON.

    No candidate checker is imported or consulted. Operation slots lie inside
    the already recorded command/close intervals. Captures, OCR bytes and all
    original-failure.bin/fault injection behavior are preserved by the caller.
    """
    plan=[]
    template=old_actions[0]
    pauses={row['capture']:row for row in result['hud_analysis_pauses']}
    fences=result['phase_capture_fences'];reload=result['native_reload']
    settings=result['native_settings_resume'];focus=result['native_focus_recovery']
    hud_ocr={'05-after-fire':(1,2),'06-after-reload':(3,4),'06e-purchased-smg':(6,7),
             '06f-switched-sidearm':(8,9),'06g-switched-primary':(10,11),'07d-explicit-resume':(14,15)}
    ui_ocr={'06d-funded-requisition':(5,),'07-field-menu':(12,),
            '07b-field-settings':(13,),'07d-explicit-resume':(16,)}
    def action(event,**fields):
        row=copy.deepcopy(template)
        for key in ('capture','dimensions','state','label'):row.pop(key,None)
        row.update(event=event,held_keys=[]);row.update(fields);plan.append(('action',row))
    def observed(label,state,budget=5):
        action('wait_begin',label=label,_budget=budget)
        action('wait_completed',label=label)
        action('offline_observation',label=label,state=copy.deepcopy(state))
    def ocr(number):plan.extend((('ocr_start',number),('ocr_finish',number)))
    def key(name,down):
        action('key_before',key=name,down=down,held_keys=[] if down else [name])
        action('key_after',key=name,down=down,held_keys=[name] if down else [])
    def before_capture(name):
        if name in fences:
            fence=fences[name]
            plan.append(('fence_until',name))
            label=('Natural exported round completion' if name=='06c-next-round'
                   else 'Reopened process loaded profile into ordinary offline match')
            action('wait_begin',label=label,_budget=('fence',name));action('wait_completed',label=label)
            for field,label in [('acknowledged','Named living buy phase'),('ready','Two drawn frames before named capture'),('before_capture','Fresh named context immediately before capture')]:
                observed(label+': '+name,fence[field],('fence',name))
        if name=='05-after-fire':observed('Authoritative depleted sidearm and two drawn frames',reload['before'])
        if name=='06-after-reload':
            plan.append(('reload_input',None));key('r',True)
            observed('Real R input starts authoritative offline reload',reload['started']);key('r',False)
            observed('Authoritative offline reload completion',reload['completed'],15)
            observed('Two rendered frames after authoritative reload transfer',reload['capture_ready'])
            plan.append(('reload_wall',None))
        if name=='07d-explicit-resume':
            observed('Fresh paused player after native settings change',settings['paused_after_settings'])
            plan.append(('settings_until',None))
            key('Escape',True)
            observed('Actual living player explicitly resumes after field settings',settings['resumed'],'settings')
            action('key_after',key='Escape',down=False,scope='field_settings_resume')
            observed('Two drawn frames after explicit native settings resume',settings['capture_ready'],'settings')
        if name=='11a-restored-focus-still-paused':
            observed('Fresh stock match reaches a living active player before native focus loss',focus['context_fence']['baseline'],60)
            observed('Game consumed physical W and LMB before native focus loss',focus['held_input_acknowledged'],10)
            action('native_focus_held_input_acknowledged',state=copy.deepcopy(focus['held_input_acknowledged']))
            observed('Native focus loss pauses actual offline match',focus['lost'],10)
            observed('Actual game observes restored focus',focus['restored_paused'],10)
        if name=='11b-resumed-held-input-neutral':
            rows=focus['held_neutral_samples']
            observed('Explicit resume with W and LMB still physically held',rows[0],10)
            for index,row in enumerate(rows[1:]):
                label=('Neutral held input while ordinary inertia settles' if index<len(rows)-3
                       else 'Fresh held-input guard sample '+str(index-(len(rows)-3)+1))
                observed(label,row,10)
        if name=='11c-fresh-press-movement':
            observed('Released held focus-test controls',focus['released'],10)
            key('w',True)
            observed('Fresh W press moves actual player after focus recovery',focus['fresh_press_movement'],10)
            key('w',False)
    def after_capture(name):
        if name in fences:
            for field,label in [('after_capture_barrier','Observation barrier after raw capture'),('after_capture','Fresh named context beyond post-capture barrier')]:
                observed(label+': '+name,fences[name][field],('fence',name))
            plan.append(('fence_remaining',name))
        if name in hud_ocr:
            receipt=pauses[name]
            key('Escape',True)
            action('key_after',key='Escape',down=False,scope='saved_hud_analysis')
            observed('Native pause before saved-HUD OCR: '+name,receipt['paused'],10)
            for number in hud_ocr[name]:ocr(number)
            observed('Fresh paused observation after saved-HUD OCR: '+name,receipt['after_analysis'])
            if receipt['resume_after_analysis']:
                action('key_after',key='Escape',down=True,scope='saved_hud_analysis_cleanup',held_keys=['Escape'])
                action('key_after',key='Escape',down=False,scope='saved_hud_analysis')
                observed('Explicit native resume after saved-HUD OCR: '+name,receipt['resumed'],10)
        for number in ui_ocr.get(name,()):ocr(number)
    for row in old_actions:
        if row['event']=='capture_begin':before_capture(row['capture'])
        plan.append(('action',copy.deepcopy(row)))
        if row['event']=='capture_end':after_capture(row['capture'])
    # Native process scopes stay separate. The source command/close observations
    # are actual synchronous fixture callbacks, not invented Windows receipts.
    split=next(index for index,(kind,row) in enumerate(plan) if kind=='action' and row.get('event')=='capture_begin' and row.get('capture')=='09-reopened-menu')
    actions=[];settings_until=None
    for index,nodes in enumerate((plan[:split],plan[split:])):
        left=result['commands'][index]['started_seconds']
        right=result['shutdown_study_observations'][index]['request_before_monotonic']-started
        if not left<right:raise ValueError('fixture process interval has no operation slots')
        for ordinal,(kind,value) in enumerate(nodes,1):
            seconds=left+(right-left)*ordinal/(len(nodes)+1)
            if kind=='action':
                budget=value.pop('_budget',None)
                if budget is not None:
                    if type(budget) is tuple:budget=fences[budget[1]]['absolute_deadline_monotonic']-started-seconds
                    elif budget=='settings':budget=settings_until-started-seconds
                    value['budget_seconds']=budget
                value['seconds']=seconds;actions.append(value)
            elif kind=='ocr_start':ocr_commands[value-1]['started_seconds']=seconds
            elif kind=='ocr_finish':ocr_commands[value-1]['finished_seconds']=seconds
            elif kind=='reload_input':reload['input_seconds']=seconds
            elif kind=='reload_wall':reload['wall_seconds_after_input']=seconds-reload['input_seconds']
            elif kind=='fence_until':fences[value]['absolute_deadline_monotonic']=min(started+300,started+seconds+fences[value]['transition_watchdog_seconds'])
            elif kind=='fence_remaining':fences[value]['remaining_original_budget_seconds']=fences[value]['absolute_deadline_monotonic']-started-seconds
            elif kind=='settings_until':settings_until=min(started+300,started+seconds+10)
    return actions
