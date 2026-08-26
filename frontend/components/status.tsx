export function Status({ value }: Readonly<{ value: string }>) {
  return <span className={`status ${value}`}>{value}</span>;
}

export function Severity({ value }: Readonly<{ value: string }>) {
  return <span className={`severity ${value}`}>{value}</span>;
}
