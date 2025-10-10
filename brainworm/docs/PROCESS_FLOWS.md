# Process Flow Documentation - Brainworm Architecture

This document provides comprehensive process flow diagrams using Mermaid to illustrate the architectural patterns and integration points within the brainworm system.

## Hook Independence Architecture

The following diagram shows how hooks maintain independence from the analytics system while providing optional integration points:

```mermaid
graph TD
    A[Claude Code Session] --> B[Hook System]
    A --> C[Analytics System]
    
    B --> D[Core Function]
    B --> E{Analytics Available?}
    
    E -->|Yes| F[Optional Integration]
    E -->|No| G[Graceful Degradation]
    
    F --> H[Enhanced Capabilities]
    G --> I[Basic Operation]
    
    D --> J[Hook Execution Success]
    H --> J
    I --> J
    
    C --> K[Session Correlation]
    C --> L[Event Storage]
    C --> M[Pattern Learning]
    
    F -.-> K
    F -.-> L
    F -.-> M
    
    subgraph "Hook Independence"
        D
        G
        I
        J
    end
    
    subgraph "Analytics Enhancement"
        F
        H
        K
        L
        M
    end
    
    style D fill:#90EE90
    style G fill:#90EE90
    style I fill:#90EE90
    style J fill:#90EE90
    style F fill:#87CEEB
    style H fill:#87CEEB
```

## Hooks Framework Lifecycle

This diagram illustrates the comprehensive lifecycle management provided by the Hooks Framework:

```mermaid
sequenceDiagram
    participant CC as Claude Code
    participant HF as HookFramework
    participant TC as Type System
    participant BC as Business Controllers
    participant AS as Analytics System
    participant HL as Hook Logic

    CC->>HF: Raw JSON Input
    HF->>TC: Parse & Validate Input
    TC->>HF: Typed Input Object
    
    HF->>HF: Project Root Discovery
    HF->>BC: Initialize Controllers
    BC->>HF: Controller Instances
    
    HF->>AS: Initialize Analytics (if enabled)
    AS->>HF: Analytics Logger
    
    HF->>HL: Execute Custom Logic
    HL->>BC: Business Operations
    BC->>HL: Results
    HL->>HF: Decision/Response
    
    HF->>TC: Format Response
    TC->>HF: Schema-Compliant JSON
    
    HF->>AS: Log Event (if enabled)
    AS->>AS: Store & Correlate
    
    HF->>CC: Hook Response
    
    Note over HF,AS: All analytics operations are optional and non-blocking
    Note over TC: Type safety enforced throughout
    Note over BC: High-level business abstractions
```

## Analytics Integration Points

This diagram shows the specific integration points between hooks and analytics, emphasizing the optional nature of the integration:

```mermaid
graph LR
    subgraph "Hook Templates"
        A[pre_tool_use.py]
        B[post_tool_use.py]  
        C[stop.py]
        D[session_start.py]
        E[user_prompt_submit.py]
    end
    
    subgraph "Hooks Framework Infrastructure"
        F[HookFramework]
        G[AnalyticsLogger]
        H[Type System]
        I[Business Controllers]
    end
    
    subgraph "Analytics Components"
        J[ClaudeAnalyticsProcessor]
        K[Session Correlation]
        L[Event Storage]
        M[Pattern Learning]
    end
    
    subgraph "Storage Layer"
        N[hooks.db SQLite]
        O[JSONL Backup Files]
        P[Correlation Data]
    end
    
    A --> F
    B --> F
    C --> F
    D --> F
    E --> F
    
    F --> G
    F --> H
    F --> I
    
    G -.->|Optional| J
    J -.->|Optional| K
    J -.->|Optional| L
    J -.->|Optional| M
    
    J --> N
    J --> O
    K --> P
    
    style A fill:#FFE4E1
    style B fill:#FFE4E1
    style C fill:#FFE4E1
    style D fill:#FFE4E1
    style E fill:#FFE4E1
    style G fill:#E6E6FA
    style J fill:#E6E6FA
    style K fill:#E6E6FA
    style L fill:#E6E6FA
    style M fill:#E6E6FA
```

## Session Correlation Flow

This diagram illustrates the multi-strategy session correlation system with confidence scoring:

```mermaid
flowchart TD
    A[New Hook Event] --> B[Extract Session Context]
    B --> C{Direct Session ID Available?}
    
    C -->|Yes| D[Use Direct Session ID]
    C -->|No| E[Multi-Strategy Correlation]
    
    E --> F[Timestamp Correlation]
    E --> G[Git State Correlation] 
    E --> H[File Activity Correlation]
    E --> I[Content Similarity]
    
    F --> J[Score: Weight 0.4]
    G --> K[Score: Weight 0.3]
    H --> L[Score: Weight 0.2]
    I --> M[Score: Weight 0.1]
    
    J --> N[Confidence Calculation]
    K --> N
    L --> N
    M --> N
    
    N --> O{Confidence > 85%?}
    O -->|Yes| P[High Confidence Match]
    O -->|No| Q{Confidence > 60%?}
    
    Q -->|Yes| R[Medium Confidence Match]
    Q -->|No| S[Create New Session]
    
    D --> T[Store Correlation]
    P --> T
    R --> T
    S --> T
    
    T --> U[Update Session State]
    U --> V[Analytics Processing]
    
    style D fill:#90EE90
    style P fill:#90EE90
    style R fill:#FFD700
    style S fill:#FFB6C1
```

## DAIC Workflow Process

This diagram shows the DAIC workflow enforcement process with tool blocking logic:

```mermaid
stateDiagram-v2
    [*] --> Discussion
    
    Discussion --> CheckToolUse: Tool Requested
    CheckToolUse --> BlockTool: Implementation Tool in Discussion Mode
    CheckToolUse --> AllowTool: Read-only Tool or System Command
    
    BlockTool --> Discussion: Tool Blocked with Message
    AllowTool --> Discussion: Tool Executed
    
    Discussion --> DetectTrigger: User Input Analysis
    DetectTrigger --> Implementation: Trigger Phrase Detected
    DetectTrigger --> Discussion: No Trigger Found
    
    Implementation --> CheckToolUse2: Tool Requested
    CheckToolUse2 --> AllowTool2: All Tools Allowed
    AllowTool2 --> Implementation: Tool Executed
    
    Implementation --> NewTopicDetected: Context Analysis
    NewTopicDetected --> Discussion: Return to Discussion
    
    state CheckToolUse {
        [*] --> SecurityCheck
        SecurityCheck --> DAICCheck: Security OK
        SecurityCheck --> BlockTool: Security Fail
        DAICCheck --> SubagentCheck: DAIC OK
        DAICCheck --> BlockTool: DAIC Block
        SubagentCheck --> AllowTool: In Subagent Context
        SubagentCheck --> [*]: Normal Context
    }
    
    state DetectTrigger {
        [*] --> AnalyzeInput
        AnalyzeInput --> CheckPhrases: Parse User Message
        CheckPhrases --> TriggerFound: Match: "make it so", "ship it", etc.
        CheckPhrases --> NoTrigger: No Match
        TriggerFound --> SetFlag: Create trigger_phrase_detected.flag
        SetFlag --> [*]
        NoTrigger --> [*]
    }
```

## Transcript Processing Pipeline

This diagram shows the intelligent transcript processing system for subagent context delivery:

```mermaid
flowchart TD
    A[Task Tool Invoked] --> B[transcript_processor.py Triggered]
    B --> C[Read Claude Code Transcript]
    
    C --> D[Pre-work Removal]
    D --> E{First Edit/Write/MultiEdit Found?}
    E -->|Yes| F[Remove Everything Before First Tool]
    E -->|No| G[Keep Full Transcript]
    
    F --> H[Clean Transcript Format]
    G --> H
    
    H --> I[Convert to {role, content} Format]
    I --> J[Token-Aware Chunking]
    
    J --> K[18k Token Chunks with tiktoken]
    K --> L[Extract Subagent Type from Task Call]
    
    L --> M[Create Target Directory]
    M --> N[.brainworm/state/{subagent_type}/]
    
    N --> O[Save Numbered JSON Chunks]
    O --> P[transcript_chunk_1.json]
    O --> Q[transcript_chunk_2.json]
    O --> R[transcript_chunk_N.json]
    
    P --> S[Set Subagent Context Flag]
    Q --> S
    R --> S
    
    S --> T[in_subagent_context.flag]
    T --> U[Subagent Receives Context]
    
    U --> V[Task Execution with Full Context]
    V --> W[post_tool_use.py Cleanup]
    W --> X[Remove Subagent Flag]
    
    style A fill:#FFE4E1
    style B fill:#E6E6FA
    style T fill:#FFD700
    style U fill:#90EE90
```

## Configuration and Deployment Flow

This diagram illustrates the installation and configuration process:

```mermaid
graph TD
    A[./install Command] --> B[install_hooks.py]
    
    B --> C[Load Governance Manifest]
    C --> D[Detect Installation Mode]
    
    D --> E{Existing Installation?}
    E -->|Yes| F[Intelligent Merge Process]
    E -->|No| G[Fresh Installation]
    
    F --> H[Backup Existing Config]
    H --> I[Merge Hook Configurations]
    I --> J[Preserve User Customizations]
    
    G --> K[Copy All Hook Templates]
    K --> L[Generate settings.json]
    
    J --> M[Update .claude/settings.json]
    L --> M
    
    M --> N[Set Hook Permissions]
    N --> O[Create Directory Structure]
    
    O --> P[.brainworm/hooks/]
    O --> Q[.brainworm/state/]
    O --> R[.brainworm/analytics/]
    O --> S[.brainworm/protocols/]
    
    P --> T[Copy Hooks Framework Infrastructure]
    Q --> U[Initialize State Files]
    R --> V[Setup Analytics Database]
    S --> W[Install Protocol Templates]
    
    T --> X[Hooks Framework Ready]
    U --> X
    V --> X
    W --> X
    
    X --> Y[Installation Complete]
    Y --> Z[Restart Claude Code Required]
    
    style A fill:#FFE4E1
    style X fill:#90EE90
    style Y fill:#90EE90
    style Z fill:#FFD700
```

## Analytics Data Flow

This diagram shows how analytics data flows through the system with optional collection:

```mermaid
sequenceDiagram
    participant Hook as Hook Execution
    participant Framework as Hooks Framework
    participant Logger as Analytics Logger
    participant Processor as Analytics Processor
    participant DB as SQLite Database
    participant Files as JSONL Files
    participant Correlation as Session Correlation

    Hook->>Framework: Execute with enable_analytics=true
    Framework->>Logger: Initialize Analytics Logger
    Logger->>Framework: Logger Instance (or None)
    
    alt Analytics Enabled
        Hook->>Framework: Log Event
        Framework->>Logger: enrich_event_data()
        Logger->>Logger: Add session correlation
        Logger->>Logger: Add DAIC workflow phase
        Logger->>Logger: Add developer info
        Logger->>Processor: process_hook_event()
        
        Processor->>DB: INSERT INTO hook_events
        Processor->>Files: Append to daily JSONL
        Processor->>Correlation: Update session mapping
        
        DB-->>Processor: Success/Failure
        alt DB Write Fails
            Processor->>Processor: Continue (non-blocking)
        end
        
        Processor->>Framework: Analytics Complete
    else Analytics Disabled
        Hook->>Framework: Skip analytics
        Framework->>Hook: Continue execution
    end
    
    Framework->>Hook: Execution Complete
    
    Note over Logger,Correlation: All analytics operations are optional and non-blocking
    Note over DB,Files: Dual storage for reliability
```

## Error Handling and Failsafes

This diagram shows the comprehensive error handling that ensures hook independence:

```mermaid
graph TD
    A[Hook Starts] --> B[Try Import Analytics]
    B --> C{Import Success?}
    
    C -->|Yes| D[Initialize Analytics]
    C -->|No| E[Set Analytics = None]
    
    D --> F{Analytics Init Success?}
    F -->|Yes| G[Enable Analytics Features]
    F -->|No| H[Disable Analytics]
    
    E --> I[Hook Core Logic]
    G --> I
    H --> I
    
    I --> J[Execute Hook Function]
    J --> K{Analytics Enabled?}
    
    K -->|Yes| L[Try Log Event]
    K -->|No| M[Skip Analytics]
    
    L --> N{Log Success?}
    N -->|Yes| O[Analytics Logged]
    N -->|No| P[Continue Without Analytics]
    
    O --> Q[Hook Success]
    P --> Q
    M --> Q
    
    Q --> R[Return to Claude Code]
    
    subgraph "Failsafe Layer"
        E
        H
        P
        M
    end
    
    subgraph "Enhanced Layer"
        G
        L
        O
    end
    
    style E fill:#FFB6C1
    style H fill:#FFB6C1
    style P fill:#FFB6C1
    style M fill:#FFB6C1
    style Q fill:#90EE90
```

## Key Architectural Insights

### Independence Guarantees
- Hooks function completely without analytics system
- Multiple failsafe layers prevent analytics failures from blocking hooks  
- Try/catch blocks around all analytics operations
- Graceful degradation when analytics components unavailable

### Integration Benefits
- Enhanced session correlation when analytics available
- Pattern learning and success prediction
- Real-time monitoring and alerting
- Cross-project organizational learning

### Performance Characteristics
- Hooks Framework overhead: <100ms with full analytics
- Analytics processing: Non-blocking background operations
- Database operations: Optimized with critical indexes
- Memory footprint: Minimal with efficient data structures

## Implementation Dependencies

### Critical Hook Configurations
The system requires specific hook configurations in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": {"tools": ["Task"]}, 
        "hooks": [{"type": "command", "command": "uv run .brainworm/hooks/transcript_processor.py"}]
      },
      {
        "matcher": {"tools": ["Edit", "MultiEdit", "Write", "NotebookEdit"]}, 
        "hooks": [{"type": "command", "command": "uv run .brainworm/hooks/pre_tool_use.py"}]
      }
    ]
  }
}
```

### Installation Validation
- Task tool invocation should create transcript chunks in `.brainworm/state/{subagent_type}/`
- Implementation tools should be blocked in discussion mode
- Analytics database should be created at `.brainworm/analytics/hooks.db`
- Hooks Framework components should be installed in `.brainworm/hooks/utils/`

This process flow documentation provides a comprehensive view of how the brainworm system maintains hook independence while offering powerful analytics enhancements when available.