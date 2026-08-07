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
        <p>{answer || "Ask a question to let Atlas synthesize an answer from your indexed files."}</p>
      )}
    </GlassCard>
  );
}
