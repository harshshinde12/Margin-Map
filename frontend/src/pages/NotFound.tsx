import { Link } from 'react-router-dom';

export function NotFound() {
  return (
    <div className="page">
      <div className="state-card notfound">
        <h4>Page not found.</h4>
        <p>The requested view does not exist in this application.</p>
        <Link className="btn btn-primary" to="/executive" style={{ textDecoration: 'none' }}>
          Back to Executive
        </Link>
      </div>
    </div>
  );
}
