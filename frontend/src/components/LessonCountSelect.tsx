interface Props {
  value: number;
  onChange: (n: number) => void;
  disabled?: boolean;
  /** Upper bound of lessons per request (matches the server cap). */
  max?: number;
}

/** Small dropdown to choose how many lessons to generate. */
export function LessonCountSelect({ value, onChange, disabled, max = 5 }: Props) {
  return (
    <label className="flex items-center gap-1 text-sm text-muted-foreground">
      <span className="sr-only">Lessons to add</span>
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        disabled={disabled}
        className="rounded-md border border-input bg-background px-2 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-50"
      >
        {Array.from({ length: max }, (_, i) => i + 1).map((n) => (
          <option key={n} value={n}>
            {n} {n === 1 ? "lesson" : "lessons"}
          </option>
        ))}
      </select>
    </label>
  );
}
