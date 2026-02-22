import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatSidebar } from "@/components/ChatSidebar";
import type { BoardData } from "@/lib/kanban";

const mockSendChat = vi.fn();

vi.mock("@/lib/api", () => ({
  sendChat: (...args: unknown[]) => mockSendChat(...args),
}));

const mockBoard: BoardData = {
  id: 1,
  name: "Board",
  columns: [{ id: 1, title: "Backlog", position: 0, cards: [] }],
};

describe("ChatSidebar", () => {
  const onClose = vi.fn();
  const onBoardUpdate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders when open", () => {
    render(<ChatSidebar isOpen={true} onClose={onClose} onBoardUpdate={onBoardUpdate} />);
    expect(screen.getByText("AI Assistant")).toBeInTheDocument();
    expect(screen.getByLabelText("Chat message")).toBeInTheDocument();
  });

  it("has translate-x-full class when closed", () => {
    render(<ChatSidebar isOpen={false} onClose={onClose} onBoardUpdate={onBoardUpdate} />);
    const sidebar = screen.getByTestId("chat-sidebar");
    expect(sidebar.className).toContain("translate-x-full");
  });

  it("calls onClose when Close button clicked", async () => {
    render(<ChatSidebar isOpen={true} onClose={onClose} onBoardUpdate={onBoardUpdate} />);
    await userEvent.click(screen.getByRole("button", { name: /close chat/i }));
    expect(onClose).toHaveBeenCalled();
  });

  it("sends a message and displays response", async () => {
    mockSendChat.mockResolvedValue({
      message: "Done! I created a card.",
      board_updates: [{ action: "create", column_id: 1, title: "New", details: "" }],
      board: mockBoard,
    });

    render(<ChatSidebar isOpen={true} onClose={onClose} onBoardUpdate={onBoardUpdate} />);
    const input = screen.getByLabelText("Chat message");
    await userEvent.type(input, "Create a card");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(screen.getByText("Create a card")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Done! I created a card.")).toBeInTheDocument());
    expect(mockSendChat).toHaveBeenCalledWith("Create a card", []);
    expect(onBoardUpdate).toHaveBeenCalledWith(mockBoard);
  });

  it("passes conversation history to sendChat", async () => {
    mockSendChat
      .mockResolvedValueOnce({ message: "First reply", board_updates: [], board: mockBoard })
      .mockResolvedValueOnce({ message: "Second reply", board_updates: [], board: mockBoard });

    render(<ChatSidebar isOpen={true} onClose={onClose} onBoardUpdate={onBoardUpdate} />);
    const input = screen.getByLabelText("Chat message");

    await userEvent.type(input, "Hello");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));
    await waitFor(() => expect(screen.getByText("First reply")).toBeInTheDocument());

    await userEvent.type(input, "Follow up");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));
    await waitFor(() => expect(screen.getByText("Second reply")).toBeInTheDocument());

    expect(mockSendChat).toHaveBeenLastCalledWith("Follow up", [
      { role: "user", content: "Hello" },
      { role: "assistant", content: "First reply" },
    ]);
  });

  it("does not call onBoardUpdate when no board_updates", async () => {
    mockSendChat.mockResolvedValue({ message: "Just chatting", board_updates: [], board: mockBoard });

    render(<ChatSidebar isOpen={true} onClose={onClose} onBoardUpdate={onBoardUpdate} />);
    await userEvent.type(screen.getByLabelText("Chat message"), "Hi");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => expect(screen.getByText("Just chatting")).toBeInTheDocument());
    expect(onBoardUpdate).not.toHaveBeenCalled();
  });

  it("shows error message on failure", async () => {
    mockSendChat.mockRejectedValue(new Error("Network error"));

    render(<ChatSidebar isOpen={true} onClose={onClose} onBoardUpdate={onBoardUpdate} />);
    await userEvent.type(screen.getByLabelText("Chat message"), "Fail");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() =>
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
    );
  });

  it("disables send button when input is empty", () => {
    render(<ChatSidebar isOpen={true} onClose={onClose} onBoardUpdate={onBoardUpdate} />);
    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
  });

  it("shows thinking indicator while sending", async () => {
    let resolve: (v: unknown) => void;
    mockSendChat.mockReturnValue(new Promise((r) => { resolve = r; }));

    render(<ChatSidebar isOpen={true} onClose={onClose} onBoardUpdate={onBoardUpdate} />);
    await userEvent.type(screen.getByLabelText("Chat message"), "Test");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(screen.getByText("Thinking...")).toBeInTheDocument();

    resolve!({ message: "OK", board_updates: [], board: mockBoard });
    await waitFor(() => expect(screen.queryByText("Thinking...")).not.toBeInTheDocument());
  });
});
