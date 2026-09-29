/**
 * The people shown on the About page and in the home page's team strip.
 *
 * To add a photo: save it in src/assets/people/ named after the person's `slug`
 * (e.g. joy-richman.jpg). It is picked up automatically - no import needed. A person without a
 * photo still appears on the About page (as an initial) but is left out of the home page strip.
 *
 * `quote` and `story` are shown only when set, and should be the person's own words - leave them
 * out rather than writing something for them.
 */

export type Person = {
  slug: string;
  name: string;
  role: string;
  group: "students" | "team";
  quote?: string;
  story?: string;
};

export const people: Person[] = [
  { slug: "joy-richman", name: "Joy Richman", role: "CEO", group: "students" },
  { slug: "leanonjah", name: "Leanonjah", role: "VP Production", group: "students" },
  { slug: "goodness", name: "Goodness", role: "VP Finance", group: "students" },
];

const photoModules = import.meta.glob("/src/assets/people/*.{jpg,jpeg,png,webp}", {
  eager: true,
  query: "?url",
  import: "default",
}) as Record<string, string>;

const photos = new Map<string, string>();
for (const [path, url] of Object.entries(photoModules)) {
  const file = path.split("/").pop() ?? "";
  photos.set(file.replace(/\.[^.]+$/, ""), url);
}

export function photoFor(person: Person): string | undefined {
  return photos.get(person.slug);
}

export const students = people.filter((person) => person.group === "students");
export const team = people.filter((person) => person.group === "team");
