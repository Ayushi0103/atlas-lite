import { FormEvent, useEffect, useRef, useState } from "react";
import { GlassCard, Loader } from "./Glass";
import { ArrowUpRightIcon, HomeIcon, SparkleIcon, SunIcon } from "./Icons";
import {
  deleteConversation,
  getConversation,
  getConversations,
  streamChatMessage,
} from "../services/atlasApi";
import type { ChatConversation, ChatMessage } from "../types/atlas";

type ChatPageProps = {
  isOpen: boolean;
  onClose: () => void;
};

let localMessageId = -1;

export function ChatPage({ isOpen, onClose }: ChatPageProps) {
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isLoadingThread, setIsLoadingThread] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamingText, setStreamingText] = useState("");
  const streamingTextRef = useRef("");
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);

  async function refreshList() {
    setIsLoadingList(true);
    try {
      setConversations(await getConversations());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load conversations.");
    } finally {
      setIsLoadingList(false);
      setHasLoadedOnce(true);
    }
  }

  useEffect(() => {
    if (isOpen && !hasLoadedOnce) void refreshList();
  }, [isOpen, hasLoadedOnce]);

  async function openConversation(id: number) {
    setActiveId(id);
    setIsLoadingThread(true);
    setError(null);
    try {
      const detail = await getConversation(id);
      setMessages(detail.messages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load this conversation.");
    } finally {
      setIsLoadingThread(false);
    }
  }

  function startNewConversation() {
    setActiveId(null);
    setMessages([]);
    setError(null);
    setStreamingText("");
  }

  async function handleDelete(id: number) {
    setError(null);
    try {
      await deleteConversation(id);
      if (activeId === id) startNewConversation();
      await refreshList();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete this conversation.");
    }
  }

  async function handleSend(event: FormEvent) {
    event.preventDefault();
    const question = draft.trim();
    if (!question || isSending) return;

    setDraft("");
    setError(null);
    setIsSending(true);
    setMessages((prev) => [
      ...prev,
      {
        id: localMessageId--,
        conversation_id: activeId ?? 0,
        role: "user",
        content: question,
        created_at: new Date().toISOString(),
      },
    ]);
    streamingTextRef.current = "";
    setStreamingText("");

    try {
      await streamChatMessage(
        { conversationId: activeId, question },
        {
          onMeta: (conversationId) => {
            if (activeId === null) setActiveId(conversationId);
          },
          onToken: (text) => {
            streamingTextRef.current += text;
            setStreamingText(streamingTextRef.current);
          },
          onDone: async (_sources, conversationId) => {
            setStreamingText("");
            await openConversation(conversationId);
            await refreshList();
          },
          onError: (detail) => {
            setError(detail);
            setStreamingText("");
          },
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reach Atlas chat.");
      setStreamingText("");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className={`result-sheet ${isOpen ? "is-open" : ""}`} aria-hidden={!isOpen}>
      <div className="sheet-frame">
        <header className="sheet-header">
          <button className="sheet-home" aria-label="Back home" onClick={onClose} type="button">
            <HomeIcon aria-hidden="true" />
          </button>
          <div className="query-pill">Chat</div>
          <div className="greeting">Good morning <SunIcon aria-hidden="true" /></div>
        </header>
        <div className="sheet-content">
          <div className="chat-layout">
            <GlassCard className="chat-sidebar">
              <button className="panel-link chat-new-button" onClick={startNewConversation} type="button">
                New chat
              </button>
              {isLoadingList && <Loader label="Loading chats" />}
              <div className="chat-list">
                {conversations.map((conversation) => (
                  <div
                    className={`chat-list-item ${conversation.id === activeId ? "is-active" : ""}`}
                    key={conversation.id}
                  >
                    <button onClick={() => openConversation(conversation.id)} type="button">
                      {conversation.title}
                    </button>
                    <button
                      aria-label={`Delete ${conversation.title}`}
                      className="danger-link"
                      onClick={() => handleDelete(conversation.id)}
                      type="button"
                    >
                      ×
                    </button>
                  </div>
                ))}
                {!isLoadingList && conversations.length === 0 && (
                  <p className="empty-copy">Start a new chat to talk with Atlas.</p>
                )}
              </div>
            </GlassCard>

            <GlassCard className="chat-thread">
              {isLoadingThread && <Loader label="Loading conversation" />}
              {!isLoadingThread && (
                <div className="chat-messages">
                  {messages.map((message) => (
                    <div className={`chat-bubble chat-bubble-${message.role}`} key={message.id}>
                      <p>{message.content}</p>
                    </div>
                  ))}
                  {streamingText && (
                    <div className="chat-bubble chat-bubble-assistant">
                      <p>{streamingText}</p>
                    </div>
                  )}
                  {messages.length === 0 && !streamingText && (
                    <p className="empty-copy">Ask Atlas anything about your files.</p>
                  )}
                </div>
              )}
              {error && <p className="error-copy">{error}</p>}
              <form className="chat-input-row" onSubmit={handleSend}>
                <SparkleIcon aria-hidden="true" />
                <input
                  aria-label="Message Atlas"
                  disabled={isSending}
                  onChange={(event) => setDraft(event.target.value)}
                  placeholder="Message Atlas..."
                  value={draft}
                />
                <button aria-label="Send message" disabled={isSending || !draft.trim()} type="submit">
                  <ArrowUpRightIcon aria-hidden="true" />
                </button>
              </form>
            </GlassCard>
          </div>
        </div>
      </div>
    </section>
  );
}