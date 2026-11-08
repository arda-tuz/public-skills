# Story mode: one structure for every deliverable

Read this file only when story mode is on, and only once per project: to derive `notes/story.md`. After that, every
deliverable reads `notes/story.md`, never this file again.

## Why it matters

A report that lists facts, hypotheses and results side by side reads as a pile of independent pieces. The audience
cannot place them, asks scattered or overly detailed questions, and concludes that the author has not understood the
work. Someone who has understood a project can split it into a few categories and explain it from the big picture down
to the details. For each category, they can say:
- what was aimed for and what was not;
- what was achieved and what was not;
- which evidence shows it.

Story mode gives every deliverable that structure.

**What it is not:**
- No narrative tone, no anecdotes, and no TED-talk register. The academic, technical voice stays.
- Nothing is rewritten from scratch. Existing text is reordered and regrouped, gets lead sentences and new headings, and
  is cut where it repeats.
- No claim, number or limitation changes. The fact sheet stays the only source.

## Deriving the story (once)

Work from `notes/facts.md`, not from memory.

1. **Find the big picture.** One sentence: the problem, and what the project does about it.
2. **Find the natural partition.**
   - Two to four categories that together cover the work. Prefer what the project already has: its halves, modules,
     layers or phases. A partition the system's architecture already shows is easiest to follow.
   - Each result belongs to exactly one category.
   - Cross-cutting material (the delivered system, cost, method) goes in a closing category, or stays where the report
     kind puts it.
3. **For each category, write:**
   - goal and non-goal;
   - what was achieved;
   - what was not achieved;
   - the evidence, with the deciding numbers and their sources.

   An honest "not achieved" belongs to the story; it is often what the audience remembers as credibility.
4. **Write the spine.**
   - One sentence per category, two to four in all, each a claim with its key number.
   - A closing cross-cutting category (the delivered system, cost) needs no spine sentence of its own.
   - Order the categories as the argument builds, usually from the expected result to the new one.
   - The spine is what the audience should be able to repeat after the talk.
5. **Order from big picture to detail.** Spine first, then categories, then each category's evidence. Within an
   evidence item, the simple version comes before the full one.
6. **Check the story against the facts.** Every spine claim is defensible as written. Every category has a "not
   achieved" line, even if it is "nothing in scope"; a closing cross-cutting category may state its limits inline instead.

## `notes/story.md`

It must stand on its own: a later run, or a later deliverable in this run, reads only this file to apply the story.
Keep it under about 80 lines.

```markdown
# Story (derived <date> from facts.md)

## Spine
1. <category 1 claim with its key number>
2. <category 2 claim>
3. <category 3 claim>

## Big picture
<one sentence: the problem and what the project does>

## Categories
### 1. <name>: <claim>
- Goal / non-goal:
- Achieved: <result, number, source>
- Not achieved:
- Evidence order (simple to full):
...

## Applying this story
- Report: <section order, which results go under which category, what the abstract and conclusion restate>
- Deck: <slide order by category>
- Study documents: <same categories; questions grouped by category>
- Terms: <the names used everywhere>
```

The "Applying this story" block is part of the derivation. Fill it for the deliverables the user asked for, using the
rules below.

## Applying it

**Report** (`latex-report.md`):
- **Abstract.** The problem, then the spine claims in spine order, each with its number, then the limits.
- **Introduction.**
  - It ends with the big picture and the spine, as a short list or one paragraph.
  - Objectives and contributions are mapped onto the categories.
- **Approach and outcomes.** Both are grouped by category.
  - Each outcome category opens with one lead sentence: its claim.
  - Then its evidence, then what it did not achieve.
  - Research questions stay labeled, but they sit under their category instead of in RQ order.
- **Lessons learned.** Grouped by category where they fit.
- **Conclusion.** Restates the spine in the same order, with the same numbers.
- **Headings.** They may carry the claim ("Gate: parity, not superiority"), as long as they stay short and factual.

**Deck** (`slides.md`):
- Slide 1 after the title states the big picture and the spine.
- One section per category: claim, evidence, what was not achieved.
- The closing slide repeats the spine. Speaker notes follow the same order.

**Study documents** (`study-documents.md`):
- The same categories, so the presenter explains the project in the order the deck uses.
- Likely questions are grouped by category, and each answer starts from the category's claim.

**Demo material.** Each scene names the category it proves. A category with no scene is listed as a gap.

## Turning it off or on

- **Off.** Leave existing deliverables as they are. Later deliverables follow the normal structure.
- **On again.** Reuse `notes/story.md` if the facts have not changed. Derive it again only when they have.
