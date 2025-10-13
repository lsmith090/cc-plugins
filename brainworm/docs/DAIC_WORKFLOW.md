# DAIC Workflow Methodology - Discussion → Alignment → Implementation → Check

## Overview

The DAIC (Discussion → Alignment → Implementation → Check) methodology is the core workflow system enforced by brainworm. This structured approach to development ensures better code quality, reduced errors, and improved team collaboration by preventing premature implementation and encouraging thorough planning.

DAIC transforms the typical "ask → implement immediately" pattern into a deliberate workflow that learns from your patterns and provides guidance.

## The Four Phases

### 🎯 Discussion Phase

**Purpose**: Explore the problem space, understand requirements, and consider approaches

**Characteristics**:
- **Tool Blocking**: Implementation tools (`Edit`, `Write`, `MultiEdit`, `NotebookEdit`) are blocked
- **Read-Only Operations**: Extensive allowlist of safe commands for exploration
- **Collaborative**: Encourages asking questions, exploring alternatives, presenting options
- **Event-Tracked**: Workflow data captured for session continuity

**What You Can Do**:
- File exploration (`ls`, `cat`, `grep`, `rg`, `find`)
- Git inspection (`git status`, `git log`, `git diff`)
- Test execution (`pytest`, `npm test`, `cargo test`, etc.)
- Code analysis and investigation
- Research existing patterns and conventions
- Use specialized subagents for complex analysis
- Read documentation and understand context

**Best Practices**:
- **Ask clarifying questions** when requirements are unclear
- **Research existing patterns** in the codebase before proposing new approaches
- **Present multiple options** when architectural decisions have tradeoffs
- **Use subagents proactively** for complex analysis (context-gathering, code-review)
- **Document your findings** to inform implementation decisions

### 🤝 Alignment Phase

**Purpose**: Achieve consensus on the approach and ensure all stakeholders understand the plan

**Characteristics**:
- **Collaborative Decision Making**: Present findings and get explicit user confirmation
- **Risk Assessment**: Identify potential issues and dependencies
- **Resource Planning**: Understand time estimates and complexity
- **Documentation**: Capture agreed-upon approach for implementation reference

**What You Should Do**:
- **Summarize your analysis** clearly and concisely
- **Present your recommended approach** with reasoning
- **Identify risks, dependencies, or unknowns** that could affect implementation
- **Get explicit confirmation** before proceeding to implementation
- **Document the plan** for future reference and team members

**Alignment Indicators**:
- User provides explicit agreement ("sounds good", "let's do it", "proceed")
- Approach is documented and understood by all parties
- Risks and dependencies are acknowledged and addressed
- Success criteria are clear and measurable

### ⚡ Implementation Phase

**Purpose**: Execute the agreed-upon approach efficiently and correctly

**Activation Methods**:
- **Trigger Phrases**: `"make it so"`, `"ship it"`, `"go ahead"`, `"let's do it"`, `"execute"`, `"implement it"`
- **Manual Mode Switch**: `./daic implementation`

**Characteristics**:
- **Full Tool Access**: All implementation tools become available
- **Focused Execution**: Stay aligned with the agreed approach
- **Progress Tracking**: Real-time monitoring of implementation progress
- **Quality Assurance**: Continuous validation against success criteria

**What You Should Do**:
- **Follow the agreed plan** systematically
- **Implement incrementally** with regular validation checkpoints
- **Document changes** as you make them for future reference
- **Test changes** as you implement them when possible
- **Stay focused** on the specific task scope

**Best Practices**:
- **One logical change at a time** to maintain code clarity
- **Test frequently** to catch issues early
- **Follow existing code conventions** and patterns consistently
- **Document complex decisions** for future maintainers
- **Use meaningful commit messages** that explain the "why" not just the "what"

### ✅ Check Phase

**Purpose**: Validate implementation quality, completeness, and alignment with original goals

**Activation**:
- Automatic after implementation completion
- Manual invocation for interim checks
- Triggered by quality thresholds or error detection

**Characteristics**:
- **Quality Validation**: Code review, testing, and documentation verification
- **Completeness Check**: Ensure all success criteria are met
- **Integration Testing**: Verify changes work within the broader system
- **Knowledge Capture**: Document learnings for future similar work

**What You Should Do**:
- **Run all relevant tests** to ensure functionality
- **Perform code review** using code-review agent for sophisticated analysis
- **Validate success criteria** against original requirements
- **Test edge cases and error scenarios** that could cause issues
- **Update documentation** to reflect changes and decisions made

**Quality Gates**:
- All tests pass without errors
- Code review identifies no critical issues
- Success criteria are demonstrably met
- Documentation is updated and accurate
- Team members can understand and maintain the changes

## Workflow Transitions

### Discussion → Implementation (Direct)

**When Appropriate**:
- Simple, well-understood tasks
- Clear requirements with no ambiguity
- Established patterns with minimal risk

**Trigger Conditions**:
- User provides clear, specific instructions
- No significant architectural decisions required
- Implementation approach is obvious and low-risk

### Discussion → Alignment → Implementation (Recommended)

**When Appropriate**:
- Complex or novel implementations
- Multiple possible approaches to consider
- Significant architectural or design decisions
- High-risk changes or unfamiliar territory

**Benefits**:
- Reduces implementation errors through better planning
- Ensures stakeholder understanding and buy-in
- Creates documentation for future similar work
- Enables better time and resource estimation

## Analytics Features ⚠️ **PLANNED/LIMITED IMPLEMENTATION**

**Important Note**: The analytics features described below represent the planned evolution of the DAIC system. Most are not yet fully implemented and should be considered aspirational capabilities for future development.

### Codebase Memory Enhancement 🔄 **PLANNED**

**Status**: Basic pattern recognition exists, enhanced memory features planned
**Planned Capability**: Improve agent understanding of codebase patterns
- Remember architectural decisions and their contexts
- Learn from code review findings to suggest better approaches
- Track successful implementation patterns for similar tasks
- Maintain knowledge of team conventions and best practices

**Current Reality**: Basic analytics tracking with limited pattern recognition
**Example** (when enhanced): "Previous authentication implementations in this codebase consistently use middleware pattern in /src/auth/. Consider reviewing AuthMiddleware.js for established conventions."

### Smart Recommendations ⚠️ **LIMITED IMPLEMENTATION**

**Status**: Basic implementation - simple prompt length checking only
**Current Capability**: Very basic transition suggestions
- Simple prompt length analysis
- Basic context checking
- No ML-driven insights or historical pattern analysis

**Planned Enhancement**: Intelligent suggestions for discussion quality
- Early identification of missing context or unclear requirements
- Recommendations for relevant codebase patterns to investigate
- Integration with code review insights and quality metrics
- Suggestions for appropriate subagent usage based on task complexity

**Current Reality**: Minimal recommendations, no ML intelligence
**Example** (current): Basic prompt-based suggestions only
**Example** (when enhanced): "Similar authentication tasks typically benefit from reviewing the existing auth middleware patterns. Consider examining /src/auth/middleware/ before implementing."

## Configuration and Customization

DAIC workflow behavior can be customized through configuration files. See [`docs/CONFIGURATION.md`](CONFIGURATION.md) for complete configuration reference including:

- **Trigger phrase customization** - Modify phrases that transition to implementation mode
- **Tool blocking configuration** - Control which tools are restricted in discussion mode
- **Read-only command allowlists** - Define investigation commands allowed in discussion mode
- **Event storage settings** - Configure workflow event capture

## Common Workflow Patterns

### Simple Task Pattern
```
Discussion (5-10 min) → "go ahead" → Implementation (20-30 min) → Check (5 min)
```

### Complex Feature Pattern
```
Discussion (15-25 min) → Context-Gathering Agent → 
Alignment (5-10 min) → "make it so" → 
Implementation (45-60 min) → Code-Review Agent → 
Check (10-15 min)
```

### Research-Heavy Pattern
```
Discussion (20-30 min) → Multiple Subagents → 
Extended Alignment (10-15 min) → "ship it" → 
Phased Implementation (60+ min) → Comprehensive Check (15+ min)
```

### Iterative Refinement Pattern
```
Discussion → Implementation → Check → "let's refine this" → 
Discussion → Implementation → Check (repeat until satisfied)
```

## Troubleshooting and Common Issues

### "I'm Blocked from Making Changes"

**Cause**: Currently in discussion mode
**Solution**: 
1. Complete your analysis and present findings
2. Get user alignment on approach
3. Use trigger phrase to switch to implementation mode

### "The System Keeps Suggesting More Discussion"

**Cause**: Intelligence features detecting complexity patterns
**Solutions**:
- Address the specific concerns raised by the system
- Use context-gathering agent for comprehensive analysis
- Override with explicit trigger phrase if you're confident

### "Mode Switching Isn't Working"

**Important**: Only human users can switch modes - Claude agents cannot transition themselves.

**Troubleshooting**:
1. Use trigger phrases: "make it so", "ship it", "go ahead", "execute", "implement it"
2. Check DAIC status: `./daic status`
3. Manual override: `./daic implementation` 
4. Verify configuration in `brainworm-config.toml`
5. Restart Claude Code if hooks were recently updated

### "Discussion Phase Taking Too Long"

**Strategies**:
- Use specialized subagents for comprehensive analysis
- Focus on understanding requirements and constraints thoroughly
- Present well-researched options with clear tradeoffs
- Leverage documented patterns to improve investigation quality

## Integration with Other Brainworm Features

### Subagent Integration
- **Context-Gathering**: Use during discussion phase for comprehensive analysis
- **Code-Review**: Automatic invocation during check phase
- **Logging**: Continuous documentation throughout workflow
- **Service-Documentation**: Updates documentation as changes are implemented

### Event Storage Integration
- **Session Correlation**: Track workflow continuity across sessions
- **Event Capture**: Record DAIC transitions and tool usage
- **Workflow Tracking**: Maintain event history for debugging and analysis

### Task Management
- **Protocol Integration**: DAIC workflow built into task creation, completion, and startup protocols
- **State Management**: Current workflow phase tracked in unified session state
- **Branch Enforcement**: Git workflow coordination with DAIC phases
- **Progress Tracking**: Visual indication of workflow progress in statusline

## Best Practices for Teams

### Individual Development
- **Embrace the discussion phase** - it saves time in implementation and debugging
- **Use trigger phrases naturally** as part of your thinking process
- **Leverage subagents proactively** for complex analysis and quality assurance
- **Document your reasoning** during alignment phase for future reference

### Team Collaboration
- **Share workflow patterns** that work well for your team
- **Customize trigger phrases** to match team communication style
- **Review event data** to understand team development patterns
- **Establish team standards** for thorough discussion and comprehensive analysis

### Project Management
- **Track DAIC effectiveness** using event data queries
- **Maintain consistent discipline** regardless of team experience to preserve thoughtful workflow
- **Document successful patterns** to guide project planning and estimation
- **Monitor workflow consistency** through event tracking

The DAIC methodology creates a structured development workflow that maintains high code quality through deliberate phases and thoughtful decision-making.