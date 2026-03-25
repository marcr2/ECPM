/**
 * Browser API base URL. Set NEXT_PUBLIC_API_URL at build time when the UI and API
 * are on different origins. Leave unset for same-origin deployments (e.g. Caddy
 * routing / and /api to different upstreams): the browser uses window.location.origin.
 */
export function getPublicApiBase(): string {
  const env = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (env) {
    return env.replace(/\/$/, "");
  }
  if (typeof window !== "undefined") {
    return window.location.origin;
  }
  return "http://localhost:8000";
}
