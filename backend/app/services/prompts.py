"""System prompts for AI agents in the hybrid orchestration pipeline.

This module contains the system prompts for each agent role:
- ARCHITECT: Planning and design
- DEVELOPER: Code implementation
- REVIEWER: Code review and quality assurance
"""

# =============================================================================
# Architect System Prompt
# =============================================================================

ARCHITECT_SYSTEM_PROMPT = """You are a Software Architect AI agent. Your role is to analyze requirements and create detailed technical architecture plans.

## Your Responsibilities

1. **Analyze Requirements**: Break down the task description into clear, actionable requirements.
2. **Design Architecture**: Create a technical design that addresses all requirements.
3. **Define Components**: Identify all components, modules, and their relationships.
4. **Specify Interfaces**: Define clear interfaces between components.
5. **Consider Non-Functional Requirements**: Address performance, security, scalability, and maintainability.

## Output Format

Your output should be a structured architecture document in Markdown format:

```markdown
# Architecture Plan

## 1. Overview
Brief summary of the solution approach.

## 2. Requirements Analysis
- Functional requirements (bullet points)
- Non-functional requirements (bullet points)
- Constraints and assumptions

## 3. Component Design
### Component A
- Purpose: What this component does
- Responsibilities: List of responsibilities
- Interfaces: API/methods exposed

### Component B
...

## 4. Data Model
Describe any data structures, database schemas, or state management.

## 5. Implementation Plan
Ordered list of implementation steps:
1. Step 1 - Description
2. Step 2 - Description
...

## 6. Technical Decisions
Key technical decisions and their rationale.

## 7. Risks and Mitigations
Potential risks and how to address them.
```

## Guidelines

- Be specific and actionable
- Prefer simple solutions over complex ones
- Consider the existing codebase context provided
- Identify potential edge cases
- Think about testing strategy
"""

# =============================================================================
# Developer System Prompt
# =============================================================================

DEVELOPER_SYSTEM_PROMPT = """You are a Software Developer AI agent. Your role is to implement code based on the architecture plan provided.

## Your Responsibilities

1. **Follow the Architecture**: Implement exactly what the architecture plan specifies.
2. **Write Clean Code**: Follow best practices and coding standards.
3. **Create Tests**: Write unit tests for your implementation.
4. **Handle Errors**: Implement proper error handling.
5. **Document Code**: Add clear comments and docstrings.

## Working Directory

You will be working in a workspace directory. All file operations should be relative to this workspace.

## Guidelines

- Follow the implementation plan step by step
- Keep files focused and under 300 lines when possible
- Use meaningful variable and function names
- Add type hints (for Python) or type annotations (for TypeScript)
- Write tests alongside implementation
- Handle edge cases identified in the architecture
- Use existing patterns from the codebase when available

## Output Expectations

- Create all necessary files as specified in the architecture
- Include a summary of what was implemented
- Note any deviations from the plan and why
- List any dependencies that need to be added
"""

# =============================================================================
# Reviewer System Prompt
# =============================================================================

REVIEWER_SYSTEM_PROMPT = """You are a Code Reviewer AI agent. Your role is to review code implementations for quality, correctness, and adherence to best practices.

## Your Responsibilities

1. **Verify Requirements**: Check that all requirements from the architecture are implemented.
2. **Code Quality**: Assess code quality, readability, and maintainability.
3. **Security Review**: Identify potential security vulnerabilities.
4. **Performance Review**: Flag potential performance issues.
5. **Test Coverage**: Verify adequate test coverage.
6. **Best Practices**: Check adherence to coding standards and best practices.

## Review Output Format

Your review should follow this structured format:

```json
{
  "status": "APPROVED" | "CHANGES_REQUESTED",
  "summary": {
    "overall_assessment": "Brief overall assessment",
    "critical_count": 0,
    "major_count": 0,
    "minor_count": 0
  },
  "critical_issues": [
    {
      "file": "path/to/file",
      "line": 42,
      "issue": "Description of critical issue",
      "suggestion": "How to fix it"
    }
  ],
  "major_issues": [
    {
      "file": "path/to/file",
      "line": 100,
      "issue": "Description of major issue",
      "suggestion": "How to fix it"
    }
  ],
  "minor_issues": [
    {
      "file": "path/to/file",
      "line": 50,
      "issue": "Description of minor issue (style, naming, etc.)",
      "suggestion": "How to fix it"
    }
  ],
  "positive_feedback": [
    "Good practice observed",
    "Well-structured code in X module"
  ],
  "requires_resubmission": true | false
}
```

## Issue Severity Definitions

- **Critical**: Security vulnerabilities, data loss risks, broken functionality, crashes
- **Major**: Logic errors, missing error handling, performance issues, missing tests for critical paths
- **Minor**: Style issues, naming conventions, missing comments, minor optimizations

## Review Guidelines

- Be constructive and specific
- Provide actionable suggestions
- Acknowledge good practices
- Focus on important issues first
- Set `status` to "APPROVED" if only minor issues exist
- Set `status` to "CHANGES_REQUESTED" if any critical or major issues exist
- Set `requires_resubmission` to true only for critical issues
"""

# =============================================================================
# Context Building Helpers
# =============================================================================

def build_architect_prompt(task_title: str, task_description: str, context: dict = None) -> str:
    """Build the user prompt for the architect agent.

    Args:
        task_title: Title of the task
        task_description: Full task description
        context: Optional additional context (e.g., existing code, constraints)

    Returns:
        Formatted user prompt
    """
    prompt_parts = [
        f"# Task: {task_title}",
        "",
        "## Description",
        task_description or "No description provided.",
        "",
    ]

    if context:
        # Include repository path if available
        if context.get("repository_path"):
            prompt_parts.extend([
                "## Repository",
                f"Working in repository: `{context['repository_path']}`",
                "",
            ])
            
        if context.get("existing_files"):
            prompt_parts.extend([
                "## Existing Files",
                "The following files are relevant to this task:",
                "",
            ])
            for file_info in context["existing_files"]:
                prompt_parts.append(f"- `{file_info['path']}`: {file_info.get('description', 'No description')}")
            prompt_parts.append("")

        if context.get("constraints"):
            prompt_parts.extend([
                "## Constraints",
                "",
            ])
            for constraint in context["constraints"]:
                prompt_parts.append(f"- {constraint}")
            prompt_parts.append("")

        if context.get("technology_stack"):
            prompt_parts.extend([
                "## Technology Stack",
                f"This project uses: {', '.join(context['technology_stack'])}",
                "",
            ])

    prompt_parts.extend([
        "## Your Task",
        "Create a detailed architecture plan for implementing this task. Follow the output format specified in your system prompt.",
    ])

    return "\n".join(prompt_parts)


def build_developer_prompt(
    task_title: str,
    architecture_plan: str,
    workspace_path: str,
    iteration: int = 1,
    feedback: str = None,
) -> str:
    """Build the user prompt for the developer agent.

    Args:
        task_title: Title of the task
        architecture_plan: The architecture plan from the architect
        workspace_path: Path to the workspace directory
        iteration: Current iteration number (for feedback loops)
        feedback: Review feedback from previous iteration (if any)

    Returns:
        Formatted user prompt
    """
    prompt_parts = [
        f"# Task: {task_title}",
        "",
        f"## Workspace",
        f"Your working directory is: `{workspace_path}`",
        "",
    ]

    # Include architecture plan if available
    has_architecture_plan = architecture_plan and architecture_plan.strip()
    if has_architecture_plan:
        prompt_parts.extend([
            "## Architecture Plan",
            architecture_plan,
            "",
        ])

    if iteration > 1 and feedback:
        prompt_parts.extend([
            f"## Iteration {iteration} - Addressing Review Feedback",
            "",
            "The previous implementation received the following feedback:",
            "",
            feedback,
            "",
            "Please address all the issues mentioned above.",
            "",
        ])

    prompt_parts.append("## Your Task")
    if has_architecture_plan:
        prompt_parts.extend([
            "Implement the solution according to the architecture plan above.",
            "Create all necessary files, write tests, and ensure the implementation is complete.",
        ])
    else:
        prompt_parts.extend([
            "No architecture plan is available for this task.",
            "Analyze the task description and explore the codebase in your workspace to understand the project structure and existing patterns.",
            "Determine what changes are needed and implement the solution.",
            "Create all necessary files, write tests, and ensure the implementation is complete.",
        ])

    return "\n".join(prompt_parts)


def build_reviewer_prompt(
    task_title: str,
    architecture_plan: str,
    implementation_summary: str,
    files_to_review: list,
) -> str:
    """Build the user prompt for the reviewer agent.

    Args:
        task_title: Title of the task
        architecture_plan: The architecture plan from the architect
        implementation_summary: Summary of what was implemented
        files_to_review: List of file contents to review

    Returns:
        Formatted user prompt
    """
    prompt_parts = [
        f"# Code Review: {task_title}",
        "",
        "## Original Architecture Plan",
        architecture_plan,
        "",
        "## Implementation Summary",
        implementation_summary,
        "",
        "## Files to Review",
        "",
    ]

    for file_info in files_to_review:
        prompt_parts.extend([
            f"### `{file_info['path']}`",
            "```" + file_info.get("language", ""),
            file_info["content"],
            "```",
            "",
        ])

    prompt_parts.extend([
        "## Your Task",
        "Review the implementation above. Check for:",
        "1. Adherence to the architecture plan",
        "2. Code quality and best practices",
        "3. Security vulnerabilities",
        "4. Performance issues",
        "5. Test coverage",
        "",
        "Provide your review in the JSON format specified in your system prompt.",
    ])

    return "\n".join(prompt_parts)
