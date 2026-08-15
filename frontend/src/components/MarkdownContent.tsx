import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

type MarkdownContentProps = {
  content: string;
  className?: string;
};

/**
 * Shared Markdown renderer used anywhere Atlas's answers are displayed
 * (Search answers, Chat messages) so formatting never drifts out of sync
 * between surfaces again.
 */
export function MarkdownContent({ content, className = "answer-markdown" }: MarkdownContentProps) {
  return (
    <div className={className}>
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
          code: ({ className: codeClassName, children, ...props }) => {
            const isBlock = Boolean(codeClassName);
            if (!isBlock) {
              return (
                <code className="inline-code" {...props}>
                  {children}
                </code>
              );
            }
            return (
              <code className={codeClassName} {...props}>
                {children}
              </code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}