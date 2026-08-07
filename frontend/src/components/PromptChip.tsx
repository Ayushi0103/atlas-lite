import { ArrowUpRightIcon, SparkleIcon } from "./Icons";

type PromptChipProps = {
  label: string;
  onSelect: (label: string) => void;
};

export function PromptChip({ label, onSelect }: PromptChipProps) {
  return (
    <button className="prompt-chip" type="button" onClick={() => onSelect(label)}>
      <SparkleIcon aria-hidden="true" />
      <span>{label}</span>
      <ArrowUpRightIcon aria-hidden="true" />
    </button>
  );
}
