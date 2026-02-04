# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## What this repo is
This repository is a **Claude Code skill** implemented entirely as Markdown, adapted for academic medical writing.

The "runtime" artifact is `SKILL.md`: Claude Code reads the YAML frontmatter (metadata + allowed tools) and the prompt/instructions that follow.

`README.md` is for humans: installation, usage, and a compact overview of the patterns.

## Key files (and how they relate)
- `SKILL.md`
  - The actual skill definition.
  - Starts with YAML frontmatter (`---` … `---`) containing `name`, `version`, `description`, and `allowed-tools`.
  - After the frontmatter is the editor prompt: the canonical, detailed pattern list with medical examples.
- `README.md`
  - Installation and usage instructions.
  - Contains a summarized "18 patterns" table and a short version history.

When changing behavior/content, treat `SKILL.md` as the source of truth, and update `README.md` to stay consistent.

## Common commands
### Install the skill into Claude Code
Recommended (clone directly into Claude Code skills directory):
```bash
mkdir -p ~/.claude/skills
git clone <repository-url> ~/.claude/skills/humanizer_academic
```

Manual install/update (only the skill file):
```bash
mkdir -p ~/.claude/skills/humanizer_academic
cp SKILL.md ~/.claude/skills/humanizer_academic/
```

## How to "run" it (Claude Code)
Invoke the skill:
- `/humanizer_academic` then paste text

## Making changes safely
### Versioning (keep in sync)
- `SKILL.md` has a `version:` field in its YAML frontmatter.
- `README.md` has a "Version History" section.

If you bump the version, update both.

### Editing `SKILL.md`
- Preserve valid YAML frontmatter formatting and indentation.
- Keep the pattern numbering stable unless you're intentionally re-numbering (since the README table and examples reference the same numbering).
- All examples should be from medical/academic contexts (primarily EMPA-REG OUTCOME trial).

### Documenting non-obvious fixes
If you change the prompt to handle a tricky failure mode (e.g., a repeated mis-edit or an unexpected tone shift), add a short note to `README.md`'s version history describing what was fixed and why.

## Differences from standard humanizer
This skill is adapted from the standard humanizer skill with the following changes:
- 18 patterns (vs 24) - removed patterns irrelevant to academic writing
- Medical/scientific examples throughout
- No "personality and soul" section (academic writing should be objective)
- Focus on preserving data integrity and precise language
