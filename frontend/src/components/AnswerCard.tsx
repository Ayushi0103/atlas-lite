import { GlassCard, Loader } from "./Glass";
import { MarkdownContent } from "./MarkdownContent";

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
          <MarkdownContent content={answer} />
        ) : (
          <p>Ask a question to let Atlas synthesize an answer from your indexed files.</p>
        )
      )}
    </GlassCard>
  );
}