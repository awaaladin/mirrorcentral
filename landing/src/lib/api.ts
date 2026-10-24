/**
 * Thin client for the mirrorcentral FastAPI backend (the same API the Android app talks to).
 *
 * Default base URL is the production API itself. When this page is served from
 * mirrorcentral.vercel.app (the normal case - see vercel.json's rewrite), these calls are same
 * -origin; from the landing project's own domain they're cross-origin but already allowed by the
 * backend's CORS list. Override locally with VITE_MIRROR_API_BASE_URL (e.g. http://localhost:8000)
 * to test against a backend running on your machine.
 */

const BASE_URL = (import.meta.env["VITE_MIRROR_API_BASE_URL"] as string | undefined)?.replace(/\/$/, "")
  || "https://mirrorcentral.vercel.app";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError("Couldn't reach Mirror's servers. Check your connection and try again.", 0);
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    // no/invalid JSON body - body stays null, handled below per status
  }
  if (!response.ok) {
    const detail = (body as { detail?: string } | null)?.detail;
    throw new ApiError(detail || `Something went wrong (${response.status}).`, response.status);
  }
  return body as T;
}

export type BillingPlan = "solo" | "studio";

export type PlanPublic = {
  plan: BillingPlan;
  name: string;
  price_ngn: number;
  period_days: number;
  /** False = shown (name + price) but not purchasable yet - pricing still under review. */
  available: boolean;
};

export type AuthUser = { id: string; email: string; account_type: "consumer" | "business" };
export type TokenResponse = { access_token: string; refresh_token: string; user: AuthUser };

export function listPlans(): Promise<PlanPublic[]> {
  return request("/billing/plans");
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
}

export function register(email: string, password: string, accountType: "consumer" | "business"): Promise<TokenResponse> {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, account_type: accountType }),
  });
}

export function startCheckout(accessToken: string, plan: BillingPlan): Promise<{ reference: string; authorization_url: string }> {
  return request("/billing/checkout", {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify({ plan }),
  });
}
