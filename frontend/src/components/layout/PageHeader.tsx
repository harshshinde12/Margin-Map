interface PageHeaderProps {
  title: string;
  lede: string;
  meta?: React.ReactNode;
}

export function PageHeader({ title, lede, meta }: PageHeaderProps) {
  return (
    <header className="page-header">
      <h2>{title}</h2>
      <p className="lede">{lede}</p>
      {meta ? <div className="meta">{meta}</div> : null}
    </header>
  );
}
