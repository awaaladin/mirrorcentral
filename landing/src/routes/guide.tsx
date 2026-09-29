import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, Check, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageShell, StoreBadges } from "@/components/mirror-shell";

export const Route = createFileRoute("/guide")({ head: () => ({ meta: [
  { title: "How it works — mirror" },
  { name: "description", content: "A step-by-step guide to using mirror: create an account, import a portrait, pick shades, compare before and after, save looks and manage clients." },
  { property: "og:title", content: "How to use mirror" }, { property: "og:description", content: "From sign-up to a saved look, step by step." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" },
] }), component: GuidePage });

type Step = { title: string; body: string; points: string[]; note?: string };

const steps: Step[] = [
  {
    title: "Create your account",
    body: "Sign up with an email and password. At sign-up you also choose the kind of account you want, and that choice decides whether Client Mode is unlocked.",
    points: [
      "Personal: for your own looks. Saved looks, the full shade library and custom shades.",
      "Pro / MUA: everything in Personal, plus the Client Mode directory for bridal and editorial clients.",
      "Right after your first sign-up, a short walkthrough appears once. You will not see it again.",
    ],
    note: "The account type is set when you sign up. Upgrading later from inside the app is not available yet.",
  },
  {
    title: "Start on the Looks tab",
    body: "Looks is your home screen, with five tabs along the bottom: Looks, Studio, Library, Clients and Settings. At the top is a Self and Client switch. Client is for Pro accounts; on a Personal account it shows a Pro badge and explains what it unlocks.",
    points: [
      "IMPORT lets you choose a portrait from your phone. This is the button that works today.",
      "SIMULATE is the live camera mode. It is a Pro feature that is not released yet, so tapping it explains that instead of doing nothing.",
      "Below are your Recent Looks, with a search box for your saved looks.",
    ],
  },
  {
    title: "Choose a photo",
    body: "In the Studio, tap CHOOSE A PHOTO. mirror then reads the face on your phone. You will see “Detailing your photo…” while it maps the face, and nothing is uploaded to do this.",
    points: [
      "Use a photo with exactly one face, looking toward the camera, in even light.",
      "If there is no face, or more than one, mirror tells you so and lets you TRY AGAIN with another photo.",
      "The face mapping works without an internet connection.",
    ],
  },
  {
    title: "Pick a layer, then a shade",
    body: "Along the top of the shade panel are the layers: Lips, Foundation, Eyeshadow, Eye Color, Lashes, Blush and Brows. Choose one and the shade spectrum below shows its colours. Tap a swatch to apply it to your photo straight away.",
    points: [
      "The name and finish (matte, satin, glossy or shimmer) of the chosen shade appear beside the spectrum.",
      "Search a layer's shades by name, for example “brick” in Lips.",
      "Tap a selected swatch again, or press REMOVE, to take that layer off.",
      "Lashes work differently: you pick a style (Natural, Wispy, Dramatic or Doll eye) instead of a colour.",
      "Eye Color tints the iris and keeps the natural highlight.",
    ],
  },
  {
    title: "Tune it",
    body: "Each colour layer has its own Intensity slider, starting at a mild 50%, plus a Pigment Saturation slider. Layers are independent, so you can push the lips and keep the foundation light.",
    points: [
      "Drag the divider between the photo and the shade panel to give the photo more room.",
      "Missing a colour? Tap the + tile, name your shade, enter a hex code such as #B85C38 and press CREATE. It is kept on your phone and works on every account.",
    ],
  },
  {
    title: "Compare with the original",
    body: "Tap Split Diff to open the wipe comparison. Drag across the photo to reveal your untouched portrait on one side and the makeup as rendered on the other.",
    points: ["It compares against your real photo, not a filtered stand-in."],
  },
  {
    title: "Save the look",
    body: "Name the look (for example Bridal Glam) and press SAVE. It appears under Recent Looks on the Looks tab, with the photo, shades and lash style remembered.",
    points: [
      "Tap a saved look to reopen it in the Studio and keep editing.",
      "The ⋮ menu on each look has Edit and Delete. Simulate is listed too, but background removal and relighting are not built yet.",
    ],
  },
  {
    title: "Work with clients (Pro / MUA)",
    body: "The Clients tab is the Client Mode directory. Add a client with a name, notes such as undertone or wedding date, and a Self or Client tag. Search the list by name or notes, then START A LOOK IN THE STUDIO for that consultation.",
    points: ["On a Personal account, the Client Mode Directory shows a Pro badge and explains what Pro adds."],
  },
  {
    title: "Browse the full library",
    body: "The Library tab is the certified shade catalogue for every category, with search. It refreshes from mirror's servers, so new shades appear without an app update, and a copy is built into the app so it still works offline.",
    points: [],
  },
];

const soon = [
  ["Live camera simulation", "Try makeup on the camera feed, for Pro accounts."],
  ["Background clean-up and relighting", "Remove the background from a saved look and light it like a studio portrait."],
  ["Gele and head-wrap preview", "Built, but held back until it looks right."],
  ["Upgrade from inside the app", "Move from Personal to Pro without creating a new account."],
];

const tips = [
  ["One face per photo", "A group photo will be rejected. Crop first, or ask for a solo portrait."],
  ["Face the camera", "The face mesh is most accurate on straight-on portraits with the whole face in frame."],
  ["Even light", "Strong shadows across the face change how a shade reads. Daylight from the front works well."],
  ["Compare before you save", "Use Split Diff. It is the fastest way to catch a layer that is too heavy."],
];

function GuidePage() {
  return <PageShell><main className="px-5 pb-24 pt-36 sm:px-8 md:pt-44"><div className="mx-auto max-w-6xl">
    <header className="reveal-flow max-w-3xl"><p className="text-xs font-semibold uppercase text-primary">How it works</p><h1 className="mt-4 text-balance text-6xl leading-[.95] sm:text-7xl">From a portrait to a look you can keep.</h1><p className="mt-6 max-w-xl text-lg text-muted-foreground">Nine steps, in the order you will meet them in the app. Each screen and button below is named the way it appears on your phone.</p>
      <div className="mt-8 flex flex-wrap gap-3"><Button asChild className="h-12 rounded-full px-7"><a href="#steps">Start the guide <ArrowRight /></a></Button><Button asChild variant="outline" className="h-12 rounded-full px-7"><a href="#download">Download mirror</a></Button></div>
    </header>

    <div className="reveal-flow mt-16 grid grid-cols-2 gap-3 sm:grid-cols-5">{["Looks", "Studio", "Library", "Clients", "Settings"].map((tab) => <div key={tab} className="rounded-2xl border border-border bg-card px-4 py-4 text-center"><p className="font-display text-2xl">{tab}</p><p className="mt-1 text-[.7rem] uppercase text-muted-foreground">{{ Looks: "Recent looks", Studio: "Paint a look", Library: "All shades", Clients: "Pro only", Settings: "Account" }[tab]}</p></div>)}</div>

    <ol id="steps" className="mt-16 space-y-5 scroll-mt-28">{steps.map((step, index) => (
      <li key={step.title} className="reveal-flow grid gap-6 rounded-[2.5rem] border border-border bg-card p-7 sm:p-10 md:grid-cols-[5rem_1fr]">
        <span className="font-display text-6xl leading-none text-primary">{String(index + 1).padStart(2, "0")}</span>
        <div><h2 className="text-4xl leading-tight">{step.title}</h2><p className="mt-4 max-w-2xl leading-relaxed text-muted-foreground">{step.body}</p>
          {step.points.length > 0 && <ul className="mt-6 space-y-3">{step.points.map((point) => <li key={point} className="flex items-start gap-3 text-sm leading-relaxed"><span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-accent text-primary"><Check className="size-3.5" /></span>{point}</li>)}</ul>}
          {step.note && <p className="mt-6 rounded-2xl bg-muted px-5 py-4 text-sm text-muted-foreground">{step.note}</p>}
        </div>
      </li>))}
    </ol>

    <section className="mt-24 grid gap-12 md:grid-cols-2">
      <div className="reveal-flow"><p className="text-xs font-semibold uppercase text-primary">For a cleaner result</p><h2 className="mt-3 text-5xl leading-none">Small habits that help.</h2><dl className="mt-9 space-y-6">{tips.map(([title, copy]) => <div key={title}><dt className="font-display text-2xl">{title}</dt><dd className="mt-1 text-sm leading-relaxed text-muted-foreground">{copy}</dd></div>)}</dl></div>
      <div className="reveal-flow rounded-[2.5rem] bg-foreground p-8 text-background sm:p-10"><p className="text-xs font-semibold uppercase text-secondary">Still to come</p><h2 className="mt-3 text-4xl leading-none">Not in the app yet.</h2><p className="mt-4 text-sm text-background/60">We would rather tell you than let you hunt for a button.</p><ul className="mt-8 space-y-5">{soon.map(([title, copy]) => <li key={title} className="flex items-start gap-3"><Clock className="mt-1 size-4 shrink-0 text-secondary" /><div><p className="text-sm">{title}</p><p className="mt-0.5 text-xs leading-relaxed text-background/55">{copy}</p></div></li>)}</ul></div>
    </section>

    <section className="reveal-flow mt-24 flex flex-col items-center gap-6 rounded-[3rem] bg-accent p-10 text-center md:p-16"><h2 className="max-w-xl text-balance text-5xl leading-none">Ready to see a look on your own face?</h2><StoreBadges /><p className="text-sm text-muted-foreground">Questions or a studio rollout in mind? <Link to="/contact" className="underline underline-offset-4">Get in touch</Link>.</p></section>
  </div></main></PageShell>;
}
