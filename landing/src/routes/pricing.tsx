import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Check, CreditCard, Loader2, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { PageShell, StoreBadges } from "@/components/mirror-shell";
import { ApiError, listPlans, login, register, startCheckout, type AuthUser, type BillingPlan, type PlanPublic } from "@/lib/api";

export const Route = createFileRoute("/pricing")({ head: () => ({ meta: [
  { title: "Pricing — mirror Nigerian Atelier Edition" }, { name: "description", content: "Prepaid Mirror Pro, billed through Paystack and tied to your Mirror account - not your device." },
  { property: "og:title", content: "mirror pricing" }, { property: "og:description", content: "Prepaid Pro plans, paid once per period through Paystack." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" },
] }), component: PricingPage });

const naira = new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN", maximumFractionDigits: 0 });

const planCopy: Record<BillingPlan, { eyebrow: string; features: string[]; highlighted: boolean }> = {
  solo: {
    eyebrow: "For yourself",
    features: ["Full on-device simulation", "Personal look library", "Certified shade library", "Works fully offline"],
    highlighted: false,
  },
  studio: {
    eyebrow: "For artists & studios",
    features: ["Client Mode Directory", "Private client profiles", "Unlimited shade formulations", "Studio-ready exports"],
    highlighted: true,
  },
};

type CheckoutStep = "credentials" | "redirecting";
type AuthMode = "login" | "register";

function PricingPage() {
  const [plans, setPlans] = useState<PlanPublic[] | null>(null);
  const [plansError, setPlansError] = useState("");
  const [checkoutPlan, setCheckoutPlan] = useState<PlanPublic | null>(null);

  useEffect(() => {
    listPlans().then(setPlans).catch(() => setPlansError("Couldn't load plans right now. Please refresh the page."));
  }, []);

  return <PageShell><main className="px-5 pb-24 pt-36 sm:px-8 md:pt-44"><div className="mx-auto max-w-6xl">
    <header className="reveal-flow text-center"><p className="text-xs font-semibold uppercase text-primary">Atelier access</p><h1 className="mx-auto mt-4 max-w-3xl text-balance text-6xl leading-[.95] sm:text-7xl">Choose the space your artistry needs.</h1><p className="mx-auto mt-6 max-w-xl text-muted-foreground">Prepaid Mirror Pro, paid through Paystack. Your plan is tied to your Mirror account, not this device or browser.</p></header>

    {plansError && <p className="reveal-flow mx-auto mt-10 max-w-md rounded-2xl bg-destructive/10 p-5 text-center text-sm text-destructive">{plansError}</p>}

    {!plans && !plansError && <div className="mt-20 flex justify-center"><Loader2 className="size-8 animate-spin text-primary" /></div>}

    {plans && (
      <div className="mt-16 grid gap-6 md:grid-cols-2">
        {plans.map((plan) => <Plan key={plan.plan} plan={plan} onChoose={() => setCheckoutPlan(plan)} />)}
      </div>
    )}

    <div className="mt-16 flex flex-col items-center gap-5 text-center"><p className="text-sm text-muted-foreground">Prefer to purchase in the app?</p><StoreBadges /></div>
  </div></main>
  <CheckoutDialog plan={checkoutPlan} onClose={() => setCheckoutPlan(null)} />
  </PageShell>;
}

function Plan({ plan, onChoose }: { plan: PlanPublic; onChoose: () => void }) {
  const copy = planCopy[plan.plan];
  return <article className={`reveal-flow flex min-h-[530px] flex-col rounded-[2.5rem] p-8 sm:p-10 ${copy.highlighted ? "bg-foreground text-background" : "border border-border bg-card"}`}>
    <p className={`text-xs font-semibold uppercase ${copy.highlighted ? "text-secondary" : "text-primary"}`}>{copy.eyebrow}</p>
    <h2 className="mt-3 text-4xl">{plan.name}</h2>
    <p className="mt-8 font-display text-5xl">{naira.format(plan.price_ngn)}<span className={`ml-2 font-body text-xs uppercase ${copy.highlighted ? "text-background/50" : "text-muted-foreground"}`}>every {plan.period_days} days</span></p>
    <ul className="mt-10 flex-1 space-y-4">{copy.features.map((feature) => <li key={feature} className="flex items-center gap-3 text-sm"><span className={`grid size-7 place-items-center rounded-full ${copy.highlighted ? "bg-background/10 text-secondary" : "bg-accent text-primary"}`}><Check className="size-4" /></span>{feature}</li>)}</ul>
    <Button variant={copy.highlighted ? "secondary" : "default"} className="mt-10 h-12 rounded-full" onClick={onChoose}>Choose {plan.name}</Button>
  </article>;
}

function CheckoutDialog({ plan, onClose }: { plan: PlanPublic | null; onClose: () => void }) {
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [step, setStep] = useState<CheckoutStep>("credentials");

  function reset() {
    setMode("login"); setEmail(""); setPassword(""); setBusy(false); setError(""); setStep("credentials");
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!plan) return;
    setBusy(true);
    setError("");
    try {
      const auth: { access_token: string; user: AuthUser } =
        mode === "login" ? await login(email, password) : await register(email, password, plan.plan === "studio" ? "business" : "consumer");
      setStep("redirecting");
      const checkout = await startCheckout(auth.access_token, plan.plan);
      window.location.href = checkout.authorization_url;
    } catch (err) {
      setStep("credentials");
      if (err instanceof ApiError && err.status === 401 && mode === "login") {
        setError("No account with that email and password. New here? Use \"Create an account\" below.");
      } else if (err instanceof ApiError && err.status === 409 && mode === "register") {
        setError("An account with this email already exists. Switch to \"Log in\" instead.");
      } else {
        setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
      }
      setBusy(false);
    }
  }

  return <Dialog open={plan !== null} onOpenChange={(open) => { if (!open) { onClose(); reset(); } }}>
    <DialogContent className="max-w-md rounded-[2rem] border-border p-7">
      {step === "redirecting" ? (
        <div className="py-10 text-center">
          <Loader2 className="mx-auto size-10 animate-spin text-primary" />
          <DialogTitle className="mt-6 font-display text-3xl">Taking you to Paystack…</DialogTitle>
          <DialogDescription className="mt-3">Complete your payment there. You'll land back on Mirror once it's done.</DialogDescription>
        </div>
      ) : (
        <>
          <DialogHeader>
            <DialogTitle className="font-display text-4xl">{mode === "login" ? "Log in to pay" : "Create your account"}</DialogTitle>
            <DialogDescription>{plan?.name} · {plan ? naira.format(plan.price_ngn) : ""} every {plan?.period_days} days. Use the same email you'll sign in with on the app.</DialogDescription>
          </DialogHeader>
          <form className="mt-3 space-y-4" onSubmit={submit}>
            <Input required type="email" placeholder="Email address" value={email} onChange={(event) => setEmail(event.target.value)} className="h-12 rounded-full px-5" />
            <Input required type="password" minLength={8} placeholder={mode === "login" ? "Password" : "Password (min. 8 characters)"} value={password} onChange={(event) => setPassword(event.target.value)} className="h-12 rounded-full px-5" />
            <div className="rounded-2xl bg-muted p-4 text-sm">
              <div className="flex items-center gap-2 font-medium"><CreditCard className="size-4 text-primary" /> Pay securely with Paystack</div>
              <p className="mt-1 text-xs text-muted-foreground">Card, bank transfer, USSD and supported local methods.</p>
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" className="h-12 w-full rounded-full" disabled={busy}>{busy ? "One moment…" : mode === "login" ? "Log in & continue" : "Create account & continue"}</Button>
            <button type="button" className="w-full text-center text-xs text-muted-foreground underline underline-offset-4" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>
              {mode === "login" ? "New here? Create an account instead" : "Already have an account? Log in instead"}
            </button>
            <p className="flex items-center justify-center gap-2 text-xs text-muted-foreground"><ShieldCheck className="size-4" /> Your plan is unlocked on your account, not this device</p>
          </form>
        </>
      )}
    </DialogContent>
  </Dialog>;
}
