# The presentation deck

## Build it with the `slides` skill

Invoke the `slides` skill and follow it: PptxGenJS authoring, its layout helpers, and its render, overflow and
font checks. Hand it a deck brief and say what goes on each slide:
- the slide list with titles, the message of each slide, the figures and numbers it shows, and its presenter;
- the theme fonts and colors;
- the figure files.

If `slides` is not available in this agent, use the `pptx` skill, or PptxGenJS directly, with the same render
and overflow checks.

Deliver `presentation.pptx` and `presentation.pdf`. The PDF is exported from the same deck, for example with
`soffice --headless --convert-to pdf`. Keep the deck's source `.js` and assets in `deliverables/slides/`, so the
deck can be rebuilt.

## What a good deck here looks like

**Audience.** It must work for listeners who have never seen the project. It is academic, but it never drowns in
technical detail.

**Order.** It moves top-down, from the big picture to the details:
1. the problem and why it matters;
2. the idea and the overall architecture;
3. the components or methods, grouped into a few families rather than listed one by one;
4. how the work was evaluated;
5. the results;
6. what they mean, and the limitations;
7. the conclusion;
8. the demo, if there is one, then questions.

**Language and layout.**
- Use simple but academic language and one message per slide.
- Prefer a figure or diagram to bullet text.
- Keep the type large enough to read in a video or from the back of a room.

**Length.** Fit the slide count to the talk length and the share of time the demo takes. About one content slide
per minute of talk is a reasonable start; adjust it to the material.

**Agreement with the report.** Every number, name and claim comes from the fact sheet and agrees with the report.
Re-render the report's figures at slide resolution instead of screenshotting the PDF, from the same scripts at
slide size (`figures.md`). A deck for an interim or proposal report covers that report's scope only.

**Team decks.**
- Group the slides by presenter in talk order, and mark who presents each part the way the user prefers, for
  example a small name tag or a section divider.
- A short "who did what" slide and a technology slide are common course expectations. Include them when the user
  asks, or when the course material suggests it.

**Speaker notes** are optional. If you add them, they follow the same voice rule as the report: no word about how
the deck was made.

## Check before delivering

Look at every rendered slide: no overflow, no overlapping elements, no substituted fonts, readable charts,
consistent styling. Then check the PDF the same way. The study documents' scripts refer to slide numbers and
titles, so finish the deck before writing them.
