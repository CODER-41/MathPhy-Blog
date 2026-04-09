interface Props {
  category: string;
  onClick?: () => void;
  active?: boolean;
}

export default function CategoryBadge({ category, onClick, active }: Props) {
  const base = "inline-block rounded-full px-3 py-1 text-xs font-medium tracking-wide transition-colors cursor-default";
  const styles = active
    ? "bg-primary text-primary-foreground"
    : "bg-secondary text-secondary-foreground hover:bg-primary/20 hover:text-primary";

  return onClick ? (
    <button onClick={onClick} className={`${base} ${styles} cursor-pointer`}>
      {category}
    </button>
  ) : (
    <span className={`${base} ${styles}`}>{category}</span>
  );
}
