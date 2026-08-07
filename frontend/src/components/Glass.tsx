import type { PropsWithChildren } from "react";

type GlassCardProps = PropsWithChildren<{
  className?: string;
  as?: "section" | "article" | "div";
}>;

export function GlassCard({ as: Element = "section", className = "", children }: GlassCardProps) {
  return <Element className={`glass-card ${className}`}>{children}</Element>;
}

export function Loader({ label = "Thinking" }: { label?: string }) {
  return (
    <div className="loader" role="status" aria-live="polite">
      <span />
      <span />
      <span />
      <p>{label}</p>
    </div>
  );
}
