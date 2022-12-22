const loadingQuips = [
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
  "Sorry, that was a strange thing to ask.",
  "Gotta catch 'em all!",
  "I'll become the Pirate King!",
  "I am the bone of my sword",
  "Believe in the Kamina who believes in you!",
  "I'm coming through!",
  "It's a terrible day for rain...",
  "This could have been a spoiler!",
  "すもももももももものうち",
  "I'll leave tomorrow's problems to tomorrow's me.",
  "Life is not a game of luck. If you wanna win, work hard."
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
