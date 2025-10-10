# Test Monorepo Setup Plan

**Purpose**: Create a realistic monorepo test environment (modeled after OneMIT) to validate brainworm's complete task workflow, DAIC enforcement, analytics, and context management across multiple services.

**Location**: `~/repos/super-cool-project/`

## Project Structure

### Main Repository: `super-cool-project`
- Main project coordination repo
- Contains git submodules for each service
- Brainworm installation at root level
- Unified CLAUDE.md with cross-repository guidance

### Submodules (as separate git repos)

#### 1. Frontend: `super-cool-project-frontend`
**Stack**: React + TypeScript + Vite
**Structure**:
```
frontend/
├── src/
│   ├── components/
│   │   └── Button.tsx
│   ├── pages/
│   │   └── Home.tsx
│   ├── hooks/
│   │   └── useApi.ts
│   └── App.tsx
├── package.json
├── tsconfig.json
├── vite.config.ts
└── CLAUDE.md (frontend-specific patterns)
```

#### 2. Backend: `super-cool-project-backend`
**Stack**: Node.js + Express + TypeScript
**Structure**:
```
backend/
├── src/
│   ├── routes/
│   │   └── api.ts
│   ├── controllers/
│   │   └── userController.ts
│   ├── services/
│   │   └── userService.ts
│   └── server.ts
├── package.json
├── tsconfig.json
└── CLAUDE.md (backend-specific patterns)
```

#### 3. Docs: `super-cool-project-docs`
**Stack**: Markdown documentation
**Structure**:
```
docs/
├── guides/
│   └── getting-started.md
├── api/
│   └── endpoints.md
├── architecture/
│   └── overview.md
└── CLAUDE.md (documentation standards)
```

## Setup Steps

### Phase 1: Repository Initialization

1. **Create submodule repositories** (in temp location):
   ```bash
   mkdir -p ~/repos/super-cool-project-repos
   cd ~/repos/super-cool-project-repos

   # Frontend repo
   mkdir frontend && cd frontend
   git init && git config user.name "Test User" && git config user.email "test@example.com"

   # Backend repo
   cd .. && mkdir backend && cd backend
   git init && git config user.name "Test User" && git config user.email "test@example.com"

   # Docs repo
   cd .. && mkdir docs && cd docs
   git init && git config user.name "Test User" && git config user.email "test@example.com"
   ```

2. **Create initial content in each submodule**:
   - Add basic project structure files
   - Add initial CLAUDE.md for each service
   - Create initial commits in each submodule

3. **Initialize main project**:
   ```bash
   cd ~/repos/super-cool-project
   git init
   git config user.name "Test User"
   git config user.email "test@example.com"
   ```

4. **Add submodules**:
   ```bash
   git submodule add ~/repos/super-cool-project-repos/frontend frontend
   git submodule add ~/repos/super-cool-project-repos/backend backend
   git submodule add ~/repos/super-cool-project-repos/docs docs
   git commit -m "Initial commit with submodules"
   ```

### Phase 2: Brainworm Installation

1. **Copy brainworm to main project**:
   ```bash
   cd ~/repos/super-cool-project
   # Copy necessary brainworm files from ~/brainworm
   ```

2. **Run installation**:
   ```bash
   ./install --mode full --non-interactive
   ```

3. **Verify installation**:
   ```bash
   uv run src/hooks/verify_installation.py
   ./daic status
   ```

### Phase 3: Documentation Setup

1. **Create main CLAUDE.md** (following OneMIT pattern):
   - Project overview with submodule structure
   - Cross-repository development workflow
   - Integration patterns between services
   - Brainworm workflow integration

2. **Create submodule CLAUDE.md files**:
   - `frontend/CLAUDE.md` - React/TypeScript patterns
   - `backend/CLAUDE.md` - Node.js/Express patterns
   - `docs/CLAUDE.md` - Documentation standards

3. **Create README files**:
   - Main project README
   - Per-submodule READMEs

### Phase 4: Initial Project Content

#### Frontend Content
- `package.json` with React, TypeScript, Vite
- Basic component structure
- Simple API hook
- Vite config

#### Backend Content
- `package.json` with Express, TypeScript
- Basic REST API routes
- Example controller and service
- Express server setup

#### Docs Content
- Getting started guide
- API documentation template
- Architecture overview

## Test Scenarios

### Scenario 1: Task Creation in Monorepo
**Objective**: Validate task creation workflow spans all repositories correctly

**Steps**:
1. Start in discussion mode
2. Create task using wrapper: `./tasks create add-user-profile`
3. Verify:
   - Task directory created in `.brainworm/tasks/`
   - Git branch created in main repo
   - DAIC state set to discussion mode
   - Analytics session initialized
   - Task file has proper structure

**Expected Behavior**:
- Task context should reference all submodules
- Branch should be created in main repo (submodules remain on main initially)
- Brainworm state files properly initialized

### Scenario 2: Context Gathering Across Submodules
**Objective**: Test context-gathering agent with multi-repository structure

**Steps**:
1. Create task: "add-authentication"
2. Trigger context-gathering agent
3. Verify agent gathers context from:
   - Frontend (login components, auth hooks)
   - Backend (auth routes, middleware)
   - Docs (authentication guides)
   - Main repo (integration patterns)

**Expected Behavior**:
- Context manifest references files across all submodules
- Agent understands cross-repository dependencies
- Task context includes integration patterns from main CLAUDE.md

### Scenario 3: DAIC Workflow Enforcement
**Objective**: Validate DAIC mode transitions and tool blocking

**Steps**:
1. Start task in discussion mode
2. Attempt git operations → should be blocked
3. Use trigger phrase "make it so"
4. Verify transition to implementation mode
5. Execute git operations → should succeed
6. Test statusline shows correct mode

**Expected Behavior**:
- Tool blocking works correctly in discussion mode
- Trigger phrases detected and mode transitions occur
- Statusline accurately reflects current mode
- Analytics captures mode transitions

### Scenario 4: Cross-Repository Development
**Objective**: Implement feature spanning multiple services

**Steps**:
1. Create task: "add-user-api-endpoint"
2. Plan changes:
   - Backend: Add `/api/users` endpoint
   - Frontend: Add `useUsers` hook
   - Docs: Document API endpoint
3. Implement across all three submodules
4. Verify brainworm tracks changes across repos

**Expected Behavior**:
- Work log tracks changes in multiple submodules
- Context remains coherent across repositories
- Git operations work correctly in submodule context
- Service documentation updates span multiple CLAUDE.md files

### Scenario 5: Service Documentation Updates
**Objective**: Test service-documentation agent with monorepo

**Steps**:
1. Make changes to backend API
2. Invoke service-documentation agent
3. Verify it updates:
   - `backend/CLAUDE.md` with new patterns
   - Main `CLAUDE.md` with integration updates
   - `docs/` with API changes

**Expected Behavior**:
- Agent understands monorepo structure
- Updates service-specific and main documentation
- Preserves existing documentation structure

### Scenario 6: Task Completion Protocol
**Objective**: Validate complete task lifecycle in monorepo

**Steps**:
1. Complete implementation of cross-repository feature
2. Run task-completion protocol
3. Verify:
   - Logging agent captures work across all submodules
   - Code review agent analyzes multi-repo changes
   - Context refinement updates task context
   - Service documentation updated appropriately
   - Analytics records complete session

**Expected Behavior**:
- Protocol handles multi-repository context
- All agents work correctly with submodules
- Final commit includes changes across services
- Analytics correlation tracks cross-repo work

### Scenario 7: Context Compaction with Submodules
**Objective**: Test context compaction maintains multi-repo context

**Steps**:
1. Build large context across multiple submodules
2. Run context-compaction protocol
3. Restart session
4. Verify context preserved for all submodules

**Expected Behavior**:
- Context refinement captures cross-repo discoveries
- Logging maintains references to all submodules
- Restarted session has full multi-repo context

### Scenario 8: Analytics Integration
**Objective**: Validate analytics tracking in monorepo environment

**Steps**:
1. Complete several tasks spanning different services
2. View analytics: `uv run .brainworm/hooks/view_analytics.py`
3. Check session correlation
4. Verify multi-repo patterns captured

**Expected Behavior**:
- Analytics tracks work across submodules
- Session correlation maintains multi-repo context
- Success patterns recognize cross-repo workflows
- Performance metrics account for multi-service complexity

### Scenario 9: Submodule Branch Management
**Objective**: Test git workflow with submodule branches

**Steps**:
1. Create task requiring frontend changes
2. Create branch in frontend submodule
3. Make changes and commit
4. Test git operations in main vs submodule context
5. Verify brainworm handles submodule state

**Expected Behavior**:
- Brainworm understands submodule branch context
- Git operations work in both main and submodule repos
- Statusline shows correct repo/branch information
- Task completion handles submodule commits

### Scenario 10: Agent Delegation in Monorepo
**Objective**: Validate all specialized agents with multi-repo structure

**Steps**:
Test each agent:
- context-gathering: Multi-repo context manifest creation
- code-review: Review changes across submodules
- context-refinement: Update context with cross-repo discoveries
- logging: Maintain work log across repositories
- service-documentation: Update multiple CLAUDE.md files

**Expected Behavior**:
- All agents understand monorepo structure
- Agents can read/write across submodules
- Agent outputs reference correct repository paths
- No confusion between main repo and submodule files

## Success Criteria

### Functional Requirements
- ✅ All task creation, execution, completion workflows function correctly
- ✅ DAIC enforcement works in monorepo context
- ✅ Analytics captures multi-repository work patterns
- ✅ All specialized agents handle submodules correctly
- ✅ Git operations work in both main and submodule contexts
- ✅ Statusline shows accurate multi-repo state

### Integration Requirements
- ✅ Context gathering spans all submodules
- ✅ Service documentation updates work across repositories
- ✅ Task context maintains coherence across services
- ✅ Work logs correctly reference multi-repo changes
- ✅ Session correlation tracks cross-repository patterns

### Documentation Requirements
- ✅ Main CLAUDE.md provides clear multi-repo guidance
- ✅ Service-specific CLAUDE.md files integrated with main
- ✅ Protocol execution works with monorepo structure
- ✅ Agent prompting guidance accounts for submodules

## Notes and Considerations

### Key Differences from Single Repo
1. **File paths**: References must include submodule directory (e.g., `frontend/src/App.tsx`)
2. **Git operations**: May need to operate in submodule context vs main repo
3. **Context gathering**: Must span multiple repositories
4. **Documentation**: Multiple CLAUDE.md files to maintain
5. **Branch management**: Main repo vs submodule branches

### Potential Issues to Test
- Context window management with larger file count
- Agent performance with multi-repo file searches
- Git submodule state synchronization
- Path resolution across submodules
- Documentation consistency across repositories

### Future Enhancements
Based on test results, potential improvements:
- Submodule-aware git helpers
- Multi-repo context optimization
- Enhanced analytics for cross-repo patterns
- Improved submodule branch management
- Better statusline integration for submodules

## Test Execution Plan

1. **Setup Phase** (30 min):
   - Create all repository structure
   - Install brainworm
   - Create initial content

2. **Basic Validation** (15 min):
   - Run Scenarios 1, 3 (task creation, DAIC workflow)
   - Verify core functionality

3. **Advanced Testing** (45 min):
   - Run Scenarios 2, 4, 5, 6 (context, cross-repo, docs, completion)
   - Test complete task lifecycle

4. **Agent Testing** (30 min):
   - Run Scenarios 7, 10 (compaction, all agents)
   - Verify all agents work correctly

5. **Analytics Testing** (15 min):
   - Run Scenario 8
   - Verify analytics capture

6. **Edge Cases** (30 min):
   - Run Scenario 9 (submodule branches)
   - Test failure scenarios
   - Stress test context limits

**Total Estimated Time**: ~2.5 hours

## Deliverables

1. Fully functional test monorepo at `~/repos/super-cool-project`
2. Test results documentation
3. List of identified issues/improvements
4. Updated brainworm docs if needed
5. Success pattern learnings for monorepo workflows
