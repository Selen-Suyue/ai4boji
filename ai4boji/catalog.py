"""Conservative starter exercise cards. All prescriptions are project rules."""
def bi(zh, en):
    return {'zh-CN': zh, 'en': en}


EXERCISES = {
    'chair-squat': {'name': bi('坐椅深蹲', 'Chair squat'), 'pattern': 'squat',
        'cue': bi('椅子靠墙固定，缓慢坐下再站起，膝盖朝向脚尖。', 'Secure a chair against a wall. Sit down slowly, then stand; knees follow toes.'),
        'alternative': bi('减少下蹲幅度；仍不适则停止。', 'Use a smaller range; stop if uncomfortable.')},
    'wall-pushup': {'name': bi('墙壁俯卧撑', 'Wall push-up'), 'pattern': 'push',
        'cue': bi('双手扶墙，身体保持一条直线，缓慢屈肘再推开。', 'Place hands on a wall, keep the body straight, bend elbows slowly and press away.'),
        'alternative': bi('站得更靠近墙，减轻难度。', 'Stand closer to the wall to reduce difficulty.')},
    'hip-hinge': {'name': bi('徒手髋折叠', 'Bodyweight hip hinge'), 'pattern': 'hinge',
        'cue': bi('膝盖微屈，臀部向后，背部保持自然，不追求下探深度。', 'Soften knees, move hips back, keep a neutral back and a comfortable range.'),
        'alternative': bi('缩小幅度，先练习臀部向后移动。', 'Use a small range and practise moving the hips back.')},
    'bird-dog': {'name': bi('鸟狗式', 'Bird dog'), 'pattern': 'core',
        'cue': bi('四点支撑，缓慢伸出对侧手脚，保持躯干稳定；次数按每侧计算。', 'From hands and knees, slowly extend opposite arm and leg; keep the trunk still. Reps are per side.'),
        'alternative': bi('每次只抬一只手或一条腿。', 'Lift just one arm or one leg at a time.')},
    'db-row': {'name': bi('支撑式哑铃划船', 'Supported dumbbell row'), 'pattern': 'pull',
        'cue': bi('一手支撑稳定平面，轻重量，肘部向后拉，躯干不转动；每侧完成。', 'Support one hand on a stable surface. With a light weight, pull the elbow back without twisting; repeat each side.'),
        'alternative': bi('先用空手练习轨迹；不使用不稳的桌椅。', 'Practise unloaded first; do not use unstable furniture.')},
}


TEXT = {
    'training': bi('全身基础训练', 'Full-body foundations'),
    'recovery': bi('恢复与轻松活动', 'Recovery & easy movement'),
    'hold': bi('先确认身体状况', 'Check your condition first'),
    'scheduled': bi('今天是你选择的训练日。', 'Today is one of your chosen training days.'),
    'off_day': bi('今天没有安排力量训练，按舒适程度轻松活动。', 'No strength session is scheduled today. Move gently as comfortable.'),
    'yesterday': bi('昨天记录了训练，今天安排恢复，避免连续叠加。', 'Training was recorded yesterday; today is reserved for recovery.'),
    'completed_today': bi('今天已经记录了训练，接下来优先恢复，不叠加第二次力量安排。', 'Training is already recorded today. Prioritize recovery instead of adding another strength session.'),
    'fatigue': bi('今天的精力、睡眠或酸痛反馈提示需要放轻松。', 'Your energy, sleep or soreness check-in calls for an easier day.'),
    'short': bi('可用时间较少，今天采用简短活动安排。', 'Your available time is short; use a brief activity session today.'),
    'missing': bi('尚无今日状态记录，暂用保守安排；开始前请补充状态。', 'No check-in yet. This is a conservative draft; check in before starting.'),
    'pain': bi('存在疼痛、运动限制或待确认的不适。暂停自动力量安排，先与合格专业人士确认适合的活动。', 'Pain, an exercise restriction or unresolved discomfort is recorded. Automated strength planning is paused; clarify suitable activity with a qualified professional.'),
    'warmup': bi('先用约 5 分钟轻松走动、活动关节；保持呼吸顺畅。', 'Start with about 5 minutes of easy walking and comfortable joint movement; breathe freely.'),
    'effort': bi('动作保持可控，每组结束时应感觉还能完成约 3–4 次；出现疼痛即停止。', 'Keep repetitions controlled and finish each set feeling you could do about 3–4 more; stop with pain.'),
    'nutrition': bi('规律吃饭，每餐搭配蛋白质来源、蔬菜与主食。先记录能坚持的饮食习惯，无需追求极端限制。', 'Eat regular meals with a protein source, vegetables and a staple carbohydrate. Focus on sustainable habits without extreme restriction.'),
    'cooldown': bi('结束后慢走、平稳呼吸，记录实际完成和感受。', 'Finish with an easy walk, settle your breathing and record what you actually did.'),
    'review_empty': bi('这段时间尚无训练记录。先完成一次简短记录，让后续建议有依据。', 'No session records in this period. Start with a brief record to inform future guidance.'),
    'review': bi('根据实际完成和感受复盘；缺失日期保持未知。下周安排可交给 Codex 结合这些记录讨论。', 'Review actual activity and how it felt. Missing days remain unknown. Discuss next week with Codex using these records.'),
}


def localize(value, lang):
    if isinstance(value, dict):
        if set(value) == {'zh-CN', 'en'}:
            return value[lang]
        return {k: localize(v, lang) for k, v in value.items()}
    if isinstance(value, list):
        return [localize(v, lang) for v in value]
    return value
