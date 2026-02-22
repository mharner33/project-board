"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { ChatSidebar } from "@/components/ChatSidebar";
import { useAuth } from "@/components/AuthProvider";
import { dndId, findCard, findCardColumn, parseDndId, type BoardData } from "@/lib/kanban";
import * as api from "@/lib/api";

export const KanbanBoard = () => {
  const { logout, username } = useAuth() as { logout: () => void; username: string };
  const [board, setBoard] = useState<BoardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeCardId, setActiveCardId] = useState<number | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const renameTimers = useRef<Map<number, ReturnType<typeof setTimeout>>>(new Map());

  useEffect(() => {
    api.fetchBoard().then(setBoard).catch(console.error).finally(() => setLoading(false));
  }, []);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } })
  );

  const handleDragStart = (event: DragStartEvent) => {
    const parsed = parseDndId(event.active.id as string);
    if (parsed?.type === "card") setActiveCardId(parsed.id);
  };

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      setActiveCardId(null);
      if (!board) return;
      const { active, over } = event;
      if (!over || active.id === over.id) return;

      const activeParsed = parseDndId(active.id as string);
      const overParsed = parseDndId(over.id as string);
      if (!activeParsed || activeParsed.type !== "card" || !overParsed) return;

      const cardId = activeParsed.id;
      let targetColId: number;
      let targetPos: number;

      if (overParsed.type === "col") {
        targetColId = overParsed.id;
        const col = board.columns.find((c) => c.id === targetColId);
        targetPos = col ? col.cards.length : 0;
      } else {
        const targetCol = findCardColumn(board, overParsed.id);
        if (!targetCol) return;
        targetColId = targetCol.id;
        targetPos = targetCol.cards.findIndex((c) => c.id === overParsed.id);
        if (targetPos === -1) targetPos = targetCol.cards.length;
      }

      // Optimistic: move card in local state
      setBoard((prev) => {
        if (!prev) return prev;
        const card = findCard(prev, cardId);
        if (!card) return prev;
        const columns = prev.columns.map((col) => ({
          ...col,
          cards: col.cards.filter((c) => c.id !== cardId),
        }));
        const targetColumn = columns.find((c) => c.id === targetColId);
        if (targetColumn) {
          targetColumn.cards.splice(targetPos, 0, { ...card, position: targetPos });
          targetColumn.cards.forEach((c, i) => (c.position = i));
        }
        return { ...prev, columns };
      });

      api.moveCard(cardId, targetColId, targetPos).then(setBoard).catch(console.error);
    },
    [board]
  );

  const handleRenameColumn = useCallback((columnId: number, title: string) => {
    setBoard((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        columns: prev.columns.map((col) =>
          col.id === columnId ? { ...col, title } : col
        ),
      };
    });

    const existing = renameTimers.current.get(columnId);
    if (existing) clearTimeout(existing);
    renameTimers.current.set(
      columnId,
      setTimeout(() => {
        api.renameColumn(columnId, title).catch(console.error);
        renameTimers.current.delete(columnId);
      }, 500)
    );
  }, []);

  const handleAddCard = useCallback((columnId: number, title: string, details: string) => {
    api.createCard(columnId, title, details || "").then(setBoard).catch(console.error);
  }, []);

  const handleDeleteCard = useCallback((_columnId: number, cardId: number) => {
    api.deleteCard(cardId).then(setBoard).catch(console.error);
  }, []);

  if (loading || !board) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
          Loading board...
        </p>
      </div>
    );
  }

  const activeCard = activeCardId ? findCard(board, activeCardId) : null;

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="flex items-start gap-4">
              <button
                type="button"
                onClick={() => setChatOpen(true)}
                className="rounded-xl bg-[var(--secondary-purple)] px-5 py-3 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
              >
                AI Chat
              </button>
              <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                  Signed in as
                </p>
                <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                  {username}
                </p>
              </div>
              <button
                type="button"
                onClick={logout}
                className="rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
              >
                Sign out
              </button>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
        </header>

        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <section className="grid gap-6 lg:grid-cols-5">
            {board.columns.map((column) => (
              <KanbanColumn
                key={column.id}
                column={column}
                onRename={handleRenameColumn}
                onAddCard={handleAddCard}
                onDeleteCard={handleDeleteCard}
              />
            ))}
          </section>
          <DragOverlay>
            {activeCard ? (
              <div className="w-[260px]">
                <KanbanCardPreview card={activeCard} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </main>

      <ChatSidebar
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
        onBoardUpdate={setBoard}
      />
    </div>
  );
};
