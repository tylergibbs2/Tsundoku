const loadingQuips = [
  "Are you scared of the Home Server Devil?",
  "I have existed for millennia.",
  "???%",
  "Loading 10 billion shows...",
  "Slaying goblins...",
  "In the name of the moon, I will punish you!",
  "We're not hitting it off, are we?",
  "Believe it!",
  "True strength comes from within.",
  "People die if they are killed.",
  "I may not be perfect, but at least I'm not a cabbage.",
  "It's not about revenge. It's about justice.",
  "Sometimes the best way to solve your own problems is to help someone else.",
];

interface GlobalLoadingParams {
  withText?: boolean;
  heightTranslation?: string;
}

export const GlobalLoading = ({
  withText,
  heightTranslation,
}: GlobalLoadingParams) => {
  if (!withText) withText = false;
  if (!heightTranslation) heightTranslation = "translateY(25vh)";

  const loadString =
    loadingQuips[Math.floor(Math.random() * loadingQuips.length)];

  return (
    <div
      style={{ transform: heightTranslation }}
      className="has-text-centered noselect"
    >
      {withText && (
        <h1 className="is-size-2" style={{ marginBottom: "2em" }}>
          {loadString}
        </h1>
      )}
      <progress className="progress is-large is-primary" max="100" />
    </div>
  );
};
