import { useCallback, useEffect, useMemo, useState } from "react";
import { askAtlas, getDocuments, semanticSearch, uploadDocument } from "../services/atlasApi";
import type { DocumentFile, SearchFilters, SearchState } from "../types/atlas";
import { useNotifications } from "../context/NotificationsContext";

const emptySearch: SearchState = {
  query: "",
  answer: "",
  sources: [],
  semanticResults: [],
  relatedConcepts: [],
  intent: null,
};

const defaultFilters: SearchFilters = {
  scope: "all",
  fileType: null,
  since: "all",
};

function parseStringList(value?: string | null): string[] {
  if (!value) return [];
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === "string") : [];
  } catch {
    return value.split(",").map((item) => item.trim()).filter(Boolean);
  }
}

export function useAtlasSearch() {
  const { notify } = useNotifications();
  const [documents, setDocuments] = useState<DocumentFile[]>([]);
  const [search, setSearch] = useState<SearchState>(emptySearch);
  const [isSheetOpen, setIsSheetOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<SearchFilters>(defaultFilters);

  const refreshDocuments = useCallback(async () => {
    try {
      setDocuments(await getDocuments());
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not load documents.");
    }
  }, []);

  useEffect(() => {
    void refreshDocuments();
  }, [refreshDocuments]);

  const promptSuggestions = useMemo(() => {
    const questions = documents.flatMap((document) => parseStringList(document.suggested_questions));
    return Array.from(new Set(questions)).slice(0, 4);
  }, [documents]);

  const submitSearch = useCallback(async (query: string) => {
    const cleaned = query.trim();
    if (!cleaned) return;

    setIsSheetOpen(true);
    setIsLoading(true);
    setError(null);
    setSearch({ ...emptySearch, query: cleaned });

    try {
      const [answer, semanticResults] = await Promise.all([
        askAtlas(cleaned, filters),
        semanticSearch(cleaned, 6, filters),
      ]);

      setSearch({
        query: cleaned,
        answer: answer.answer,
        sources: answer.sources ?? [],
        semanticResults,
        relatedConcepts: answer.related_concepts ?? [],
        intent: answer.intent ?? null,
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : "KORA could not answer that yet.");
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  const handleUpload = useCallback(async (file: File) => {
  setIsUploading(true);
  setError(null);
  try {
    await uploadDocument(file);
    await refreshDocuments();
    notify("File uploaded", `${file.name} was added to your library.`, "success");
  } catch (error) {
    const message = error instanceof Error ? error.message : "Could not upload this file.";
    setError(message);
    notify("Upload failed", message, "error");
  } finally {
    setIsUploading(false);
  }
}, [refreshDocuments, notify]);

  return {
    documents,
    error,
    filters,
    handleUpload,
    isLoading,
    isSheetOpen,
    isUploading,
    promptSuggestions,
    search,
    setFilters,
    setIsSheetOpen,
    submitSearch,
  };
}
