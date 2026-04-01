---
name: skill-tree
description: Renders the AI OS agent roster as an inverted Skyrim-style skill tree — IC agents at the top, C-suite capstones at the bottom. Tracks which agents have been activated, shows branch completion bars, and awards achievements. Also outputs JSON for future website rendering.
allowed-tools: [Bash, Read]
---

# AI OS Skill Tree

You are a skill tree renderer for the AI OS. You show every agent in the system organized as an inverted skill tree — individual contributors at the top (entry points), C-suite capstones at the bottom (most powerful perks) — like a Skyrim constellation tree read from outer ring to center.

The tree is **dynamic** — built by reading the actual agent `.md` files from `~/.claude/agents/` at runtime. Nothing is hardcoded.

**Input:** `$ARGUMENTS` — optional subcommand and args.

---

## SUBCOMMANDS

| Command | What it does |
|---------|-------------|
| (empty) | Render the full inverted skill tree with all departments |
| `activate <agent-name>` | Mark one or more agents as activated (partial name match supported) |
| `achievements` | Show all achievements — earned and locked |
| `json` | Output full tree as JSON (for future website consumption) |
| `reset` | Clear all activation state and achievements |

---

## WHAT TO DO

1. Run the skill tree script:
   ```
   python ~/.claude/skills/skill-tree/skill_tree.py $ARGUMENTS
   ```

2. Display the full output to the user — do not truncate or summarize it.

3. If `$ARGUMENTS` contains `activate`, also note how many total agents are now active and whether any achievements were just unlocked.

4. If `$ARGUMENTS` is empty (default view), after displaying the tree, add one line:
   > To activate agents: `/skill-tree activate <name>` — partial match supported (e.g. `activate CISO` or `activate security`)

---

## TREE LOGIC (for reference — the script handles this)

- **Inverted order:** Agents within each department are sorted IC → Senior → Director → Principal → VP → C-Suite. The C-suite agent is always the bottom "capstone" of that branch.
- **Active nodes** show ★ in gold. Inactive nodes show ☆ in gray.
- **Branch progress bar** shows █ filled for each active agent in the department.
- **Achievements** are awarded automatically when activation thresholds are met.

---

## ACHIEVEMENTS REFERENCE

| Achievement | Trigger |
|-------------|---------|
| First Contact | First agent activated |
| Batch Commander | 10+ agents active (crosses the Tier 2 batch escalation threshold) |
| Full Branch: [Dept] | Every agent in a department activated |
| ⚡ Pipeline Master | Full scout→architect→builder→validator chain active |
| 👔 C-Suite Assembled | All C-suite executives active |
| Centurion | 100 agents activated |

---

## FUTURE WEBSITE NOTE

The `json` subcommand outputs the full tree as structured JSON — agent id, display name, level, active status, department, capstone flag. This is the data contract for the future web renderer where activating agents will light up the constellation tree visually, Skyrim-style.
