import { useRef } from "react";
import { ClockIcon, FileIcon, GridIcon, SearchIcon, UploadIcon } from "./Icons";
import { Dropdown } from "./Dropdown";

type TopToolbarProps = {
  isUploading: boolean;
  onUpload: (file: File) => void;
};

export function TopToolbar({ isUploading, onUpload }: TopToolbarProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <header className="top-toolbar">
      <button className="ask-pill" type="button">
        <SearchIcon aria-hidden="true" />
        <span>Ask AI</span>
      </button>
      <div className="toolbar-filters" aria-label="Search filters">
        <Dropdown icon={<FileIcon />} label="Search in" value="All Files" />
        <Dropdown icon={<ClockIcon />} label="Recently accessed" value="Anytime" />
        <Dropdown icon={<GridIcon />} label="File types" value="All Types" />
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
