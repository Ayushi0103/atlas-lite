import type { AskResponse, DocumentFile, SemanticResult } from "../types/atlas";

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

export function askAtlas(question: string) {
  return request<AskResponse>("/ai/ask", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}

export async function semanticSearch(query: string, topK = 6) {
  const payload = await request<{ results: SemanticResult[] }>("/search/semantic", {
    method: "POST",
    body: JSON.stringify({ query, top_k: topK }),
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
