import { PaginationInfo } from "../../interfaces";
import { getInjector } from "../../fluent";

const _ = getInjector();

interface PaginationProps {
  pagination: PaginationInfo;
  onPageChange: (page: number) => void;
}

export const Pagination = ({ pagination, onPageChange }: PaginationProps) => {
  const { page, pages, total } = pagination;

  if (pages <= 1) {
    return null;
  }

  const getPageNumbers = () => {
    const pageNumbers = [];
    const maxVisible = 5;

    if (pages <= maxVisible) {
      for (let i = 1; i <= pages; i++) {
        pageNumbers.push(i);
      }
    } else {
      pageNumbers.push(1);
      let start = Math.max(2, page - 1);
      let end = Math.min(pages - 1, page + 1);
      if (page <= 3) {
        end = Math.min(pages - 1, 4);
      } else if (page >= pages - 2) {
        start = Math.max(2, pages - 3);
      }
      if (start > 2) {
        pageNumbers.push("...");
      }
      for (let i = start; i <= end; i++) {
        pageNumbers.push(i);
      }
      if (end < pages - 1) {
        pageNumbers.push("...");
      }
      if (pages > 1) {
        pageNumbers.push(pages);
      }
    }
    return pageNumbers;
  };

  return (
    <div style={{ marginTop: 24 }}>
      {/* Controls centered */}
      <nav className="pagination is-centered" role="navigation" aria-label="pagination">
        <button
          className="pagination-previous"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          style={{ marginRight: 8 }}
        >
          {_("pagination-previous")}
        </button>
        <ul className="pagination-list" style={{ display: "flex", alignItems: "center" }}>
          {getPageNumbers().map((pageNum, index) => (
            <li key={index}>
              {pageNum === "..." ? (
                <span className="pagination-ellipsis">&hellip;</span>
              ) : (
                <button
                  className={`pagination-link ${pageNum === page ? "is-current" : ""}`}
                  onClick={() => onPageChange(pageNum as number)}
                  aria-label={`Page ${pageNum}`}
                  aria-current={pageNum === page ? "page" : undefined}
                  style={{ margin: "0 2px" }}
                >
                  {pageNum}
                </button>
              )}
            </li>
          ))}
        </ul>
        <button
          className="pagination-next"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= pages}
          style={{ marginLeft: 8 }}
        >
          {_("pagination-next")}
        </button>
      </nav>
      {/* Info text below, centered */}
      <div style={{ textAlign: "center", marginTop: 8 }}>
        <small className="has-text-grey">
          {_("pagination-showing")} {((page - 1) * pagination.limit) + 1}-{Math.min(page * pagination.limit, total)} {_("pagination-of")} {total} {_("pagination-items")}
        </small>
      </div>
    </div>
  );
};