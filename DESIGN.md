# Default lesson design

The user chose the visual style of [`9/gerund/index.html`](9/gerund/index.html) as the repository default. Use it for new pages and for pages being redesigned. Keep existing lesson behavior and teaching content when applying it to an older page.

## Visual language

- **Reading first.** A dark deep-teal introduction leads into a light, spacious lesson. Headings explain the topic directly. The opening breadcrumb provides context; there is no small uppercase kicker above the title.
- **Palette.** Use the tokens in [`assets/lesson-theme.css`](assets/lesson-theme.css): ink `#14243a`, deep teal `#10354b`, action teal `#075b79`, light canvas `#f3f7f6`, white paper, lime `#d7f58b`, pale teal examples, warm sand notes. Use green and red only for answer feedback.
- **Type and spacing.** Use a system sans at 16px/1.55. Large headings are tight and direct; body text stays readable on phones. Keep at least 16px inside cards and 8px inside bordered controls. Separate lesson sections with generous vertical space.
- **Components.** Use a breadcrumb, clear lesson title, simple metadata, a compact section navigation row, numbered section headings when sequence matters, white reading cards, lightly bordered examples, warm notes, and dark practice or test areas with white question cards. Buttons use teal; the primary action on a dark area may use lime.
- **Interaction.** Show a clear focus ring, keyboard-operable controls, feedback beside the answer, and a readable result. Respect reduced-motion preference. Content and controls must work at narrow mobile widths without horizontal page scrolling; wide tables may scroll inside their container.
- **Depth.** Use neutral shadows with a downward offset. Borders and surface color distinguish examples and notes without a thick side stripe.

## Implementation

Load `assets/lesson-theme.css` for design tokens. Use the gerund lesson as a visual reference and adapt its composition to the subject. Do not copy its exercise content or compress a complex lesson into its exact layout. For the existing Future Forms lesson, page-specific rules in the shared stylesheet are scoped to `body.future-lesson` so they do not change older lessons unexpectedly.
