# Frontend

Next.js 16 app with React 19, Tailwind CSS 4, and dnd-kit for drag-and-drop. Currently a standalone client-side demo with no backend integration.

## Stack

- Next.js 16.1.6, React 19.2.3, TypeScript 5
- Tailwind CSS 4 via `@tailwindcss/postcss`
- `@dnd-kit/core` 6.x + `@dnd-kit/sortable` 10.x for drag-and-drop
- `clsx` for conditional class merging
- Fonts: Space Grotesk (display), Manrope (body) via `next/font/google`

## Structure

```
src/
  app/
    layout.tsx      Root layout. Sets fonts and metadata ("Kanban Studio").
    page.tsx        Renders <KanbanBoard />.
    globals.css     CSS variables for the color scheme + Tailwind import.
  components/
    KanbanBoard.tsx     Top-level board. Owns all state (useState with BoardData).
                        Handles drag start/end, column rename, card add/delete.
    KanbanColumn.tsx    Single column. Droppable target, sortable context,
                        inline-editable title, "Add a card" button.
    KanbanCard.tsx      Draggable card with title, details, and Remove button.
    KanbanCardPreview.tsx   Static card used as the DragOverlay ghost.
    NewCardForm.tsx     Expand/collapse form for adding a card (title + details).
  lib/
    kanban.ts       Types (Card, Column, BoardData), initialData with 5 columns
                    and 8 sample cards, moveCard() logic, createId() helper.
```

## Data model (client-side only, for now)

- `BoardData`: `{ columns: Column[], cards: Record<string, Card> }`
- `Column`: `{ id, title, cardIds[] }`
- `Card`: `{ id, title, details }`
- All state lives in `KanbanBoard` via `useState`. No persistence.

## Testing

- **Unit tests** (Vitest + jsdom + Testing Library): `src/**/*.test.{ts,tsx}`
  - `kanban.test.ts` -- moveCard logic (reorder, cross-column, drop on column)
  - `KanbanBoard.test.tsx` -- renders 5 columns, rename column, add/remove card
- **E2E tests** (Playwright): `tests/kanban.spec.ts`
  - Board loads, add card, drag card between columns
  - Runs against `next dev` on port 3000

## Build

- `npm run dev` -- development server
- `npm run build` -- production build (will need `output: 'export'` added for static export)
- `npm run test` / `npm run test:unit` -- Vitest
- `npm run test:e2e` -- Playwright
