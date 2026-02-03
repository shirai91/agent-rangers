# Agent Rangers Frontend

A modern, real-time Kanban board application built with React 19, TypeScript, and Tailwind CSS.

## Features

- **Modern Stack**: React 19, TypeScript, Vite, Tailwind CSS v4
- **Real-time Updates**: WebSocket integration for live collaboration
- **Drag & Drop**: Intuitive task management with @dnd-kit
- **State Management**: Zustand for efficient state handling
- **UI Components**: shadcn/ui for beautiful, accessible components
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Tech Stack

- **React 19** - Latest React with improved hooks and performance
- **TypeScript** - Type-safe development with strict mode
- **Vite** - Lightning-fast build tool and dev server
- **Tailwind CSS v4** - Utility-first CSS framework
- **Zustand** - Lightweight state management
- **@dnd-kit** - Modern drag-and-drop toolkit
- **shadcn/ui** - High-quality, accessible UI components
- **Lucide React** - Beautiful icon library

## Getting Started

### Prerequisites

- Node.js 20 or higher
- npm or yarn

### Installation

1. Install dependencies:

```bash
npm install
```

2. Copy the environment file:

```bash
cp .env.example .env
```

3. Update the `.env` file with your backend URL if different from defaults:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Development

Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Build

Build for production:

```bash
npm run build
```

Preview production build:

```bash
npm run preview
```

### Docker

Build and run with Docker:

```bash
docker build -t agent-rangers-frontend .
docker run -p 5173:5173 agent-rangers-frontend
```

Or use docker-compose from the root directory:

```bash
docker-compose up frontend
```

## Project Structure

```
frontend/
├── src/
│   ├── components/        # React components
│   │   ├── ui/           # shadcn/ui components
│   │   ├── Board.tsx     # Main board component
│   │   ├── Column.tsx    # Column component
│   │   ├── TaskCard.tsx  # Task card component
│   │   └── ...           # Dialog components
│   ├── stores/           # Zustand stores
│   │   └── boardStore.ts # Board state management
│   ├── hooks/            # Custom React hooks
│   │   └── useWebSocket.ts # WebSocket hook
│   ├── api/              # API client
│   │   └── client.ts     # HTTP client
│   ├── types/            # TypeScript types
│   │   └── index.ts      # Type definitions
│   ├── lib/              # Utilities
│   │   └── utils.ts      # Helper functions
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── public/               # Static assets
├── index.html           # HTML template
├── vite.config.ts       # Vite configuration
├── tsconfig.json        # TypeScript configuration
├── tailwind.config.js   # Tailwind configuration
└── package.json         # Dependencies
```

## Features in Detail

### Board Management

- Create multiple boards for different projects
- View all boards in a grid layout
- Delete boards with confirmation

### Column Management

- Add columns to organize tasks
- Edit column names
- Delete columns (removes all contained tasks)
- Drag and drop tasks between columns

### Task Management

- Create tasks with title, description, assignee, and priority
- Edit task details
- Delete tasks
- Drag and drop to reorder within columns
- Drag and drop to move between columns
- Visual priority indicators (High, Medium, Low)

### Real-time Collaboration

- WebSocket connection for live updates
- Automatic reconnection on connection loss
- Optimistic updates for smooth UX
- See changes from other users in real-time

### Drag and Drop

- Fractional ordering system for smooth reordering
- Visual feedback during drag operations
- Touch-friendly for mobile devices
- Smart positioning between items

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_WS_URL` | WebSocket URL | `ws://localhost:8000` |

## License

MIT
