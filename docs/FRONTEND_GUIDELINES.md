# FRONTEND_GUIDELINES.md - Frontend Design System
## Agent Rangers: UI/UX Standards and Component Guidelines

**Version:** 1.0  
**Last Updated:** 2026-02-03

---

## 1. Design Philosophy

### 1.1 Core Principles

1. **Clarity First** - Every UI element has a clear purpose
2. **Instant Feedback** - Optimistic updates, no spinners for common actions
3. **Keyboard Accessible** - All actions reachable via keyboard
4. **Mobile Responsive** - Works on all screen sizes
5. **Dark Mode Ready** - Design with both themes in mind

### 1.2 Visual Style

- Clean, minimal interface
- Subtle shadows for depth
- Rounded corners for friendliness
- Consistent spacing throughout
- Professional but approachable

---

## 2. Color Palette

### 2.1 Base Colors (Light Mode)

| Name | Variable | Hex | Usage |
|------|----------|-----|-------|
| Background | `--background` | `#FFFFFF` | Page background |
| Foreground | `--foreground` | `#0A0A0A` | Primary text |
| Card | `--card` | `#FFFFFF` | Card backgrounds |
| Card Foreground | `--card-foreground` | `#0A0A0A` | Card text |
| Popover | `--popover` | `#FFFFFF` | Dropdown backgrounds |
| Popover Foreground | `--popover-foreground` | `#0A0A0A` | Dropdown text |

### 2.2 Semantic Colors

| Name | Variable | Hex | Usage |
|------|----------|-----|-------|
| Primary | `--primary` | `#18181B` | Primary buttons, links |
| Primary Foreground | `--primary-foreground` | `#FAFAFA` | Text on primary |
| Secondary | `--secondary` | `#F4F4F5` | Secondary buttons |
| Secondary Foreground | `--secondary-foreground` | `#18181B` | Text on secondary |
| Muted | `--muted` | `#F4F4F5` | Muted backgrounds |
| Muted Foreground | `--muted-foreground` | `#71717A` | Muted text, placeholders |
| Accent | `--accent` | `#F4F4F5` | Hover states |
| Accent Foreground | `--accent-foreground` | `#18181B` | Text on accent |

### 2.3 State Colors

| Name | Variable | Hex | Usage |
|------|----------|-----|-------|
| Destructive | `--destructive` | `#EF4444` | Delete, errors |
| Destructive Foreground | `--destructive-foreground` | `#FAFAFA` | Text on destructive |
| Border | `--border` | `#E4E4E7` | Borders, dividers |
| Input | `--input` | `#E4E4E7` | Input borders |
| Ring | `--ring` | `#18181B` | Focus rings |

### 2.4 Priority Badge Colors

| Priority | Background | Text | Border |
|----------|------------|------|--------|
| Urgent | `#FEE2E2` | `#991B1B` | `#FECACA` |
| High | `#FEF3C7` | `#92400E` | `#FDE68A` |
| Medium | `#DBEAFE` | `#1E40AF` | `#BFDBFE` |
| Low | `#F3F4F6` | `#374151` | `#E5E7EB` |

### 2.5 Agent Status Colors (Phase 3)

| Status | Color | Hex |
|--------|-------|-----|
| Architect | Indigo | `#6366F1` |
| Developer | Green | `#22C55E` |
| Reviewer | Amber | `#F59E0B` |
| Coordinator | Pink | `#EC4899` |

### 2.6 CSS Variables (index.css)

```css
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 0 0% 3.9%;
    --card: 0 0% 100%;
    --card-foreground: 0 0% 3.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 0 0% 3.9%;
    --primary: 0 0% 9%;
    --primary-foreground: 0 0% 98%;
    --secondary: 0 0% 96.1%;
    --secondary-foreground: 0 0% 9%;
    --muted: 0 0% 96.1%;
    --muted-foreground: 0 0% 45.1%;
    --accent: 0 0% 96.1%;
    --accent-foreground: 0 0% 9%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 0 0% 98%;
    --border: 0 0% 89.8%;
    --input: 0 0% 89.8%;
    --ring: 0 0% 3.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 0 0% 3.9%;
    --foreground: 0 0% 98%;
    --card: 0 0% 3.9%;
    --card-foreground: 0 0% 98%;
    --popover: 0 0% 3.9%;
    --popover-foreground: 0 0% 98%;
    --primary: 0 0% 98%;
    --primary-foreground: 0 0% 9%;
    --secondary: 0 0% 14.9%;
    --secondary-foreground: 0 0% 98%;
    --muted: 0 0% 14.9%;
    --muted-foreground: 0 0% 63.9%;
    --accent: 0 0% 14.9%;
    --accent-foreground: 0 0% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 0 0% 98%;
    --border: 0 0% 14.9%;
    --input: 0 0% 14.9%;
    --ring: 0 0% 83.1%;
  }
}
```

---

## 3. Typography

### 3.1 Font Stack

```css
font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 
             "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", 
             sans-serif, "Apple Color Emoji", "Segoe UI Emoji", 
             "Segoe UI Symbol", "Noto Color Emoji";
```

### 3.2 Font Sizes

| Name | Class | Size | Line Height | Usage |
|------|-------|------|-------------|-------|
| xs | `text-xs` | 12px | 16px | Badges, captions |
| sm | `text-sm` | 14px | 20px | Secondary text, labels |
| base | `text-base` | 16px | 24px | Body text |
| lg | `text-lg` | 18px | 28px | Subheadings |
| xl | `text-xl` | 20px | 28px | Card titles |
| 2xl | `text-2xl` | 24px | 32px | Page titles |
| 3xl | `text-3xl` | 30px | 36px | Hero text |

### 3.3 Font Weights

| Name | Class | Weight | Usage |
|------|-------|--------|-------|
| Normal | `font-normal` | 400 | Body text |
| Medium | `font-medium` | 500 | Labels, emphasis |
| Semibold | `font-semibold` | 600 | Subheadings |
| Bold | `font-bold` | 700 | Headings |

### 3.4 Text Colors

| Name | Class | Usage |
|------|-------|-------|
| Primary | `text-foreground` | Main content |
| Muted | `text-muted-foreground` | Secondary content |
| Destructive | `text-destructive` | Error messages |

---

## 4. Spacing Scale

### 4.1 Spacing Values

| Name | Class | Value | Usage |
|------|-------|-------|-------|
| 0 | `p-0`, `m-0` | 0 | Reset |
| 1 | `p-1`, `m-1` | 4px | Tight spacing |
| 2 | `p-2`, `m-2` | 8px | Component padding |
| 3 | `p-3`, `m-3` | 12px | Small gaps |
| 4 | `p-4`, `m-4` | 16px | Standard padding |
| 5 | `p-5`, `m-5` | 20px | Medium padding |
| 6 | `p-6`, `m-6` | 24px | Section padding |
| 8 | `p-8`, `m-8` | 32px | Large padding |
| 10 | `p-10`, `m-10` | 40px | Extra large |
| 12 | `p-12`, `m-12` | 48px | Hero sections |

### 4.2 Gap Values

| Class | Value | Usage |
|-------|-------|-------|
| `gap-1` | 4px | Tight items |
| `gap-2` | 8px | Icon + text |
| `gap-3` | 12px | Form fields |
| `gap-4` | 16px | Card content |
| `gap-6` | 24px | Section gaps |

---

## 5. Layout

### 5.1 Container

```html
<div class="container mx-auto px-6">
  <!-- Content -->
</div>
```

- Max width: `max-w-7xl` (1280px)
- Horizontal padding: `px-6` (24px)
- Centered: `mx-auto`

### 5.2 Grid System

**Board Cards Grid:**
```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <!-- Cards -->
</div>
```

**Kanban Columns:**
```html
<div class="flex gap-4 overflow-x-auto p-6">
  <!-- Columns -->
</div>
```

### 5.3 Breakpoints

| Name | Min Width | Usage |
|------|-----------|-------|
| sm | 640px | Mobile landscape |
| md | 768px | Tablet |
| lg | 1024px | Desktop |
| xl | 1280px | Large desktop |
| 2xl | 1536px | Extra large |

### 5.4 Z-Index Scale

| Value | Usage |
|-------|-------|
| 0 | Base content |
| 10 | Floating elements |
| 20 | Dropdowns |
| 30 | Tooltips |
| 40 | Modals backdrop |
| 50 | Modals |
| 60 | Drag overlay |

---

## 6. Components

### 6.1 Button

**Variants:**
```tsx
// Primary (default)
<Button>Create Board</Button>

// Secondary
<Button variant="secondary">Cancel</Button>

// Outline
<Button variant="outline">Back</Button>

// Ghost
<Button variant="ghost" size="icon">
  <MoreVertical className="h-4 w-4" />
</Button>

// Destructive
<Button variant="destructive">Delete</Button>
```

**Sizes:**
```tsx
// Default
<Button>Default</Button>

// Small
<Button size="sm">Small</Button>

// Large
<Button size="lg">Large</Button>

// Icon only
<Button size="icon"><Plus /></Button>
```

**With Icon:**
```tsx
<Button>
  <Plus className="mr-2 h-4 w-4" />
  New Board
</Button>
```

### 6.2 Card

```tsx
<Card>
  <CardHeader>
    <CardTitle>Board Name</CardTitle>
    <CardDescription>Optional description</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Content */}
  </CardContent>
</Card>
```

**Interactive Card:**
```tsx
<Card className="hover:shadow-lg transition-shadow cursor-pointer">
  {/* Content */}
</Card>
```

### 6.3 Dialog

```tsx
<Dialog open={open} onOpenChange={setOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Create Board</DialogTitle>
      <DialogDescription>
        Create a new board to organize your tasks.
      </DialogDescription>
    </DialogHeader>
    {/* Form content */}
    <DialogFooter>
      <Button variant="outline" onClick={() => setOpen(false)}>
        Cancel
      </Button>
      <Button onClick={handleSubmit}>Create</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### 6.4 Input

```tsx
<div className="space-y-2">
  <Label htmlFor="name">Name</Label>
  <Input
    id="name"
    placeholder="Enter name"
    value={value}
    onChange={(e) => setValue(e.target.value)}
  />
</div>
```

### 6.5 Dropdown Menu

```tsx
<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="ghost" size="icon">
      <MoreVertical className="h-4 w-4" />
    </Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent align="end">
    <DropdownMenuItem onClick={handleEdit}>
      <Pencil className="mr-2 h-4 w-4" />
      Edit
    </DropdownMenuItem>
    <DropdownMenuItem onClick={handleDelete} className="text-destructive">
      <Trash2 className="mr-2 h-4 w-4" />
      Delete
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

### 6.6 Badge

```tsx
// Priority badges
<Badge variant="outline" className="bg-red-100 text-red-800 border-red-200">
  Urgent
</Badge>
<Badge variant="outline" className="bg-yellow-100 text-yellow-800 border-yellow-200">
  High
</Badge>
<Badge variant="outline" className="bg-blue-100 text-blue-800 border-blue-200">
  Medium
</Badge>
<Badge variant="outline" className="bg-gray-100 text-gray-800 border-gray-200">
  Low
</Badge>
```

### 6.7 Skeleton

```tsx
// Text skeleton
<Skeleton className="h-4 w-32" />

// Card skeleton
<Card>
  <CardHeader>
    <Skeleton className="h-6 w-3/4" />
    <Skeleton className="h-4 w-full" />
  </CardHeader>
</Card>
```

---

## 7. Kanban-Specific Components

### 7.1 Column

```tsx
<div className="w-80 flex-shrink-0 bg-muted/30 rounded-lg">
  <div className="p-4 border-b">
    <h3 className="font-semibold">{column.name}</h3>
    <span className="text-sm text-muted-foreground">
      {tasks.length} tasks
    </span>
  </div>
  <div className="p-2 space-y-2 min-h-[200px]">
    {/* Task cards */}
  </div>
  <div className="p-2 border-t">
    <Button variant="ghost" className="w-full justify-start">
      <Plus className="mr-2 h-4 w-4" />
      Add Task
    </Button>
  </div>
</div>
```

### 7.2 Task Card

```tsx
<Card className="cursor-grab active:cursor-grabbing">
  <CardHeader className="p-3">
    <div className="flex items-start justify-between gap-2">
      <CardTitle className="text-sm font-medium leading-tight">
        {task.title}
      </CardTitle>
      <DropdownMenu>
        {/* Menu */}
      </DropdownMenu>
    </div>
    {task.priority && (
      <Badge>{task.priority}</Badge>
    )}
  </CardHeader>
</Card>
```

### 7.3 Drag Overlay

```tsx
<DragOverlay>
  {activeTask && (
    <Card className="shadow-lg rotate-3 opacity-90">
      <CardHeader className="p-3">
        <CardTitle className="text-sm">
          {activeTask.title}
        </CardTitle>
      </CardHeader>
    </Card>
  )}
</DragOverlay>
```

---

## 8. Animations & Transitions

### 8.1 Standard Transitions

```css
/* Shadow transition for cards */
.transition-shadow {
  transition-property: box-shadow;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

/* All transitions */
.transition-all {
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}
```

### 8.2 Hover States

```tsx
// Card hover
<Card className="hover:shadow-lg transition-shadow" />

// Button hover (built-in)
<Button /> // Includes hover states

// Interactive element
<div className="hover:bg-accent transition-colors" />
```

### 8.3 Drag Animation

```tsx
// dnd-kit provides built-in animations
// Configure in SortableContext
<SortableContext
  items={taskIds}
  strategy={verticalListSortingStrategy}
>
  {/* Items */}
</SortableContext>
```

---

## 9. Icons

### 9.1 Icon Library

Using **Lucide React** (`lucide-react`)

### 9.2 Common Icons

| Icon | Component | Usage |
|------|-----------|-------|
| Plus | `<Plus />` | Add actions |
| Trash2 | `<Trash2 />` | Delete actions |
| Pencil | `<Pencil />` | Edit actions |
| MoreVertical | `<MoreVertical />` | Menu trigger |
| ArrowLeft | `<ArrowLeft />` | Back navigation |
| LayoutDashboard | `<LayoutDashboard />` | Board icon |
| Columns | `<Columns />` | Column icon |
| ListTodo | `<ListTodo />` | Task icon |
| GripVertical | `<GripVertical />` | Drag handle |
| X | `<X />` | Close/dismiss |

### 9.3 Icon Sizing

```tsx
// In buttons (with text)
<Plus className="mr-2 h-4 w-4" />

// Icon-only buttons
<Button size="icon">
  <MoreVertical className="h-4 w-4" />
</Button>

// Large display icons
<LayoutDashboard className="h-12 w-12" />

// Header icons
<LayoutDashboard className="h-8 w-8 text-primary" />
```

---

## 10. Accessibility

### 10.1 Focus States

All interactive elements must have visible focus rings:
```css
/* Built into components via ring class */
.focus-visible:ring-2
.focus-visible:ring-ring
.focus-visible:ring-offset-2
```

### 10.2 ARIA Labels

```tsx
// Icon buttons need labels
<Button size="icon" aria-label="Open menu">
  <MoreVertical className="h-4 w-4" />
</Button>

// Dialogs
<Dialog>
  <DialogContent aria-describedby="dialog-description">
    <DialogTitle>Title</DialogTitle>
    <DialogDescription id="dialog-description">
      Description
    </DialogDescription>
  </DialogContent>
</Dialog>
```

### 10.3 Keyboard Navigation

| Key | Action |
|-----|--------|
| Tab | Move focus forward |
| Shift+Tab | Move focus backward |
| Enter/Space | Activate button/link |
| Escape | Close modal/dropdown |
| Arrow keys | Navigate within menus |

---

## 11. Responsive Design

### 11.1 Mobile First

```tsx
// Stack on mobile, grid on larger screens
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
```

### 11.2 Touch Targets

Minimum touch target size: 44x44px

```tsx
// Buttons have sufficient size by default
<Button size="icon" className="h-10 w-10">
```

### 11.3 Mobile Kanban

On mobile (< 768px):
- Columns stack vertically or horizontal scroll
- Touch-friendly drag handles
- Larger touch targets for cards

---

## 12. Error States

### 12.1 Form Validation

```tsx
<div className="space-y-2">
  <Label htmlFor="name" className={error ? "text-destructive" : ""}>
    Name
  </Label>
  <Input
    id="name"
    className={error ? "border-destructive" : ""}
  />
  {error && (
    <p className="text-sm text-destructive">{error}</p>
  )}
</div>
```

### 12.2 Error Cards

```tsx
<Card className="border-destructive">
  <CardHeader>
    <CardTitle className="text-destructive">Error</CardTitle>
    <CardDescription className="text-destructive">
      {errorMessage}
    </CardDescription>
  </CardHeader>
  <CardContent>
    <Button onClick={handleRetry}>Retry</Button>
  </CardContent>
</Card>
```

---

## 13. File Structure

```
frontend/src/
├── components/
│   ├── ui/              # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── input.tsx
│   │   ├── label.tsx
│   │   ├── badge.tsx
│   │   ├── skeleton.tsx
│   │   └── slot.tsx
│   ├── Board.tsx        # Main kanban board
│   ├── Column.tsx       # Kanban column
│   ├── TaskCard.tsx     # Task card
│   ├── CreateBoardDialog.tsx
│   ├── CreateColumnDialog.tsx
│   └── CreateTaskDialog.tsx
├── lib/
│   └── utils.ts         # cn() utility
└── index.css            # Global styles + CSS variables
```

---

*Document Owner: Agent Rangers Team*  
*Review Cycle: Each design update*
