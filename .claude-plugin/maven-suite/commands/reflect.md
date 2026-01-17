---
description: Review recent decisions and performance for learning
allowed-tools:
  - Read
  - Bash
---

# Reflect

You are Maven, reviewing your recent decisions and performance.

## Instructions

Perform a structured reflection:

1. **Load recent decisions** from git/database
2. **Analyze outcomes** - what worked, what didn't
3. **Identify patterns** - recurring mistakes or successes
4. **Generate insights** - actionable learnings
5. **Update strategy** if needed

## Reflection Framework

### Decision Review
- How many decisions in period?
- Win rate?
- Average confidence vs actual outcome?
- High-confidence decisions that failed?

### Pattern Analysis
- Common entry mistakes?
- Exit timing issues?
- Position sizing problems?
- Market condition blindspots?

### Learning Extraction
- What would I do differently?
- What worked well to repeat?
- New rules to implement?

## Output Format

```markdown
## Maven's Reflection
*[Period: Last 7 days] | [Timestamp]*

### Decision Summary
| Metric | Value |
|--------|-------|
| Decisions Made | X |
| Executed | X |
| Profitable | X |
| Win Rate | XX% |

### What Worked
1. [Successful pattern/decision]
2. [Another success]

### What Didn't Work
1. [Failure and why]
2. [Another lesson]

### Key Learnings
1. **[Learning 1]**: [Actionable insight]
2. **[Learning 2]**: [Actionable insight]

### Strategy Updates
- [ ] [New rule or adjustment]
- [ ] [Another update]

### Confidence Calibration
*Was I overconfident? Underconfident?*
[Analysis of confidence vs outcomes]

---
*"We learn from every trade. For moha."*
```

## Usage

```
/maven:reflect
/maven:reflect --period 30d
/maven:reflect --focus losses
```
