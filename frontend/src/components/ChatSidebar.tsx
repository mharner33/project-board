"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { sendChat, type ChatMessage } from "@/lib/api";
import type { BoardData } from "@/lib/kanban";

type ChatSidebarProps = {
  isOpen: boolean;
  onClose: () => void;
  onBoardUpdate: (board: BoardData) => void;
};

export const ChatSidebar = ({ isOpen, onClose, onBoardUpdate }: ChatSidebarProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    const history = [...messages];
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const res = await sendChat(text, history);
      const assistantMsg: ChatMessage = { role: "assistant", content: res.message };
      setMessages((prev) => [...prev, assistantMsg]);
      if (res.board_updates.length > 0) {
        onBoardUpdate(res.board);
      }
    } catch {
      const errorMsg: ChatMessage = {
        role: "assistant",
        content: "Sorry, something went wrong. Please try again.",
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div
      className={`fixed right-0 top-0 z-50 flex h-full w-[400px] max-w-[90vw] flex-col border-l border-[var(--stroke)] bg-white shadow-[-8px_0_30px_rgba(3,33,71,0.1)] transition-transform duration-300 ${
        isOpen ? "translate-x-0" : "translate-x-full"
      }`}
      data-testid="chat-sidebar"
    >
      <div className="flex items-center justify-between border-b border-[var(--stroke)] px-5 py-4">
        <div>
          <h2 className="font-display text-lg font-semibold text-[var(--navy-dark)]">
            AI Assistant
          </h2>
          <p className="mt-0.5 text-xs text-[var(--gray-text)]">
            Ask me to manage your board
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-full border border-[var(--stroke)] px-3 py-1.5 text-xs font-semibold text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
          aria-label="Close chat"
        >
          Close
        </button>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 py-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
            <div className="h-10 w-10 rounded-full bg-[var(--secondary-purple)] opacity-20" />
            <p className="text-sm leading-6 text-[var(--gray-text)]">
              Ask me to create, move, update, or delete cards on your board.
            </p>
          </div>
        )}
        <div className="flex flex-col gap-3">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                msg.role === "user"
                  ? "ml-auto bg-[var(--secondary-purple)] text-white"
                  : "mr-auto bg-[var(--surface)] text-[var(--navy-dark)]"
              }`}
            >
              {msg.content}
            </div>
          ))}
          {sending && (
            <div className="mr-auto max-w-[85%] rounded-2xl bg-[var(--surface)] px-4 py-3 text-sm text-[var(--gray-text)]">
              Thinking...
            </div>
          )}
        </div>
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex gap-2 border-t border-[var(--stroke)] px-5 py-4"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask the AI..."
          disabled={sending}
          className="flex-1 rounded-xl border border-[var(--stroke)] bg-white px-4 py-3 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)] disabled:opacity-50"
          aria-label="Chat message"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="rounded-xl bg-[var(--secondary-purple)] px-4 py-3 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
};
