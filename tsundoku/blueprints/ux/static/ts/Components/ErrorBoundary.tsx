import { Component, type ErrorInfo, type ReactNode } from "react";
import { useRouteError } from "react-router-dom";
import { getInjector } from "../fluent";
import { IonIcon } from "../icon";

const _ = getInjector();

// Enough to identify the failure without the fallback becoming the wall of
// text it exists to prevent. The full error always goes to the console.
const MAX_DETAIL_CHARS = 300;

const describe = (error: unknown): string => {
  if (error instanceof Error) return error.message;
  if (typeof error === "string") return error;

  try {
    return JSON.stringify(error);
  } catch {
    return String(error);
  }
};

interface ErrorPanelProps {
  error: unknown;
  onRetry?: () => void;
}

/**
 * Shared fallback UI.
 *
 * Deliberately depends on nothing but Fluent and an icon -- a fallback that
 * needs the query client or the router cannot render when those are what
 * broke.
 */
const ErrorPanel = ({ error, onRetry }: ErrorPanelProps) => {
  const detail = describe(error);

  return (
    <div className="container my-6">
      <article className="message is-danger">
        <div className="message-header">
          <p>
            <span className="icon mr-2">
              <IonIcon name="warning" />
            </span>
            {_("error-boundary-title")}
          </p>
        </div>
        <div className="message-body">
          <p className="mb-4">{_("error-boundary-subtitle")}</p>

          {detail && (
            <pre
              className="mb-4"
              style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}
            >
              {detail.length > MAX_DETAIL_CHARS
                ? `${detail.slice(0, MAX_DETAIL_CHARS - 1)}…`
                : detail}
            </pre>
          )}

          <div className="buttons">
            {onRetry && (
              <button
                type="button"
                className="button is-danger"
                onClick={onRetry}
              >
                {_("error-boundary-retry")}
              </button>
            )}
            <button
              type="button"
              className="button"
              onClick={() => window.location.reload()}
            >
              {_("error-boundary-reload")}
            </button>
          </div>
        </div>
      </article>
    </div>
  );
};

interface ErrorBoundaryProps {
  children?: ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

/**
 * Catches render-time errors so a component crash shows a recoverable panel
 * rather than an empty page. Wraps the whole app, for anything the router's
 * own boundary does not intercept.
 */
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Unhandled render error:", error, info.componentStack);
  }

  private reset = () => {
    this.setState({ error: null });
  };

  render() {
    if (!this.state.error) return this.props.children;

    return <ErrorPanel error={this.state.error} onRetry={this.reset} />;
  }
}

/**
 * Route-level fallback. React Router catches errors thrown while rendering a
 * route before they reach the boundary above, and would otherwise show its own
 * developer-facing page.
 */
export const RouteErrorBoundary = () => {
  const error = useRouteError();
  console.error("Unhandled route error:", error);

  return <ErrorPanel error={error} />;
};
