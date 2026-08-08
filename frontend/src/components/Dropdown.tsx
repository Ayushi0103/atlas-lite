import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { ChevronDownIcon } from "./Icons";

export type DropdownOption = {
  label: string;
  value: string;
};

type DropdownProps = {
  icon: ReactNode;
  label: string;
  value: string;
  options: DropdownOption[];
  onChange: (value: string) => void;
};

export function Dropdown({ icon, label, value, options, onChange }: DropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const activeLabel = options.find((option) => option.value === value)?.label ?? value;

  useEffect(() => {
    function handleClickAway(event: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickAway);
    return () => document.removeEventListener("mousedown", handleClickAway);
  }, []);

  return (
    <div className="filter-dropdown" ref={rootRef}>
      <button
        aria-expanded={isOpen}
        aria-label={`${label}: ${activeLabel}`}
        className="filter-button"
        onClick={() => setIsOpen((open) => !open)}
        type="button"
      >
        <span className="filter-icon">{icon}</span>
        <span>
          <small>{label}</small>
          <strong>{activeLabel}</strong>
        </span>
        <ChevronDownIcon aria-hidden="true" />
      </button>
      {isOpen && (
        <ul className="filter-menu" role="listbox">
          {options.map((option) => (
            <li key={option.value}>
              <button
                aria-selected={option.value === value}
                className={`filter-menu-item ${option.value === value ? "is-selected" : ""}`}
                onClick={() => {
                  onChange(option.value);
                  setIsOpen(false);
                }}
                role="option"
                type="button"
              >
                {option.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
