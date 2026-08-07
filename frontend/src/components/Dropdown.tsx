import type { ReactNode } from "react";
import { ChevronDownIcon } from "./Icons";

type DropdownProps = {
  icon: ReactNode;
  label: string;
  value: string;
};

export function Dropdown({ icon, label, value }: DropdownProps) {
  return (
    <button className="filter-button" type="button" aria-label={`${label}: ${value}`}>
      <span className="filter-icon">{icon}</span>
      <span>
        <small>{label}</small>
        <strong>{value}</strong>
      </span>
      <ChevronDownIcon aria-hidden="true" />
    </button>
  );
}
