import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Check, CreditCard, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { PageShell, StoreBadges } from "@/components/mirror-shell";

export const Route = createFileRoute("/pricing")({ head: () => ({ meta: [
  { title: "Pricing — mirror Nigerian Atelier Edition" }, { name: "description", content: "Choose lifetime personal access or mirror Pro Atelier Studio for makeup professionals." },
  { property: "og:title", content: "mirror pricing" }, { property: "og:description", content: "One-time personal access and flexible Pro studio plans." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" },
] }), component: PricingPage });

type Tier = "casual" | "pro";
function PricingPage() {
  const [currency, setCurrency] = useState<"NGN" | "USD">("NGN");
  const [checkout, setCheckout] = useState<Tier | null>(null);
  const [complete, setComplete] = useState(false);
  const price = (tier: Tier) => currency === "NGN" ? (tier === "casual" ? "₦15,000" : "₦7,500") : (tier === "casual" ? "$19" : "$9.99");
  return <PageShell><main className="px-5 pb-24 pt-36 sm:px-8 md:pt-44"><div className="mx-auto max-w-6xl">
    <header className="reveal-flow text-center"><p className="text-xs font-semibold uppercase text-primary">Atelier access</p><h1 className="mx-auto mt-4 max-w-3xl text-balance text-6xl leading-[.95] sm:text-7xl">Choose the space your artistry needs.</h1><p className="mx-auto mt-6 max-w-xl text-muted-foreground">One clear purchase for personal looks. A flexible studio subscription for working artists.</p>
      <div className="mt-8 inline-flex rounded-full bg-muted p-1"><Button size="sm" variant={currency === "NGN" ? "default" : "ghost"} className="rounded-full px-5" onClick={() => setCurrency("NGN")}>NGN ₦</Button><Button size="sm" variant={currency === "USD" ? "default" : "ghost"} className="rounded-full px-5" onClick={() => setCurrency("USD")}>USD $</Button></div>
    </header>
    <div className="mt-16 grid gap-6 md:grid-cols-2">
      <Plan eyebrow="For yourself" title="Casual / Personal" price={price("casual")} suffix="once" features={["Lifetime on-device simulation", "Personal look library", "Certified shade library", "Works fully offline"]} onChoose={() => setCheckout("casual")} />
      <Plan highlighted eyebrow="For artists & studios" title="Pro Atelier Studio" price={price("pro")} suffix="per month" features={["Client Mode Directory", "Private client profiles", "Unlimited shade formulations", "Studio-ready exports"]} onChoose={() => setCheckout("pro")} />
    </div>
    <div className="mt-16 flex flex-col items-center gap-5 text-center"><p className="text-sm text-muted-foreground">Prefer to purchase in the app?</p><StoreBadges /></div>
  </div></main>
  <Dialog open={checkout !== null} onOpenChange={(open) => { if (!open) { setCheckout(null); setComplete(false); } }}><DialogContent className="max-w-md rounded-[2rem] border-border p-7">
    {complete ? <div className="py-8 text-center"><div className="mx-auto grid size-14 place-items-center rounded-full bg-accent text-primary"><Check /></div><DialogTitle className="mt-5 font-display text-4xl">Ready for Flutterwave</DialogTitle><DialogDescription className="mt-3">Your order has been prepared. Live payment will open here once your Flutterwave business details are connected.</DialogDescription><Button className="mt-7 rounded-full px-7" onClick={() => setCheckout(null)}>Done</Button></div> : <><DialogHeader><DialogTitle className="font-display text-4xl">Complete your order</DialogTitle><DialogDescription>{checkout === "pro" ? "Pro Atelier Studio subscription" : "Casual / Personal lifetime access"} · {checkout ? price(checkout) : ""}</DialogDescription></DialogHeader>
    <form className="mt-3 space-y-4" onSubmit={(event) => { event.preventDefault(); setComplete(true); }}><Input required type="email" placeholder="Email address" className="h-12 rounded-full px-5" /><Input required placeholder="Full name" className="h-12 rounded-full px-5" /><div className="rounded-2xl bg-muted p-4 text-sm"><div className="flex items-center gap-2 font-medium"><CreditCard className="size-4 text-primary" /> Pay securely with Flutterwave</div><p className="mt-1 text-xs text-muted-foreground">Card, bank transfer, USSD and supported local methods.</p></div><Button type="submit" className="h-12 w-full rounded-full">Continue to payment</Button><p className="flex items-center justify-center gap-2 text-xs text-muted-foreground"><ShieldCheck className="size-4" /> Secure checkout preview</p></form></>}
  </DialogContent></Dialog>
  </PageShell>;
}

function Plan({ eyebrow, title, price, suffix, features, onChoose, highlighted = false }: { eyebrow: string; title: string; price: string; suffix: string; features: string[]; onChoose: () => void; highlighted?: boolean }) {
  return <article className={`reveal-flow flex min-h-[530px] flex-col rounded-[2.5rem] p-8 sm:p-10 ${highlighted ? "bg-foreground text-background" : "border border-border bg-card"}`}><p className={`text-xs font-semibold uppercase ${highlighted ? "text-secondary" : "text-primary"}`}>{eyebrow}</p><h2 className="mt-3 text-4xl">{title}</h2><p className="mt-8 font-display text-5xl">{price}<span className={`ml-2 font-body text-xs uppercase ${highlighted ? "text-background/50" : "text-muted-foreground"}`}>{suffix}</span></p><ul className="mt-10 flex-1 space-y-4">{features.map((feature) => <li key={feature} className="flex items-center gap-3 text-sm"><span className={`grid size-7 place-items-center rounded-full ${highlighted ? "bg-background/10 text-secondary" : "bg-accent text-primary"}`}><Check className="size-4" /></span>{feature}</li>)}</ul><Button variant={highlighted ? "secondary" : "default"} className="mt-10 h-12 rounded-full" onClick={onChoose}>Choose {title}</Button></article>;
}