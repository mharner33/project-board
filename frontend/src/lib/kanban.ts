export type Card = {
  id: number;
  title: string;
  details: string;
  position: number;
};

export type Column = {
  id: number;
  title: string;
  position: number;
  cards: Card[];
};

export type BoardData = {
  id: number;
  name: string;
  columns: Column[];
};

export const dndId = (type: "col" | "card", id: number) => `${type}-${id}`;

export const parseDndId = (dndId: string): { type: "col" | "card"; id: number } | null => {
  const match = dndId.match(/^(col|card)-(\d+)$/);
  if (!match) return null;
  return { type: match[1] as "col" | "card", id: Number(match[2]) };
};

export const findCardColumn = (board: BoardData, cardId: number): Column | undefined =>
  board.columns.find((col) => col.cards.some((c) => c.id === cardId));

export const findCard = (board: BoardData, cardId: number): Card | undefined => {
  for (const col of board.columns) {
    const card = col.cards.find((c) => c.id === cardId);
    if (card) return card;
  }
  return undefined;
};
