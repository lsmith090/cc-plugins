# End User Guide: Getting Started with DAIC Workflow

## Welcome to Brainworm-Enhanced Development

This guide walks you through your first few sessions using the DAIC (Discussion → Alignment → Implementation → Check) workflow with Claude Code. You'll learn by doing, with real examples and specific commands.

**What you'll learn:**
- How to recognize and work with DAIC modes
- When and how to use trigger phrases
- How to use subagents effectively
- Practical workflow patterns for common tasks

---

## Before You Start: Quick Setup Check

Verify your installation is working:

```bash
./daic status              # Should show current mode
./install                  # If anything seems broken
```

**Understanding the Statusline:**
- **Purple** = Discussion mode (planning, no code changes)
- **Green** = Implementation mode (can make code changes)

---

# Session 1: Your First DAIC Interaction

## Scenario: Adding a Simple Feature

**Your goal:** Add a new API endpoint for user preferences

### Step 1: Start in Discussion Mode (Purple Statusline)

Claude starts in discussion mode by default. You'll see tool blocking messages if you try to make changes.

**You:** "I need to add a new API endpoint for user preferences"

**Claude's typical response:**
```
I'm in discussion mode, so I'll help you plan this out first. Let me understand what you need:

1. What type of user preferences will this handle?
2. Should this integrate with existing user management?
3. What operations do you need (GET, POST, PUT, DELETE)?
4. Are there any authentication requirements?
```

**Key insight:** Claude cannot make code changes yet - this is intentional!

### Step 2: Work Through the Discussion

**You provide details:**
"I need GET and POST endpoints for user theme preferences (light/dark mode), integrated with our existing auth system."

**Claude will:**
- Ask clarifying questions
- Research your existing codebase
- Look at existing auth patterns
- Suggest specific approaches
- Present you with options

```
Based on your existing auth middleware in /src/middleware/auth.js and the user model in /src/models/User.js, I recommend:

1. Add preference fields to existing User schema
2. Create new routes in /src/routes/preferences.js  
3. Use existing JWT middleware for authentication
4. Follow RESTful patterns like your other endpoints

Should I proceed with this approach?
```

### Step 3: Trigger Implementation Mode

When you're ready for Claude to make changes, use a **trigger phrase:**

**Trigger phrases that work:**
- "make it so"
- "go ahead" 
- "ship it"
- "let's do it"
- "execute"
- "implement it"

**You:** "Sounds good, **go ahead** and implement it"

**You'll see:** `[DAIC: Implementation Mode Activated]` and the statusline turns **green**.

### Step 4: Implementation Happens

Now Claude can make code changes:
- Creates/modifies files
- Adds proper error handling
- Follows existing patterns
- Updates relevant documentation

### Step 5: Automatic Check Phase

After implementation, Claude will:
- Run tests if available
- Verify the changes work
- Check for any issues
- Suggest next steps

**What you learned:**
- Discussion mode prevents hasty implementation
- Trigger phrases control when changes happen
- The workflow encourages better planning

---

# Session 2: Working with Tasks and Subagents

## Scenario: Fixing a Complex Bug

**Your goal:** Fix a performance issue in the user dashboard

### Step 1: Create a Proper Task

Instead of jumping in, create a structured task:

**You:** "Let's create a task to fix the dashboard performance issue"

**Claude recognizes this** and uses the automated task creation wrapper:
```bash
./tasks create fix-dashboard-performance
```

**The wrapper automatically:**
- Creates task directory at `.brainworm/tasks/fix-dashboard-performance/`
- Populates README.md from template
- Creates appropriate git branch (`fix/fix-dashboard-performance`)
- Updates DAIC state
- Initializes analytics tracking

**Result:** You get a fully configured task ready for work

### Step 2: Using Subagents for Heavy Lifting

**Claude will suggest:** "Let me use the context-gathering agent to analyze the dashboard performance issues comprehensively."

**What happens:**
- A specialized subagent analyzes your codebase
- Creates a detailed context manifest
- Maps all related components
- Identifies potential performance bottlenecks
- Returns structured findings to Claude

**You see:** A comprehensive analysis without overwhelming Claude's main context.

### Step 3: Intelligent Discussion Phase

With subagent insights, Claude can have a much more informed discussion:

```
Based on the context-gathering analysis, I found several performance issues:

1. N+1 query problem in getUserDashboardData() 
2. Unoptimized database indices on user_activities table
3. Missing caching layer for frequently accessed data
4. Large payload sizes due to over-fetching

The analysis suggests we should prioritize the N+1 queries first as they're causing the most significant performance impact.

Should we focus on the database queries first, or would you prefer a different approach?
```

### Step 4: Focused Implementation

**You:** "Yes, let's fix the N+1 queries first. **Make it so**."

**Claude:** 
- Switches to implementation mode
- Fixes the specific issues
- Uses code-review agent automatically for quality assurance
- Updates the task work log

**Key insight:** Subagents handle the heavy research, letting Claude focus on implementation.

---

# Session 3: Advanced Workflow Management

## Scenario: Building a Multi-Part Feature

**Your goal:** Implement user notifications system

### Step 1: Context is Getting Full

As you work, you'll notice the context filling up. Claude might suggest:

```
Our context window is getting quite full. Would you like me to run the context compaction protocol to preserve our progress and start fresh?
```

### Step 2: Understanding Context Compaction

**You:** "Yes, let's compact the context"

**What happens:**
1. **Logging agent** organizes all work into clean chronological logs
2. **Context-refinement agent** updates task context with new discoveries  
3. All important information is preserved in task files
4. Session restarts with a clean context window

**Result:** You can continue working without losing progress.

### Step 3: Working Across Multiple Sessions

When you return to work:

**You:** "Let's continue working on the notifications system"

**Claude runs the task-startup protocol:**
```
I see we're continuing work on implement-user-notifications. Let me load the context:

From the task file, I can see we've:
1. ✓ Designed the notification schema 
2. ✓ Implemented basic database operations
3. → Next: Build the real-time WebSocket layer

Should we continue with the WebSocket implementation?
```

### Step 4: Completing Tasks

When you're finished:

**You:** "I think this task is complete"

**Claude runs task-completion protocol:**
1. **Code-review agent** does final quality check
2. **Service-documentation agent** updates relevant docs  
3. **Logging agent** creates final work summary
4. Analytics are updated with success patterns

**Result:** Clean task completion with preserved knowledge for future work.

---

# Quick Reference Guide

## Essential Commands

```bash
./daic status              # Check current mode and task
./daic discussion         # Force discussion mode
./daic implementation     # Force implementation mode  
./daic toggle            # Switch between modes
```

## Trigger Phrases (Discussion → Implementation)

| Phrase | Tone | When to Use |
|--------|------|-------------|
| "make it so" | Formal, confident | When you're sure of the approach |
| "go ahead" | Casual, ready | For straightforward implementations |  
| "ship it" | Urgent, decisive | When you want quick action |
| "let's do it" | Collaborative | For team-style decisions |
| "execute" | Direct, military | For precise, planned actions |
| "implement it" | Clear, technical | For complex technical implementations |

## What Claude Can Do in Each Mode

### Discussion Mode (Purple Statusline)
✅ **Allowed:**
- Read files and analyze code
- Search and explore the codebase
- Run git commands for inspection
- Use subagents for research
- Ask questions and gather requirements
- Present options and recommendations

❌ **Blocked:**
- Edit, Write, or MultiEdit files
- Create new files
- Make any code changes
- Commit changes

### Implementation Mode (Green Statusline)
✅ **Full access to all tools**
- Make code changes
- Create new files
- Run builds and tests
- Commit changes (when asked)

## Subagent Quick Guide

| Agent | When to Use | What It Does |
|-------|-------------|--------------|
| **context-gathering** | Starting new tasks | Creates comprehensive context manifests |
| **code-review** | Before completing tasks | Reviews code for quality and security |
| **context-refinement** | Context compaction | Updates task context with discoveries |
| **logging** | Task completion | Creates clean work logs |
| **service-documentation** | After changes | Updates service documentation |

## Reading the Statusline

**Purple statusline example:**
```
[DAIC: Discussion | implement-user-auth | feature/user-auth | 45% context]
```

**Green statusline example:**
```
[DAIC: Implementation | fix-payment-bug | bugfix/payment | 67% context]
```

**What each part means:**
- **Mode**: Current DAIC phase
- **Task**: Active task name
- **Branch**: Current git branch  
- **Context**: How full the context window is

---

# Common Patterns and Best Practices

## Pattern 1: The Simple Task Flow
```
Discussion (5-10 min) → trigger phrase → Implementation (20-30 min) → Check (5 min)
```
**Good for:** Bug fixes, small features, straightforward changes

## Pattern 2: The Complex Feature Flow  
```
Discussion (15-25 min) → Context-Gathering Agent → 
Alignment (5-10 min) → trigger phrase → 
Implementation (45-60 min) → Code-Review Agent → Check (10-15 min)
```
**Good for:** New features, architectural changes, complex integrations

## Pattern 3: The Research-Heavy Flow
```
Discussion (20-30 min) → Multiple Subagents → 
Extended Alignment (10-15 min) → trigger phrase →
Phased Implementation (60+ min) → Comprehensive Check (15+ min)
```
**Good for:** Major refactoring, new technology adoption, performance optimization

## Best Practices

### DO:
- **Embrace the discussion phase** - it saves time later
- **Use subagents proactively** for complex analysis
- **Be specific with trigger phrases** when you're ready
- **Create tasks for non-trivial work** to maintain context
- **Let context compaction happen** when Claude suggests it

### DON'T:
- **Rush to implementation** without understanding the problem
- **Fight the tool blocking** - it's there to help you think
- **Ignore subagent suggestions** - they have specialized knowledge
- **Try to work without tasks** for complex features
- **Let context fill up completely** before compacting

---

# Troubleshooting Common Issues

## "I'm Stuck in Discussion Mode"

**What you see:**
```
I'd like to implement this change, but I'm currently in discussion mode...
```

**Solutions:**
1. Use a trigger phrase: "go ahead", "make it so", etc.
2. Manual override: `./daic implementation`
3. Complete your discussion first - Claude might have good reasons to stay in discussion

## "Mode Switching Isn't Working"

**Check these:**
1. Are you using the right trigger phrases?
2. Run `./daic status` to see current state
3. Try manual mode switch: `./daic implementation`
4. Check if hooks are properly installed: `./install`

## "Claude Keeps Suggesting More Discussion"

**This means:**
- The task might be more complex than initially thought
- There could be missing requirements or unclear scope  
- Claude found potential issues during analysis

**Solutions:**
- Address the specific concerns raised
- Use context-gathering agent for comprehensive analysis
- Override with explicit trigger phrase if you're confident

## "I Don't Know What Subagent to Use"

**Quick decision tree:**
- **Starting new task?** → context-gathering
- **Finished implementing?** → code-review  
- **Context getting full?** → Let Claude suggest (usually logging + context-refinement)
- **Made service changes?** → service-documentation

---

# Advanced Tips

## Working with Analytics

The system learns from your patterns:
```
Based on brainworm analytics, similar authentication tasks typically:
- Spend 30% of time in discussion mode for planning
- Use context-gathering agent early for comprehensive context
- Complete implementation in focused sessions  
- Apply code-review agent before final completion
```

**Use these insights** to optimize your workflow.

## Effective Trigger Phrase Usage

**Context matters:**
- "make it so" after thorough discussion → Claude implements confidently
- "go ahead" during early discussion → Claude might suggest more planning
- "ship it" for urgent fixes → Claude prioritizes speed over perfection

## Managing Long Tasks

For tasks spanning multiple sessions:
1. **Use context compaction** when Claude suggests it
2. **Check task files** when resuming work
3. **Run task-startup protocol** to reload context properly
4. **Update work logs** to track progress

## Team Collaboration

**When handing off tasks:**
- Ensure task files are comprehensive
- Use context-refinement agent to capture discoveries
- Update work logs with current status
- Include any informal notes or concerns

---

# What's Next?

After mastering these basics:

1. **Read the full technical docs** in `docs/DAIC_WORKFLOW.md`
2. **Explore analytics features** with `uv run .brainworm/hooks/view_analytics.py`
3. **Customize your configuration** using `docs/CONFIGURATION.md`
4. **Learn about the architecture** in `docs/ARCHITECTURE.md`

## Remember

The DAIC workflow might feel constraining at first, but it's designed to:
- **Prevent costly mistakes** through better planning
- **Improve code quality** through structured processes
- **Build institutional knowledge** through analytics
- **Make complex tasks manageable** through proper structure

**The system learns from every session to make future development more effective.**

Welcome to more thoughtful, effective software development! 🚀