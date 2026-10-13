# NexShift Agent Evaluation Suite

This directory contains comprehensive evaluation tests for all agents in the NexShift nurse rostering system, following Google ADK evaluation patterns.

## Structure

```
eval/
├── test_config.json          # Global evaluation configuration
├── test_agent_eval.py        # Pytest runner for all evaluations
├── README.md                 # This file
│
├── compliance/               # ComplianceOfficer agent tests
│   ├── compliance.evalset.json
│   └── compliance_validation.test.json
│
├── coordinator/              # RosteringCoordinator agent tests
│   ├── coordinator.evalset.json
│   └── query_routing.test.json
│
├── empathy/                  # EmpathyAdvocate agent tests
│   ├── empathy.evalset.json
│   └── empathy_review.test.json
│
├── solver/                   # RosterSolver agent tests
│   ├── solver.evalset.json
│   └── roster_generation.test.json
│
├── context_gatherer/         # ContextGatherer agent tests
│   ├── context_gatherer.evalset.json
│   └── context_gathering.test.json
│
├── presenter/                # RosterPresenter agent tests
│   ├── presenter.evalset.json
│   └── presentation.test.json
│
├── workflow/                 # End-to-end workflow tests
│   ├── workflow.evalset.json
│   └── scenarios/
│       └── e2e_workflows.test.json
│
└── test_data/                # Test fixtures
    ├── nurses/               # Nurse team configurations
    ├── rosters/              # Sample roster data
    └── shifts/               # Shift requirement configurations
```

## Running Evaluations

### Run All Tests
```bash
pytest evals/test_agent_eval.py -v
```

### Run Specific Agent Tests
```bash
# ComplianceOfficer tests
pytest evals/test_agent_eval.py -v -k "compliance"

# Coordinator tests
pytest evals/test_agent_eval.py -v -k "coordinator"

# EmpathyAdvocate tests
pytest evals/test_agent_eval.py -v -k "empathy"

# RosterSolver tests
pytest evals/test_agent_eval.py -v -k "solver"

# ContextGatherer tests
pytest evals/test_agent_eval.py -v -k "context_gatherer"

# RosterPresenter tests
pytest evals/test_agent_eval.py -v -k "presenter"

# E2E Workflow tests
pytest evals/test_agent_eval.py -v -k "workflow"
```

### Run Specific Test Case
```bash
pytest evals/test_agent_eval.py -v -k "validate_roster_with_explicit_id"
```

### Generate Report
```bash
python evals/test_agent_eval.py --report
```

## Test Case Format

Each `.test.json` file contains test cases with the following structure:

```json
{
  "description": "Description of the test suite",
  "test_cases": [
    {
      "name": "test_case_name",
      "description": "What this test verifies",
      "input": "User input to the agent",
      "expected_tool_trajectory": [
        {"tool_name": "tool_name", "args": {"arg1": "value1"}}
      ],
      "expected_response_contains": ["keyword1", "keyword2"],
      "expected_response_not_contains": ["unwanted1"],
      "session_state": {
        "key": "initial session state value"
      }
    }
  ]
}
```

## Evaluation Metrics

### Tool Trajectory Score
Measures whether the agent calls the expected tools:
- **1.0**: All expected tools called
- **0.5-0.9**: Partial match
- **0.0**: No expected tools called

Threshold: 0.85-0.9 (configurable per evalset)

### Response Match Score
Measures response content quality:
- Checks for expected keywords/phrases
- Checks absence of unwanted content

Threshold: 0.5-0.6 (configurable per evalset)

## Test Categories

### ComplianceOfficer (14 tests)
- Tool calling correctness
- Error handling (non-existent rosters)
- Specific compliance checks (certifications, seniority, hours)
- Information retrieval

### Coordinator (25 tests)
- Query routing (nurse, shift, staffing queries)
- Roster management operations
- HRIS management (hiring, promotions)
- Direct validation

### EmpathyAdvocate (13 tests)
- Basic fairness review
- Detailed analysis (nurse-by-nurse)
- Specific checks (fatigue, preferences, weekends, nights)
- Recommendations

### RosterSolver (10 tests)
- Basic roster generation
- Custom periods and dates
- Staffing simulations
- Overlap handling
- Failure recovery

### ContextGatherer (8 tests)
- Full context gathering
- Specific queries
- Ready-for-generation assessment

### RosterPresenter (11 tests)
- Presentation formatting
- Approval/rejection flow
- Failure handling
- Roster management

### E2E Workflow (10 tests)
- Complete generation workflow
- Multi-turn conversations
- Failure recovery
- Query-then-generate patterns

## Adding New Tests

1. Add test cases to the appropriate `.test.json` file
2. Update categories in the corresponding `.evalset.json` if needed
3. Run `pytest` to verify the new tests

## Test Data Fixtures

### Nurse Teams
- `normal_team.json`: 10 nurses with varied certifications
- `minimal_team.json`: 2 nurses for capacity failure tests
- `no_icu_team.json`: No ICU certified nurses
- `high_fatigue_team.json`: All nurses with high fatigue

### Sample Rosters
- `valid_roster.json`: All compliance rules satisfied
- `consecutive_violation_roster.json`: >5 consecutive shifts
- `night_day_violation_roster.json`: Night-to-day transitions
- `understaffed_roster.json`: Missing required coverage

### Shift Requirements
- `standard_requirements.json`: Normal ward requirements
- `icu_requirements.json`: ICU-specific requirements
