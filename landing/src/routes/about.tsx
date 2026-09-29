import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, Quote } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageShell } from "@/components/mirror-shell";
import { lashStyles, shadeCount } from "@/lib/shades";
import { photoFor, students, team, type Person } from "@/lib/people";

export const Route = createFileRoute("/about")({ head: () => ({ meta: [
  { title: "About — mirror" },
  { name: "description", content: "The students and team behind mirror, a makeup simulator shaped for Nigerian beauty and professional artistry." },
  { property: "og:title", content: "About mirror" }, { property: "og:description", content: "Meet the students and team behind mirror." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" },
] }), component: AboutPage });

const facts = [
  ["468", "face points mapped on the phone"],
  [String(shadeCount), "shades with real finishes"],
  [String(lashStyles.length), "lash styles"],
  ["2", "account types: Personal and Pro / MUA"],
] as const;

function AboutPage() {
  return <PageShell><main className="px-5 pb-24 pt-36 sm:px-8 md:pt-44"><div className="mx-auto max-w-6xl">
    <header className="reveal-flow max-w-4xl"><p className="text-xs font-semibold uppercase text-primary">About mirror</p><h1 className="mt-4 text-balance text-6xl leading-[.95] sm:text-7xl lg:text-8xl">A young team, a <em className="text-primary">real</em> product.</h1><p className="mt-7 max-w-2xl text-lg leading-relaxed text-muted-foreground">mirror began as a student company idea from a team preparing for the Junior Achievement Nigeria state competition: makeup simulation made for Nigerian women and the artists who make them up. It has since become a working Android app with its own servers, an admin console and a shade library.</p></header>

    <section className="reveal-flow mt-20 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{facts.map(([figure, label]) => <div key={label} className="rounded-[2rem] border border-border bg-card p-7"><p className="font-display text-6xl leading-none text-primary">{figure}</p><p className="mt-3 text-sm text-muted-foreground">{label}</p></div>)}</section>

    <section className="mt-24 grid gap-10 md:grid-cols-[.8fr_1.2fr]">
      <div className="reveal-flow"><p className="text-xs font-semibold uppercase text-primary">The idea</p><h2 className="mt-3 text-5xl leading-none">Makeup that starts from our skin tones.</h2></div>
      <div className="reveal-flow space-y-5 leading-relaxed text-muted-foreground">
        <p>Makeup simulation can look ashy or muddy on deep skin tones. mirror's shade library is written for deep skin tones first, with names people actually say, such as brick red, oxblood, terracotta and warm cocoa, and a foundation range that still stretches from fair to the deepest ebony.</p>
        <p>The app maps the face on the phone, so a portrait never has to leave the device to be tried on. Makeup artists get a Client Mode directory for bridal and editorial consultations, and the same account keeps their saved looks.</p>
        <p>The idea came from the students below. It was refined and built into the working app and the systems behind it.</p>
      </div>
    </section>

    <PeopleSection eyebrow="The students" title="The founding team." people={students} />
    {team.length > 0 && <PeopleSection eyebrow="The wider team" title="The people who made it possible." people={team} />}

    <section className="reveal-flow mt-24 grid gap-8 rounded-[3rem] bg-foreground p-8 text-background md:grid-cols-[1fr_auto] md:items-center md:p-14"><div><p className="text-xs font-semibold uppercase text-secondary">See what they made</p><h2 className="mt-3 max-w-xl text-5xl leading-none">Learn how to use mirror, step by step.</h2></div><div className="flex flex-wrap gap-3"><Button asChild variant="secondary" className="h-12 rounded-full px-7"><Link to="/guide">How it works <ArrowRight /></Link></Button><Button asChild variant="ghost" className="h-12 rounded-full px-7 text-background hover:text-foreground"><Link to="/contact">Get in touch</Link></Button></div></section>
  </div></main></PageShell>;
}

function PeopleSection({ eyebrow, title, people }: { eyebrow: string; title: string; people: Person[] }) {
  if (people.length === 0) return null;
  return <section className="mt-24">
    <div className="reveal-flow max-w-2xl"><p className="text-xs font-semibold uppercase text-primary">{eyebrow}</p><h2 className="mt-3 text-5xl leading-none sm:text-6xl">{title}</h2></div>
    <div className="mt-12 grid gap-x-6 gap-y-14 sm:grid-cols-2 lg:grid-cols-3">{people.map((person) => <PersonCard key={person.slug} person={person} />)}</div>
  </section>;
}

function PersonCard({ person }: { person: Person }) {
  const photo = photoFor(person);
  return <article id={person.slug} className="reveal-flow scroll-mt-28">
    <div className="aspect-[3/4] overflow-hidden rounded-[2rem] bg-accent">{photo ? <img src={photo} alt={`${person.name}, ${person.role}`} loading="lazy" className="size-full object-cover" /> : <div className="grid size-full place-items-center font-display text-8xl text-primary/60" aria-hidden="true">{person.name.charAt(0)}</div>}</div>
    <p className="mt-5 text-xs font-semibold uppercase text-primary">{person.role}</p>
    <h3 className="mt-1 text-4xl leading-tight">{person.name}</h3>
    {person.quote && <blockquote className="mt-4 flex gap-3 text-sm leading-relaxed text-muted-foreground"><Quote className="mt-0.5 size-4 shrink-0 text-primary" /><p>{person.quote}</p></blockquote>}
    {person.story && <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{person.story}</p>}
  </article>;
}
