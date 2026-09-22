import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { ArrowRight, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { PageShell } from "@/components/mirror-shell";
import { supabase } from "@/integrations/supabase/client";

export const Route = createFileRoute("/contact")({ head: () => ({ meta: [
  { title: "Contact & Support — mirror" }, { name: "description", content: "Get help with mirror or discuss studio access for your beauty practice." },
  { property: "og:title", content: "Contact mirror atelier" }, { property: "og:description", content: "Support, studio inquiries, and answers about mirror." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" },
] }), component: ContactPage });

const faqs = [
  ["Does mirror really work offline?", "Yes. Face landmark detection, rendering and saved personal looks all run directly on your device after installation."],
  ["What does Personal include?", "Personal is a one-time purchase for lifetime on-device simulation, personal saved looks and the certified shade library."],
  ["What makes Pro different?", "Pro adds client profiles, Client Mode Directory, unlimited formulations and polished studio exports."],
  ["Can I use mirror with client photographs?", "Yes with Pro. The app is designed around private, on-device processing so client portraits do not need to leave the device."],
  ["Which phones are supported?", "mirror is designed for modern iOS and Android phones. Final device compatibility will appear on each store listing."],
];

function ContactPage() {
  const [sent, setSent] = useState(false); const [busy, setBusy] = useState(false); const [error, setError] = useState("");
  async function submit(event: React.FormEvent<HTMLFormElement>) { event.preventDefault(); setBusy(true); setError(""); const form = new FormData(event.currentTarget); const { error: sendError } = await supabase.from("studio_inquiries").insert({ name: String(form.get("name")), email: String(form.get("email")), inquiry_type: String(form.get("inquiry_type")), message: String(form.get("message")) }); setBusy(false); if (sendError) { setError("We couldn’t send this yet. Please try again."); return; } setSent(true); }
  return <PageShell><main className="px-5 pb-24 pt-36 sm:px-8 md:pt-44"><div className="mx-auto max-w-6xl">
    <header className="reveal-flow max-w-3xl"><p className="text-xs font-semibold uppercase text-primary">Support & studio inquiries</p><h1 className="mt-4 text-balance text-6xl leading-[.95] sm:text-7xl">Let’s make space for your artistry.</h1><p className="mt-6 max-w-xl text-lg text-muted-foreground">Questions about the app, a studio rollout, or your purchase? Tell us what you need.</p></header>
    <div className="mt-16 grid gap-12 md:grid-cols-[1.05fr_.95fr]">
      <div className="reveal-flow rounded-[2.5rem] bg-foreground p-7 text-background sm:p-10">{sent ? <div className="flex min-h-[420px] flex-col items-center justify-center text-center"><div className="grid size-14 place-items-center rounded-full bg-secondary text-foreground"><Check /></div><h2 className="mt-6 text-4xl">Your note is with us.</h2><p className="mt-3 max-w-sm text-sm text-background/60">We’ll reply to the email you shared.</p></div> : <form className="space-y-5" onSubmit={submit}><div><label className="mb-2 block text-xs uppercase text-background/60">Name</label><Input required name="name" minLength={2} className="h-12 rounded-full border-background/15 bg-background/5 px-5 text-background placeholder:text-background/30" placeholder="Your name" /></div><div><label className="mb-2 block text-xs uppercase text-background/60">Email</label><Input required name="email" type="email" className="h-12 rounded-full border-background/15 bg-background/5 px-5 text-background placeholder:text-background/30" placeholder="you@example.com" /></div><div><label className="mb-2 block text-xs uppercase text-background/60">What can we help with?</label><select name="inquiry_type" className="h-12 w-full rounded-full border border-background/15 bg-foreground px-5 text-sm"><option value="support">App support</option><option value="studio">Studio inquiry</option><option value="press">Press & partnerships</option></select></div><div><label className="mb-2 block text-xs uppercase text-background/60">Message</label><Textarea required name="message" minLength={10} className="min-h-36 rounded-3xl border-background/15 bg-background/5 p-5 text-background placeholder:text-background/30" placeholder="Tell us a little about what you need…" /></div>{error && <p className="text-sm text-secondary">{error}</p>}<Button type="submit" variant="secondary" className="h-12 w-full rounded-full" disabled={busy}>{busy ? "Sending…" : <>Send inquiry <ArrowRight /></>}</Button></form>}</div>
      <div className="reveal-flow pt-4"><p className="text-xs font-semibold uppercase text-primary">Frequently asked</p><h2 className="mt-3 text-5xl">A few useful answers.</h2><Accordion type="single" collapsible className="mt-9">{faqs.map(([question, answer], index) => <AccordionItem key={question} value={`faq-${index}`}><AccordionTrigger className="py-6 text-base hover:no-underline">{question}</AccordionTrigger><AccordionContent className="pb-6 leading-relaxed text-muted-foreground">{answer}</AccordionContent></AccordionItem>)}</Accordion></div>
    </div>
  </div></main></PageShell>;
}