import { FileIcon } from "./Icons";

const colors: Record<string, string> = {
  pdf: "file-red",
  mp3: "file-purple",
  wav: "file-purple",
  m4a: "file-purple",
  mp4: "file-pink",
  docx: "file-blue",
  md: "file-blue",
  txt: "file-blue",
  png: "file-green",
  jpg: "file-green",
  jpeg: "file-green",
  webp: "file-green",
  youtube: "file-red",
};

export function FileBadge({ type }: { type?: string }) {
  const normalized = type?.toLowerCase() ?? "file";
  return (
    <span className={`file-badge ${colors[normalized] ?? "file-blue"}`}>
      <FileIcon aria-hidden="true" />
    </span>
  );
}
