import { api } from "./client";
import type { RagSearchOut } from "./types";

export const ragApi = {
  search: (query: string, top_k = 5): Promise<RagSearchOut> =>
    api.post("/api/v1/rag/search", { query, top_k }).then((r) => r.data),

  index: (bookId: string) =>
    api.post("/api/v1/rag/index", { bookId }).then((r) => r.data),
};
