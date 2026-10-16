# AI4薄肌

## 作为 Codex 项目使用

1. 在 Codex 中打开仓库目录。
2. 新会话先请求使用 `$ai4boji` 读取档案。默认读取仓库下 `data/`；若使用其他位置，每次传同一绝对 `--data-dir`。
3. 告诉 Codex 今日状态或实际完成情况。只有明确报告的数据才能写入记录。
4. Codex 调用 CLI 并读回校验。网页刷新后会看到同一份数据。

Skill 的完整字段协议见 [protocol.md](../../.agents/skills/ai4boji/references/protocol.md)。不要把真实记录复制到 GitHub issue。

## 常用操作

在仓库根目录执行：

```bash
python3 -m ai4boji context
python3 -m ai4boji plan
python3 -m ai4boji report --days 14 --format markdown
python3 -m ai4boji history plan:2026-10-16
```

保存一条用户确认的偏好：

```bash
python3 -m ai4boji memory <<'JSON'
{"id":"memory:weekend-time","text":"周末喜欢上午训练","kind":"preference","confirmed":true}
JSON
```

后续更正时沿用相同 ID，并传入读取到的 `expected_revision`。删除请求使用 `python3 -m ai4boji forget memory:weekend-time`，会永久删除该记忆和历史版本。

## 更新与重复提交

`profile` 是部分合并更新；`checkin`、`log` 和 `memory` 是完整替换更新。只更正某一项时，先读取旧值、合并更正，再提交。网页已执行版本检查。更新冲突应重新读取，不能用旧数据强制覆盖。

同一次实际训练必须沿用同一个 `id`。日志 ID 相同且内容相同的重试保持原版本；更正内容会增加版本。两次真正不同的训练才能用不同 ID。网页保存后会进入同一条记录的编辑模式，选择“取消”即可开始新记录。

## 计划的范围

首版按时间、器械、训练日和恢复反馈产生保守安排。文字目标、饮食条件及偏好由 Codex 解释，不会被本地模板自动理解。疼痛/限制会暂停力量计划。历史疼痛持续有效，直到更晚的日期明确报告无痛；如果原记录错误，应直接更正，而不是通过删掉档案中的文字绕过限制。

不同日期可在网页顶部切换查看；查看本身不生成或修改计划。旧计划可能因档案变化显示需要更新，历史版本可通过 CLI 查看。

## 数据和故障处理

- 端口占用：加 `--port 18765`，打开新打印的地址。
- 更换项目路径：把整个私有 `data/` 一起迁移，或继续使用绝对 `--data-dir`。
- 清空演示：先停止演示服务，移走 `.demo/` 后重启；切勿误操作真实 `data/`。
- 页面无法保存：确认服务仍在运行，从它打印的本机 URL 打开；刷新后重试，不要从静态 HTML 文件直接打开。
- 时区不可用：使用带系统时区数据库的 Python 环境；Windows 若缺少 IANA 数据，可安装 `tzdata`。常规 macOS/Linux 无需额外包。
- 备份：停止服务后复制数据目录。删除记忆不影响外部备份，也不清除已有 Codex 聊天。
- 该服务供单个本机用户使用，没有多账户系统、云同步或生产公网部署配置。
