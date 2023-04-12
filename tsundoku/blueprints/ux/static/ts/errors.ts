export class APIError extends Error {
  constructor(text: string, public subtext: string | null = null) {
    super(text);
  }
}
