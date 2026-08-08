import type {
  AskResponse,
  ChatConversation,
  ChatConversationDetail,
  Collection,
  CollectionNoteSummary,
  DocumentFile,
  RagSource,
  SearchFilters,
  SemanticResult,
} from "../types/atlas";

const API_BASE = import.meta.env.VITE_ATLAS_API_BASE ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: init?.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...init,
  });

  if (!response.ok) {
    const fallback = `Atlas request failed with ${response.status}`;
    try {
      const payload = await response.json();
      throw new Error(payload.detail ?? fallback);
    } catch (error) {
      if (error instanceof Error && error.message !== fallback) throw error;
      throw new Error(fallback);
    }
  }

  return response.json() as Promise<T>;
}

export function getDocuments() {
  return request<DocumentFile[]>("/documents");
}

export function askAtlas(question: string, filters?: SearchFilters) {
  return request<AskResponse>("/ai/ask", {
    method: "POST",
    body: JSON.stringify({
      question,
      scope: filters?.scope ?? "all",
      file_type: filters?.fileType ?? null,
      since: filters?.since ?? "all",
    }),
  });
}

export async function semanticSearch(query: string, topK = 6, filters?: SearchFilters) {
  const payload = await request<{ results: SemanticResult[] }>("/search/semantic", {
    method: "POST",
    body: JSON.stringify({
      query,
      top_k: topK,
      scope: filters?.scope ?? "all",
      file_type: filters?.fileType ?? null,
      since: filters?.since ?? "all",
    }),
  });
  return payload.results;
}

export function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return request<{ status: string; document: DocumentFile }>("/documents", {
    method: "POST",
    body: formData,
  });
}

// --- Collections ---

export function getCollections() {
  return request<Collection[]>("/collections");
}

export function createCollection(name: string, description?: string) {
  return request<{ status: string; collection: Collection }>("/collections", {
    method: "POST",
    body: JSON.stringify({ name, description: description ?? null }),
  });
}

export function deleteCollection(collectionId: number) {
  return request<{ status: string; message: string }>(`/collections/${collectionId}`, {
    method: "DELETE",
  });
}

export function getCollectionNotes(collectionId: number) {
  return request<CollectionNoteSummary[]>(`/collections/${collectionId}/notes`);
}

// --- Chat / conversations ---

export function getConversations() {
  return request<ChatConversation[]>("/conversations");
}

export function createConversation(title?: string) {
  return request<ChatConversation>("/conversations", {
    method: "POST",
    body: JSON.stringify({ title: title ?? null }),
  });
}

export function getConversation(conversationId: number) {
  return request<ChatConversationDetail>(`/conversations/${conversationId}`);
}

export function deleteConversation(conversationId: number) {
  return request<{ status: string; message: string }>(`/conversations/${conversationId}`, {
    method: "DELETE",
  });
}

type StreamChatHandlers = {
  onMeta?: (conversationId: number) => void;
  onToken: (text: string) => void;
  onDone?: (sources: RagSource[], conversationId: number) => void;
  onError?: (detail: string) => void;
};

/**
 * Sends a question to /ai/chat and reads the server-sent-events response
 * as it streams in, invoking the matching handler for each event type.
 */
export async function streamChatMessage(
  params: { conversationId: number | null; question: string; filters?: SearchFilters },
  handlers: StreamChatHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/ai/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      conversation_id: params.conversationId,
      question: params.question,
      scope: params.filters?.scope ?? "all",
      file_type: params.filters?.fileType ?? null,
      since: params.filters?.since ?? "all",
    }),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Atlas chat request failed with ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const rawEvent = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);

      let eventName = "message";
      let dataLine = "";
      for (const line of rawEvent.split("\n")) {
        if (line.startsWith("event:")) eventName = line.slice(6).trim();
        if (line.startsWith("data:")) dataLine = line.slice(5).trim();
      }

      if (dataLine) {
        try {
          const payload = JSON.parse(dataLine);
          if (eventName === "meta") handlers.onMeta?.(payload.conversation_id);
          if (eventName === "token") handlers.onToken(payload.text);
          if (eventName === "done") handlers.onDone?.(payload.sources ?? [], payload.conversation_id);
          if (eventName === "error") handlers.onError?.(payload.detail ?? "Something went wrong.");
        } catch {
          // Ignore malformed SSE chunks rather than breaking the stream.
        }
      }

      boundary = buffer.indexOf("\n\n");
    }
  }
}
