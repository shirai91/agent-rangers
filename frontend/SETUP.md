# Agent Rangers Frontend - Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd /home/shirai91/projects/personal/agent-rangers/frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The application will be available at http://localhost:5173

### 3. Using Docker (Recommended)

From the root directory:

```bash
cd /home/shirai91/projects/personal/agent-rangers
docker-compose up frontend
```

## Project Overview

This is a production-ready React 19 frontend for the Agent Rangers Kanban Framework with the following features:

### Core Technologies

- **React 19** - Latest version with improved performance
- **TypeScript** - Strict mode enabled for type safety
- **Vite** - Lightning-fast build tool
- **Tailwind CSS v4** - Modern utility-first CSS
- **Zustand** - Lightweight state management
- **@dnd-kit** - Modern drag-and-drop library
- **shadcn/ui** - High-quality UI components
- **Native WebSocket** - Real-time updates

### Key Features

1. **Board Management**
   - Create, view, and delete boards
   - Board list view with cards
   - Navigate between boards

2. **Column Management**
   - Add columns to boards
   - Edit column names
   - Delete columns with confirmation
   - Automatic task cleanup

3. **Task Management**
   - Create tasks with rich details (title, description, assignee, priority)
   - Edit task information
   - Delete tasks
   - Drag & drop between columns
   - Reorder tasks within columns
   - Priority badges (High, Medium, Low)
   - Assignee tags

4. **Drag and Drop**
   - Smooth drag-and-drop experience
   - Fractional ordering system for precise positioning
   - Visual feedback during dragging
   - Touch-friendly for mobile
   - Optimistic updates

5. **Real-time Sync**
   - WebSocket connection per board
   - Live updates for all CRUD operations
   - Automatic reconnection with backoff
   - Optimistic UI updates

## Architecture

### State Management (Zustand)

The application uses Zustand for state management with a single store:

```typescript
// src/stores/boardStore.ts
- boards: Board[]
- currentBoard: Board | null
- columns: Column[]
- tasks: Task[]
- loading: boolean
- error: string | null
```

**Actions:**
- Board CRUD: `fetchBoards`, `fetchBoard`, `createBoard`, `deleteBoard`
- Column CRUD: `createColumn`, `updateColumn`, `deleteColumn`
- Task CRUD: `createTask`, `updateTask`, `deleteTask`, `moveTask`
- Optimistic updates: `optimisticMoveTask`
- WebSocket handlers: `handleTaskCreated`, `handleTaskUpdated`, etc.

### API Client

Type-safe REST API client with error handling:

```typescript
// src/api/client.ts
- Centralized fetch wrapper
- Automatic JSON parsing
- Error handling with typed responses
- Environment-based URL configuration
```

### WebSocket Hook

Custom hook for real-time updates:

```typescript
// src/hooks/useWebSocket.ts
- Connects to ws://localhost:8000/ws/boards/{boardId}
- Automatic reconnection (max 5 attempts)
- Event handling for all operations
- Cleanup on unmount
```

### Component Structure

**Main Components:**
- `App.tsx` - Main application with routing logic
- `Board.tsx` - Drag-and-drop board with DndContext
- `Column.tsx` - Column with droppable area and sortable tasks
- `TaskCard.tsx` - Draggable task card with actions

**Dialog Components:**
- `CreateBoardDialog.tsx` - Board creation form
- `CreateColumnDialog.tsx` - Column create/edit form
- `CreateTaskDialog.tsx` - Task create/edit form

**UI Components (shadcn/ui):**
- `Button`, `Card`, `Input`, `Label`
- `Dialog`, `DropdownMenu`
- `Badge`, `Skeleton`

## Drag and Drop Implementation

### Fractional Ordering

Tasks use fractional ordering for smooth reordering:

```typescript
// When dropping between items
newOrder = (prevOrder + nextOrder) / 2

// When dropping at start
newOrder = firstItem.order / 2

// When dropping at end
newOrder = lastItem.order + 1
```

### DnD Flow

1. **DragStart** - Set active task for overlay
2. **DragOver** - Handle cross-column moves, update optimistically
3. **DragEnd** - Calculate final position, persist to backend
4. **Error** - Revert optimistic update on failure

### Collision Detection

Uses `closestCorners` algorithm from @dnd-kit for best drag experience.

## TypeScript Configuration

Strict mode enabled with:
- `strict: true`
- `noImplicitAny: true`
- `strictNullChecks: true`
- `noUncheckedIndexedAccess: true`
- Path aliases: `@/*` → `./src/*`

## Styling

### Tailwind CSS v4

Custom theme with CSS variables:

```css
:root {
  --background, --foreground
  --primary, --primary-foreground
  --secondary, --secondary-foreground
  --muted, --muted-foreground
  --accent, --accent-foreground
  --destructive, --destructive-foreground
  --border, --input, --ring
  --radius
}
```

### Dark Mode Ready

Dark mode classes configured (add `dark` class to HTML element).

## Environment Variables

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Build & Deployment

### Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm run preview
```

### Docker
```bash
docker build -t agent-rangers-frontend .
docker run -p 5173:5173 agent-rangers-frontend
```

### Docker Compose
```bash
docker-compose up frontend
```

## File Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts              # REST API client
│   ├── components/
│   │   ├── ui/                    # shadcn/ui components
│   │   │   ├── badge.tsx
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── dropdown-menu.tsx
│   │   │   ├── input.tsx
│   │   │   ├── label.tsx
│   │   │   └── skeleton.tsx
│   │   ├── Board.tsx              # Main board with DnD
│   │   ├── Column.tsx             # Column component
│   │   ├── TaskCard.tsx           # Task card component
│   │   ├── CreateBoardDialog.tsx  # Board creation
│   │   ├── CreateColumnDialog.tsx # Column create/edit
│   │   └── CreateTaskDialog.tsx   # Task create/edit
│   ├── hooks/
│   │   └── useWebSocket.ts        # WebSocket hook
│   ├── lib/
│   │   └── utils.ts               # Utility functions
│   ├── stores/
│   │   └── boardStore.ts          # Zustand store
│   ├── types/
│   │   └── index.ts               # TypeScript types
│   ├── App.tsx                    # Main app component
│   ├── main.tsx                   # Entry point
│   └── index.css                  # Global styles
├── Dockerfile                     # Container config
├── package.json                   # Dependencies
├── vite.config.ts                 # Vite config
├── tsconfig.json                  # TypeScript config
├── tailwind.config.js             # Tailwind config
├── postcss.config.js              # PostCSS config
├── components.json                # shadcn/ui config
├── index.html                     # HTML template
└── README.md                      # Documentation
```

## Testing the Application

1. **Start the backend** (from root directory):
   ```bash
   docker-compose up backend
   ```

2. **Start the frontend**:
   ```bash
   docker-compose up frontend
   ```

3. **Open browser**: http://localhost:5173

4. **Test features**:
   - Create a new board
   - Add columns (e.g., "To Do", "In Progress", "Done")
   - Create tasks with different priorities
   - Drag tasks between columns
   - Edit tasks and columns
   - Open multiple tabs to see real-time sync

## Troubleshooting

### Port 5173 already in use
```bash
# Kill the process using the port
lsof -ti:5173 | xargs kill -9
```

### WebSocket connection failed
- Ensure backend is running on port 8000
- Check CORS configuration in backend
- Verify WebSocket URL in .env

### TypeScript errors
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Build errors
```bash
# Check TypeScript errors
npx tsc --noEmit
```

## Performance Optimizations

- **Code splitting** - Vite handles automatically
- **Lazy loading** - Ready for route-based splitting
- **Optimistic updates** - Instant UI feedback
- **WebSocket** - Efficient real-time updates
- **Memoization** - useMemo for computed values

## Security Features

- **Type safety** - TypeScript strict mode
- **Input validation** - Required fields enforced
- **Confirmation dialogs** - For destructive actions
- **Error boundaries** - Ready to implement
- **CORS** - Configured in backend

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Next Steps

1. Add authentication (JWT tokens)
2. Implement user management
3. Add file attachments to tasks
4. Implement comments/activity log
5. Add board templates
6. Export/import functionality
7. Advanced filtering and search
8. Email notifications
9. Mobile app with React Native
10. Analytics dashboard

## Contributing

This is a production-ready codebase following best practices:
- Clean component architecture
- Type-safe throughout
- Error handling
- Loading states
- Optimistic updates
- Real-time sync
- Responsive design
- Accessible UI components

## License

MIT
