import { useRef } from "react";
import { ClockIcon, FileIcon, GridIcon, SearchIcon, UploadIcon } from "./Icons";
import { Dropdown, type DropdownOption } from "./Dropdown";
import type { SearchFilters } from "../types/atlas";

type TopToolbarProps = {
  filters: SearchFilters;
  isUploading: boolean;
  onAskAI: () => void;
  onFiltersChange: (filters: SearchFilters) => void;
  onUpload: (file: File) => void;
};

const SCOPE_OPTIONS: DropdownOption[] = [
  { label: "All Files", value: "all" },
  { label: "Documents", value: "documents" },
  { label: "Notes", value: "notes" },
];

const RECENCY_OPTIONS: DropdownOption[] = [
  { label: "Anytime", value: "all" },
  { label: "Today", value: "today" },
  { label: "This week", value: "week" },
  { label: "This month", value: "month" },
];

const FILE_TYPE_OPTIONS: DropdownOption[] = [
  { label: "All Types", value: "all" },
  { label: "PDF", value: "pdf" },
  { label: "DOCX", value: "docx" },
  { label: "TXT / MD", value: "txt" },
  { label: "Images", value: "image" },
  { label: "Audio", value: "audio" },
  { label: "YouTube", value: "youtube" },
];

export function TopToolbar({ filters, isUploading, onAskAI, onFiltersChange, onUpload }: TopToolbarProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <header className="top-toolbar">
      <button className="ask-pill" onClick={onAskAI} type="button">
        <SearchIcon aria-hidden="true" />
        <span>Ask AI</span>
      </button>
      <div className="toolbar-filters" aria-label="Search filters">
        <Dropdown
          icon={<FileIcon />}
          label="Search in"
          onChange={(value) => onFiltersChange({ ...filters, scope: value as SearchFilters["scope"] })}
          options={SCOPE_OPTIONS}
          value={filters.scope}
        />
        <Dropdown
          icon={<ClockIcon />}
          label="Recently accessed"
          onChange={(value) => onFiltersChange({ ...filters, since: value as SearchFilters["since"] })}
          options={RECENCY_OPTIONS}
          value={filters.since}
        />
        <Dropdown
          icon={<GridIcon />}
          label="File types"
          onChange={(value) => onFiltersChange({ ...filters, fileType: value === "all" ? null : value })}
          options={FILE_TYPE_OPTIONS}
          value={filters.fileType ?? "all"}
        />
      </div>
      <input
        className="visually-hidden"
        type="file"
        ref={inputRef}
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onUpload(file);
          event.currentTarget.value = "";
        }}
      />
      <button
        className="upload-pill"
        disabled={isUploading}
        onClick={() => inputRef.current?.click()}
        type="button"
      >
        <UploadIcon aria-hidden="true" />
        <span>{isUploading ? "Uploading" : "Upload"}</span>
      </button>
    </header>
  );
}
