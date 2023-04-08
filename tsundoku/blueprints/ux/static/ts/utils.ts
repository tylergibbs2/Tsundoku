import humanizeDuration from "humanize-duration";

export const pythonTimeToDate = (pythonTime: string): Date => {
  let timeString = pythonTime + (pythonTime.endsWith("Z") ? "" : "Z");
  return new Date(timeString);
};

type DateTimeStyle = "full" | "medium" | "long" | "short";

export const localizePythonTimeAbsolute = (
  pythonTime: string,
  dateStyle: DateTimeStyle = "full",
  timeStyle: DateTimeStyle = "medium"
): string => {
  const date = pythonTimeToDate(pythonTime);

  return new Intl.DateTimeFormat(window["LOCALE"], {
    dateStyle: dateStyle,
    timeStyle: timeStyle,
  }).format(date);
};

export const localizePythonTimeRelative = (pythonTime: string): string => {
  const date = pythonTimeToDate(pythonTime);
  const diff = date.getTime() - Date.now();

  return humanizeDuration(diff, {
    language: window["LOCALE"],
    fallbacks: ["en"],
    round: true,
    largest: 2,
  });
};

export const formatBytes = (bytes: number, decimals: number = 2): string => {
  if (!+bytes) return "0 Bytes";

  const k = 1000;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
};
