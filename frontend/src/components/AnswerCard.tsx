import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { GlassCard, Loader } from "./Glass";

type AnswerCardProps = {
  answer: string;
  error: string | null;
  isLoading: boolean;
};

export function AnswerCard({ answer, error, isLoading }: AnswerCardProps) {
  return (
    <GlassCard className="answer-card">
      {isLoading && <Loader label="Searching your files" />}
      {!isLoading && error && <p className="error-copy">{error}</p>}
      {!isLoading && !error && (
        answer ? (
          <div className="answer-markdown">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
              components={{
                h1: ({ children }) => <h2>{children}</h2>,
                h2: ({ children }) => <h2>{children}</h2>,
                h3: ({ children }) => <h3>{children}</h3>,
                p: ({ children }) => <p>{children}</p>,
                ul: ({ children }) => <ul>{children}</ul>,
                ol: ({ children }) => <ol>{children}</ol>,
                li: ({ children }) => <li>{children}</li>,
                blockquote: ({ children }) => <blockquote>{children}</blockquote>,
                table: ({ children }) => (
                  <div className="answer-table-wrap">
                    <table>{children}</table>
                  </div>
                ),
                code: ({ className, children, ...props }) => {
                  const isBlock = Boolean(className);
                  if (!isBlock) {
                    return (
                      <code className="inline-code" {...props}>
                        {children}
                      </code>
                    );
                  }
                  return (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {answer}
            </ReactMarkdown>
          </div>
        ) : (
          <p>Ask a question to let Atlas synthesize an answer from your indexed files.</p>
        )
      )}
    </GlassCard>
  );
}
