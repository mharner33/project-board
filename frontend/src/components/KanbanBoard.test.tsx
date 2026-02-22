import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import type { BoardData } from "@/lib/kanban";

const mockBoard: BoardData = {
  id: 1,
  name: "My Board",
  columns: [
    {
      id: 1, title: "Backlog", position: 0,
      cards: [
        { id: 1, title: "Card A", details: "Details A", position: 0 },
        { id: 2, title: "Card B", details: "Details B", position: 1 },
      ],
    },
    { id: 2, title: "Discovery", position: 1, cards: [] },
    { id: 3, title: "In Progress", position: 2, cards: [] },
    { id: 4, title: "Review", position: 3, cards: [] },
    { id: 5, title: "Done", position: 4, cards: [] },
  ],
};

vi.mock("@/components/AuthProvider", () => ({
  useAuth: () => ({
    status: "authenticated",
    username: "user",
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

const mockFetchBoard = vi.fn<() => Promise<BoardData>>();
const mockRenameColumn = vi.fn<() => Promise<BoardData>>();
const mockCreateCard = vi.fn<() => Promise<BoardData>>();
const mockDeleteCard = vi.fn<() => Promise<BoardData>>();

vi.mock("@/lib/api", () => ({
  fetchBoard: (...args: unknown[]) => mockFetchBoard(...args),
  renameColumn: (...args: unknown[]) => mockRenameColumn(...args),
  createCard: (...args: unknown[]) => mockCreateCard(...args),
  deleteCard: (...args: unknown[]) => mockDeleteCard(...args),
  moveCard: vi.fn().mockResolvedValue({}),
  sendChat: vi.fn().mockResolvedValue({ message: "", board_updates: [], board: {} }),
}));

const getFirstColumn = () => screen.getAllByTestId(/^column-/)[0];

describe("KanbanBoard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchBoard.mockResolvedValue(structuredClone(mockBoard));
  });

  it("shows loading then renders columns", async () => {
    render(<KanbanBoard />);
    expect(screen.getByText("Loading board...")).toBeInTheDocument();
    await waitFor(() => expect(screen.getAllByTestId(/^column-/)).toHaveLength(5));
  });

  it("shows signed-in username and sign out button", async () => {
    render(<KanbanBoard />);
    await waitFor(() => expect(screen.getByText("user")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /sign out/i })).toBeInTheDocument();
  });

  it("renames a column (optimistic update)", async () => {
    mockRenameColumn.mockResolvedValue(structuredClone(mockBoard));
    render(<KanbanBoard />);
    await waitFor(() => expect(screen.getAllByTestId(/^column-/)).toHaveLength(5));
    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "Todo");
    expect(input).toHaveValue("Todo");
  });

  it("adds a card via API", async () => {
    const boardWithNewCard = structuredClone(mockBoard);
    boardWithNewCard.columns[0].cards.push({ id: 99, title: "New card", details: "Notes", position: 2 });
    mockCreateCard.mockResolvedValue(boardWithNewCard);

    render(<KanbanBoard />);
    await waitFor(() => expect(screen.getAllByTestId(/^column-/)).toHaveLength(5));
    const column = getFirstColumn();
    await userEvent.click(within(column).getByRole("button", { name: /add a card/i }));
    await userEvent.type(within(column).getByPlaceholderText(/card title/i), "New card");
    await userEvent.type(within(column).getByPlaceholderText(/details/i), "Notes");
    await userEvent.click(within(column).getByRole("button", { name: /^add card$/i }));

    expect(mockCreateCard).toHaveBeenCalledWith(1, "New card", "Notes");
    await waitFor(() => expect(within(column).getByText("New card")).toBeInTheDocument());
  });

  it("shows AI Chat button that opens sidebar", async () => {
    render(<KanbanBoard />);
    await waitFor(() => expect(screen.getAllByTestId(/^column-/)).toHaveLength(5));
    const chatBtn = screen.getByRole("button", { name: /ai chat/i });
    expect(chatBtn).toBeInTheDocument();
    await userEvent.click(chatBtn);
    expect(screen.getByTestId("chat-sidebar")).toBeInTheDocument();
  });

  it("deletes a card via API", async () => {
    const boardWithoutCard = structuredClone(mockBoard);
    boardWithoutCard.columns[0].cards.shift();
    mockDeleteCard.mockResolvedValue(boardWithoutCard);

    render(<KanbanBoard />);
    await waitFor(() => expect(screen.getByText("Card A")).toBeInTheDocument());
    const deleteBtn = screen.getByRole("button", { name: /delete card a/i });
    await userEvent.click(deleteBtn);

    expect(mockDeleteCard).toHaveBeenCalledWith(1);
    await waitFor(() => expect(screen.queryByText("Card A")).not.toBeInTheDocument());
  });
});
