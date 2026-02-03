# Agent Rangers Documentation

Welcome to the Agent Rangers documentation. This folder contains all technical documentation for the project.

## Quick Links

| Document | Description |
|----------|-------------|
| [PRD.md](./PRD.md) | Product Requirements Document - What we're building and why |
| [APP_FLOW.md](./APP_FLOW.md) | User flows and navigation - How users interact with the app |
| [TECH_STACK.md](./TECH_STACK.md) | Technology stack - Exact versions and dependencies |
| [FRONTEND_GUIDELINES.md](./FRONTEND_GUIDELINES.md) | Design system - Colors, typography, components |
| [BACKEND_STRUCTURE.md](./BACKEND_STRUCTURE.md) | Backend architecture - Database schema, API contracts |
| [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) | Build sequence - Step-by-step implementation guide |

## Document Purposes

### PRD.md
Start here to understand:
- Project vision and goals
- Feature specifications
- User stories
- Acceptance criteria
- Non-functional requirements

### APP_FLOW.md
Reference for:
- Screen inventory
- User interaction flows
- WebSocket events
- Error handling flows
- Loading states

### TECH_STACK.md
Reference for:
- Exact package versions
- Frontend dependencies
- Backend dependencies
- Docker configuration
- Environment variables

### FRONTEND_GUIDELINES.md
Reference for:
- Color palette (with CSS variables)
- Typography scale
- Spacing system
- Component library
- Animation standards
- Accessibility requirements

### BACKEND_STRUCTURE.md
Reference for:
- Database schema
- SQLAlchemy models
- Pydantic schemas
- API endpoints (with examples)
- Service layer patterns
- WebSocket implementation

### IMPLEMENTATION_PLAN.md
Reference for:
- Build order (don't skip steps!)
- Time estimates
- Verification checklists
- Rollback procedures

## How to Use These Docs

### For New Developers
1. Read **PRD.md** first to understand the project
2. Review **TECH_STACK.md** to set up your environment
3. Study **APP_FLOW.md** to understand user interactions
4. Reference **FRONTEND_GUIDELINES.md** or **BACKEND_STRUCTURE.md** based on your task

### For AI Coding Agents
1. Always read relevant documentation before starting a task
2. Follow **IMPLEMENTATION_PLAN.md** for build order
3. Reference **TECH_STACK.md** for exact versions
4. Use **FRONTEND_GUIDELINES.md** for UI consistency
5. Follow **BACKEND_STRUCTURE.md** patterns for backend code

### For Code Reviews
- Verify UI matches **FRONTEND_GUIDELINES.md**
- Verify API matches **BACKEND_STRUCTURE.md**
- Check implementation follows **IMPLEMENTATION_PLAN.md** sequence

## Keeping Docs Updated

- Update docs when making significant changes
- Each document has a "Last Updated" date
- Review cycle: After each phase completion
- Owner: Agent Rangers Team

## Questions?

If something is unclear or missing:
1. Check if the answer is in another document
2. If not, update the relevant document with the answer
3. Document assumptions and decisions in daily memory files

---

*Documentation is code. Keep it accurate and useful.*
