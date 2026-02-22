import { dndId, parseDndId, findCard, findCardColumn, type BoardData } from "@/lib/kanban";

const testBoard: BoardData = {
  id: 1,
  name: "Test",
  columns: [
    {
      id: 10,
      title: "A",
      position: 0,
      cards: [
        { id: 100, title: "Card 1", details: "", position: 0 },
        { id: 101, title: "Card 2", details: "", position: 1 },
      ],
    },
    {
      id: 11,
      title: "B",
      position: 1,
      cards: [{ id: 102, title: "Card 3", details: "", position: 0 }],
    },
  ],
};

describe("dndId", () => {
  it("creates prefixed IDs", () => {
    expect(dndId("col", 5)).toBe("col-5");
    expect(dndId("card", 42)).toBe("card-42");
  });
});

describe("parseDndId", () => {
  it("parses valid IDs", () => {
    expect(parseDndId("col-5")).toEqual({ type: "col", id: 5 });
    expect(parseDndId("card-42")).toEqual({ type: "card", id: 42 });
  });

  it("returns null for invalid IDs", () => {
    expect(parseDndId("invalid")).toBeNull();
    expect(parseDndId("col-abc")).toBeNull();
  });
});

describe("findCard", () => {
  it("finds a card across columns", () => {
    expect(findCard(testBoard, 102)?.title).toBe("Card 3");
  });

  it("returns undefined for missing card", () => {
    expect(findCard(testBoard, 999)).toBeUndefined();
  });
});

describe("findCardColumn", () => {
  it("finds the column containing a card", () => {
    expect(findCardColumn(testBoard, 100)?.id).toBe(10);
    expect(findCardColumn(testBoard, 102)?.id).toBe(11);
  });

  it("returns undefined for missing card", () => {
    expect(findCardColumn(testBoard, 999)).toBeUndefined();
  });
});
