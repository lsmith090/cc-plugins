# Brainworm Analytics System

Background intelligence system that quietly captures development patterns and builds organizational knowledge while enforcing DAIC workflow discipline.

## Overview

Brainworm's analytics layer operates transparently in the background, capturing development activity through the Hooks Framework to:

- **Enhanced Correlation**: Bridge-based session correlation with 95%+ accuracy for direct session links
- **Pattern Intelligence**: Evolutionary analysis of workflow patterns and platform optimization
- **Platform Evolution**: Data-driven recommendations for brainworm platform improvements
- **Build Memory**: Organizational knowledge that improves over time
- **Quality Assessment**: Automated data integrity monitoring and improvement

## Intelligence Features

### Bridge-Based Correlation
The enhanced correlation engine uses a session ID bridge table to achieve high-confidence session-hook correlations:
- **Direct Correlation**: Session IDs provide exact hook-session matching
- **Confidence Scoring**: 0.0-1.0 confidence ratings with method tracking
- **Multi-Strategy**: Bridge, temporal, and fuzzy correlation methods
- **Actionable Insights**: AI-generated recommendations based on correlation analysis

### Evolutionary Intelligence
Analytics focus on platform evolution rather than real-time monitoring:
- **Workflow Pattern Analysis**: DAIC mode effectiveness and optimization opportunities
- **Hook Performance Intelligence**: Individual hook analysis for platform improvements
- **Development Success Patterns**: Template generation from optimal workflows
- **Platform Recommendations**: Data-driven enhancements for brainworm components

### Data Quality Intelligence
Comprehensive assessment of analytics data integrity:
- **Quality Scoring**: 0.0-1.0 assessments across consistency, completeness, accuracy
- **Automated Monitoring**: Threshold-based quality alerts and recommendations
- **Improvement Insights**: Specific recommendations for data quality enhancement
- **Reliability Metrics**: Session correlation confidence and data trustworthiness

**Performance**: <100ms overhead with 29MB local database (optimized with critical indexes)

## Analytics Commands

### Local Session Analytics
```bash
# View captured session data
uv run .brainworm/hooks/view_analytics.py

# Session analytics with verbose output
uv run .brainworm/hooks/view_analytics.py --verbose

# Test analytics capture
echo '{"session_id": "test"}' | uv run .brainworm/hooks/stop.py --verbose --analytics
```

### Multi-Project Analytics
```bash
# View insights across multiple projects
uv run src/analytics/view_central_analytics.py

# Check data harvesting status
uv run src/analytics/harvest_data.py --stats

# Set up automated data collection (15-minute intervals)
uv run src/analytics/manage_cron.py install
```

### Enhanced Intelligence Analytics
```bash
# Enhanced session correlation with bridge confidence
uv run src/analytics/enhanced_correlation_engine.py

# Development pattern analysis dashboard
uv run src/analytics/realtime_dashboard.py

# Workflow evolution pattern analysis
uv run src/analytics/workflow_evolution_analyzer.py

# Data quality assessment
uv run src/analytics/data_quality_analyzer.py

# Hook evolution analysis
uv run src/analytics/hook_evolution_analyzer.py

# Subagent effectiveness analysis
uv run src/analytics/subagent_evolution_analyzer.py
```

### Core Analytics
```bash
# DuckDB-powered analytics queries
uv run src/analytics/duckdb_analytics.py --workflows

# Session success prediction
uv run src/analytics/predictive_session_model.py --monitor

# Database optimization
uv run src/analytics/optimize_database.py
```

## What Gets Captured

**Session Activity**:
- Tool usage patterns and timing
- DAIC workflow transitions and effectiveness
- File modification patterns
- Context usage and efficiency metrics
- Success/failure patterns

**Development Patterns**:
- Workflow sequences that lead to successful outcomes
- Common failure modes and prevention strategies
- Task completion time and quality correlations
- Subagent usage effectiveness

**Organizational Learning**:
- Cross-project pattern recognition
- Team collaboration effectiveness
- Knowledge retention across sessions
- Skill development tracking

## Privacy & Security

**Local First**: Analytics operate on local data by default
**Opt-in Sharing**: Multi-project learning requires explicit configuration
**Data Minimization**: Only captures workflow patterns, not code content
**Security Hardening**: All data processed through framework validation
**User Control**: Analytics can be disabled via `brainworm-config.toml`

## Configuration

### Enable/Disable Analytics
```toml
# brainworm-config.toml
[analytics]
enabled = true                    # Enable analytics capture
quiet_mode = true                 # Minimal user-visible output
session_correlation = true        # Enable session linking
pattern_learning = true           # Enable success pattern capture
organizational_learning = false   # Multi-project learning (opt-in)
```

### Data Storage
- **Local Database**: `.brainworm/hooks/analytics.db` (session data)
- **Central Database**: `.brainworm/analytics/central_hooks.db` (multi-project correlation)
- **Enhanced Correlations**: `enhanced_correlations` table with bridge confidence data
- **Correlation Insights**: `correlation_insights` table for AI-generated recommendations
- **Session Bridge**: `session_id_bridge` table for high-confidence correlation mapping
- **Memory Files**: `.brainworm/memory/` (session memories and insights)

## Analytics Insights

### Enhanced Session Correlation
Advanced correlation engine with session ID bridge technology provides:
- **Bridge Confidence Scoring**: Direct session-hook correlation through session_id_bridge table
- **95%+ accuracy** for high-confidence correlations using session ID matching
- **Multi-strategy correlation**: Bridge, temporal, and fuzzy matching methods
- **Actionable Intelligence**: AI-generated insights for development optimization
- **Cross-project correlation**: Multi-repository session pattern learning

### Pattern-Based Intelligence
Evolutionary intelligence system identifies and learns from patterns:
- **Workflow Evolution Analysis**: DAIC mode effectiveness and optimization opportunities
- **Hook Effectiveness Patterns**: Performance analysis of hook implementations
- **Development Pattern Recognition**: Successful workflow sequence identification
- **Platform Evolution**: Data-driven platform improvement recommendations
- **Success Template Generation**: Extract and replicate optimal development patterns

### Development Pattern Analysis Dashboard
Evolutionary intelligence dashboard provides:
- **Pattern Analysis Metrics**: Hook effectiveness and workflow efficiency scoring
- **DAIC Success Rate Tracking**: Discussion/implementation mode effectiveness
- **Correlation Intelligence**: Bridge confidence and session correlation insights
- **Performance Optimization**: Development bottleneck identification and resolution
- **Evolutionary Recommendations**: AI-generated platform improvement suggestions

## Benefits

**For Individual Developers**:
- Session continuity across time gaps
- Personalized workflow optimization suggestions
- Early warning for problematic patterns
- Skill development tracking

**For Teams**:
- Organizational pattern recognition
- Best practice identification and sharing
- Team collaboration effectiveness metrics
- Knowledge retention across personnel changes

**For Organizations**:
- Cross-project learning and optimization
- Development process improvement insights
- Resource allocation optimization
- Quality prediction and improvement

## Advanced Analytics Components

### Enhanced Correlation Engine
**Location**: `src/analytics/enhanced_correlation_engine.py`
- Bridge-based session correlation with 90%+ confidence for direct session links
- DuckDB-powered analytical views for complex pattern analysis
- Actionable insight generation with confidence and impact scoring
- Multi-strategy correlation: bridge, temporal, and fuzzy matching

### Development Pattern Analysis Dashboard  
**Location**: `src/analytics/realtime_dashboard.py`
- Evolutionary intelligence for platform improvement rather than real-time alerting
- Pattern analysis metrics including hook effectiveness and workflow efficiency
- DAIC success rate tracking and optimization recommendations
- Export capabilities for external analysis and reporting

### Workflow Evolution Analyzer
**Location**: `src/analytics/workflow_evolution_analyzer.py`
- DAIC mode usage analysis and optimization opportunities
- Workflow pattern performance metrics with bottleneck identification
- Evolutionary improvement recommendations for platform enhancements
- Success template generation from optimal workflow patterns

### Data Quality Analyzer
**Location**: `src/analytics/data_quality_analyzer.py`
- Comprehensive data quality assessment with scoring (0.0-1.0)
- Completeness, consistency, accuracy, and reliability metrics
- Automated improvement recommendations for analytics data
- Quality threshold monitoring and alerting

### Hook Evolution Analyzer
**Location**: `src/analytics/hook_evolution_analyzer.py`
- Individual hook performance analysis and optimization
- Hook effectiveness patterns and improvement opportunities
- Platform enhancement recommendations based on hook usage
- Success correlation analysis for hook implementations

### Subagent Evolution Analyzer
**Location**: `src/analytics/subagent_evolution_analyzer.py`
- Subagent effectiveness and usage pattern analysis
- Performance optimization recommendations for agent workflows
- Success pattern identification in agent-assisted development
- Agent utilization efficiency metrics

## Technical Architecture

### Enhanced Correlation Engine
**Bridge Intelligence**: Session ID bridge table provides direct hook-session correlation
**DuckDB Analytics**: High-performance analytical queries with SQLite integration
**Confidence Scoring**: Multi-method correlation with 0.0-1.0 confidence ratings
**Insight Generation**: AI-powered actionable recommendations based on pattern analysis

### Pattern Analysis System
**Workflow Evolution**: DAIC mode effectiveness and transition pattern analysis
**Hook Performance**: Individual hook effectiveness scoring and optimization identification
**Development Intelligence**: Cross-session learning and success pattern replication
**Platform Evolution**: Data-driven enhancement recommendations for brainworm platform

### Data Quality & Performance
**Database**: Optimized SQLite with critical indexes for <100ms queries
**Framework Integration**: Type-safe processing through Hooks Framework
**Data Quality Assessment**: Automated data integrity monitoring and improvement
**Performance**: Minimal overhead validated with 29MB database under production load
**Export Capabilities**: JSON export of metrics and insights for external analysis

---

*Analytics operate transparently in the background, enhancing DAIC workflow enforcement with intelligent insights and organizational learning.*