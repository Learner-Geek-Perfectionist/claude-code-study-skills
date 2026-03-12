# 安装说明

## 安装 Skill

```bash
cp SKILL.md ~/.claude/skills/study-master/
```

## 安装 Hook

```bash
cp hooks/format-validator.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/format-validator.sh
```

## 验证安装

重启 Claude Code 后，skill 会自动加载。

使用以下命令测试 hook：

```bash
~/.claude/hooks/format-validator.sh <file.md>
```

## 使用

```bash
/study-master <topic>
/study-master <topic> --source <path>
```
