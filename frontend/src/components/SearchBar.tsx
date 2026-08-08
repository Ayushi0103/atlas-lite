import { FormEvent, forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import { ArrowUpRightIcon, SparkleIcon } from "./Icons";

type SearchBarProps = {
  disabled?: boolean;
  initialValue?: string;
  onSubmit: (query: string) => void;
};

export type SearchBarHandle = {
  focus: () => void;
};

export const SearchBar = forwardRef<SearchBarHandle, SearchBarProps>(function SearchBar(
  { disabled = false, initialValue = "", onSubmit },
  ref,
) {
  const [query, setQuery] = useState(initialValue);
  const inputRef = useRef<HTMLInputElement>(null);

  useImperativeHandle(ref, () => ({
    focus: () => inputRef.current?.focus(),
  }));

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSubmit(query);
  }

  return (
    <form className="hero-search" onSubmit={handleSubmit} role="search">
      <SparkleIcon className="search-spark" aria-hidden="true" />
      <input
        aria-label="Ask anything from your files"
        disabled={disabled}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Ask anything from your files..."
        ref={inputRef}
        type="search"
        value={query}
      />
      <button aria-label="Search Atlas Lite" disabled={disabled || !query.trim()} type="submit">
        <ArrowUpRightIcon aria-hidden="true" />
      </button>
    </form>
  );
});
