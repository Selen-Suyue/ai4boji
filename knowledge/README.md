# AI4薄肌

## 知识来源与规则范围 / Sources and rule scope

资料核对日期 / Sources checked: **2026-10-16**.

- [WHO — Everyday actions for better health](https://www.who.int/europe/news-room/fact-sheets/item/everyday-actions-for-better-health-who-recommendations): provides general public-health activity guidance, including regular aerobic and muscle-strengthening activity. 一般健康活动建议，包括有氧与肌肉力量活动。
- [OpenAI — Build skills](https://learn.chatgpt.com/docs/build-skills): repository-local skill workflow integration. 仓库内 Skill 的接入方式。
- [OpenAI — Plugin architecture](https://developers.openai.com/plugins/concepts/plugins): workflow instructions and optional tool-backed integration. 工作流与后续可选工具接口。

WHO recommendations are population-level guidance, not a personalized prescription or validation of this application. WHO 没有为本项目背书，也没有验证本项目的具体动作和阈值。

## 项目自行制定的起步规则 / Project-authored starter rules

The `starter-0.1` rules, exercise cards, repetitions, time budgets, fatigue thresholds and decision priorities are project-authored conservative defaults. They have **not undergone professional clinical validation**. They are transparent software rules to support a beginner workflow, not a medical or rehabilitation model.

`starter-0.1` 的动作卡、组次、时间预算、疲劳阈值及优先级是项目自行制定的保守起步规则，**尚未经专业临床验证**。不应把它们描述为经科学验证的个体处方。

Rule priority / 规则优先级:

1. Known restrictions or unresolved pain → pause automatic strength planning. 有运动限制或未解决疼痛时，暂停自动力量安排。
2. Training already recorded today → recovery. 当天已有训练记录时，优先恢复。
3. Reported sleep < 6 hours, energy ≤ 2/5 or soreness ≥ 4/5 → recovery. 状态较差时采用恢复安排。
4. Training yesterday → recovery. 前一天训练后优先恢复。
5. Non-training weekday or available time < 15 minutes → comfortable light activity. 非训练日或时间很短时轻松活动。
6. Otherwise → a small set of beginner movements, with fewer exercises/sets when time is short. 其余情况按时间与器械生成少量基础动作。

Pain is not a diagnosis. Do not use missing pain data as proof of safety. Severe, sudden or persistent symptoms should be handled by appropriate health professionals; the product does not triage emergencies. 疼痛记录不是诊断，未报告疼痛也不代表可以确认安全。严重、突发或持续的不适应寻求相应专业帮助，本产品不进行急症分诊。

## 后续审阅 / Future review

Before expanding to goal-specific progression, clinical populations, pregnancy/postpartum, rehabilitation or dietary prescriptions, obtain qualified content review and add documented applicability, contraindications and scenario tests. Keep sources and review dates attached to new rules. 扩展更精细的负荷进阶、特殊人群或饮食处方前，应完成专业审阅并记录适用范围、限制及验证场景。
