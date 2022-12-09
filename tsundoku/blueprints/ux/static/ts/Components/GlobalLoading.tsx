interface GlobalLoadingParams {
  withText?: boolean;
  heightTranslation?: string;
}

export const GlobalLoading = ({
  withText,
  heightTranslation,
}: GlobalLoadingParams) => {
  if (!withText) withText = false;
  if (!heightTranslation) heightTranslation = "translateY(33vh)";

  return (
    <progress
      className="progress is-large is-primary"
      style={{ transform: heightTranslation }}
      max="100"
    />
  );
};
