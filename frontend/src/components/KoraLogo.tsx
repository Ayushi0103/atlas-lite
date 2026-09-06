type KoraLogoProps = {
  compact?: boolean;
};

export function KoraLogo({ compact = false }: KoraLogoProps) {
  return (
    <div className={`kora-logo ${compact ? "is-compact" : ""}`}>
      <span className="kora-mark" aria-hidden="true" />
      <div>
        <strong>KORA</strong>
        {!compact && <span>Knowledge Organizer & Retrieval Assistant</span>}
      </div>
    </div>
  );
}
