# Unit dependence probe: completion instructions

Read the claim under assessment and the whole document that follows it, then complete the form.

1. Output a single JSON object containing exactly the keys defined by the form schema, and no other text.
2. `follows` is follows when the claim under assessment is a consequence of the document's commitments and definitions as written, does_not_follow when the document as written does not yield it or contradicts it, and not_determined when the document as written leaves it open.
3. `essential` lists the named commitments and defined terms on which the claim depends essentially, so that the claim would not follow from the document without them; it may be empty.
