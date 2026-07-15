# PDF Comparison Engine
## Processing Pipeline Documentation

---

# 1. Introduction

This document describes the complete execution pipeline of the PDF Comparison Engine.

Unlike the Architecture Documentation, which explains the purpose and responsibilities of each module, this document follows the life cycle of a document as it moves through the system.

Beginning with two input PDF files, every transformation is described until the final annotated PDF is produced.

The objective of this document is to explain:

- How information flows through the engine.
- How PDF data is transformed into logical representations.
- How the alignment process operates.
- How differences are generated.
- How annotations are rendered.

This document is intended primarily for developers working on the comparison engine.

---

# 2. End-to-End Processing Pipeline

At a high level, every comparison follows the pipeline shown below.

```

Input PDFs
↓
Unified PDF Extractor
↓
Logical Document Models
↓
Robust Logical Aligner
↓
Comparison Engine
↓
Difference Models
↓
Rendering Engine
↓
Annotated PDF

```

Each stage performs one transformation before passing structured information to the next component.

---

# 3. Stage 1 — Input Documents

The engine currently accepts two digital PDF documents.

```

Original Document

↓

Modified Document

```

Both documents are assumed to be digitally generated PDFs.

At the current milestone, scanned documents and OCR-based comparison are outside the scope of the comparison pipeline.

Future versions will introduce OCR support through a dedicated extraction layer.

---

# 4. Understanding PDF Documents

One of the most important architectural considerations is understanding that a PDF is **not** a text document.

Internally, a PDF stores graphical drawing instructions rather than semantic structures.

For example, the phrase

```

Policy Number

```

is not stored as a paragraph.

Instead, the PDF contains instructions similar to:

```

Draw glyph "P"
Position (x,y)

Draw glyph "o"
Position (x,y)

Draw glyph "l"
Position (x,y)

...

```

Each glyph is associated with formatting information including:

- Font
- Size
- Color
- Position
- Transformation matrix

Consequently, semantic structures such as paragraphs, headings, lists, or tables do not explicitly exist within the PDF itself.

The responsibility of reconstructing these logical structures falls entirely upon the comparison engine.

---

# 5. Stage 2 — Unified PDF Extraction

The Unified PDF Extractor is responsible for converting low-level PDF drawing instructions into structured logical representations.

Using PyMuPDF, the extractor traverses every page and extracts information in the following hierarchy.

```

Document
↓
Pages
↓
Blocks
↓
Lines
↓
Spans
↓
Words
↓
Characters

```

Every extracted element preserves both textual and visual metadata.

---

## Metadata Preserved

For every extracted object, the following information is retained whenever available.

### Textual Information

- Raw text
- Normalized text
- Character sequence

---

### Geometric Information

- Bounding box
- X coordinate
- Y coordinate
- Width
- Height

---

### Typography

- Font family
- Font size
- Font flags
- Font color

---

### Document Information

- Page number
- Reading order
- Parent hierarchy

This metadata becomes the foundation for all downstream processing.

---

# 6. Stage 3 — Logical Document Construction

Direct interaction with PyMuPDF objects is intentionally limited to the extraction stage.

Immediately after extraction, every object is converted into internal logical models.

The transformation is illustrated below.

```

PyMuPDF Objects
↓
Logical Models

```

This abstraction provides several important advantages.

- Library independence
- Easier debugging
- Improved testing
- Stable interfaces
- Cleaner architecture

---

## Logical Model Hierarchy

The current logical hierarchy is shown below.

```

LogicalDocument

└── LogicalPage
└── TextBlock
└── LogicalLine
└── LogicalWord
└── LogicalCharacter

```

These models become the canonical representation of the document for every remaining stage of the pipeline.

No subsequent module interacts directly with the PDF extraction library.

---

# 7. Data Flow After Extraction

At the completion of extraction, the comparison engine possesses a complete logical representation of both documents.

The pipeline at this stage is therefore:

```

Original PDF
↓
LogicalDocument A
↓
Modified PDF
↓
LogicalDocument B
```

These two LogicalDocument objects become the input to the Robust Logical Aligner, which is responsible for determining correspondence between document elements.

The aligner performs no comparison.

Its only responsibility is identifying which logical elements should be compared.

---

# 8. Stage 4 — Robust Logical Alignment

Once both documents have been extracted into their respective `LogicalDocument` representations, the next stage of the pipeline is responsible for establishing correspondence between the two documents.

Unlike traditional comparison engines that directly compare lines sequentially, this project performs logical alignment before any comparison takes place.

The objective of the aligner is **not** to determine differences between documents.

Its sole responsibility is to answer the following question:

> *"Which logical element in the original document corresponds to which logical element in the modified document?"*

The output of this stage forms the foundation for every downstream comparator.

---

# 9. Motivation

The original implementation relied on sequential line-by-line matching.

```
Original Document

Line 1
Line 2
Line 3
Line 4
Line 5
```

```
Modified Document

Line 1
Inserted Line
Line 2
Line 3
Line 4
Line 5
```

A traditional sequential aligner would produce:

```
Line 1  → Line 1 ✓

Line 2  → Inserted Line ✗

Line 3  → Line 2 ✗

Line 4  → Line 3 ✗

Line 5  → Line 4 ✗
```

Although only one line was inserted, every subsequent line became incorrectly aligned.

This phenomenon is known as **alignment drift** and was the primary source of false positives in the original comparison engine.

To eliminate this issue, the current implementation introduces a multi-stage logical alignment strategy.

---

# 10. Alignment Pipeline

The Robust Logical Aligner performs the following operations.

```
Logical Documents
        ↓
Extract Logical Lines
        ↓
Anchor Detection
        ↓
Anchor Sequence Alignment
        ↓
Logical Region Construction
        ↓
Region-wise Dynamic Programming
        ↓
LogicalAlignedPair Objects
```

Each stage progressively increases the confidence of the final alignment.

---

# 11. Logical Line Extraction

The aligner begins by flattening both documents into ordered collections of `LogicalLine` objects.

```
LogicalDocument
        ↓
Logical Pages
        ↓
Logical Lines
```

Each logical line contains:

- text
- page number
- bounding box
- formatting information
- logical words
- reading order

At this stage, no comparison has yet taken place.

---

# 12. Anchor Detection

Not every line contributes equally to document alignment.

Certain lines naturally serve as structural landmarks.

Examples include:

- document titles
- section headings
- chapter headings
- policy names
- table titles
- horizontal separators
- uniquely identifiable labels

These structurally significant lines are referred to as **anchors**.

The aligner evaluates every logical line and assigns an anchor confidence score based on multiple heuristics.

Typical heuristics include:

- text length
- capitalization
- uniqueness
- formatting prominence
- punctuation patterns
- numbering
- structural keywords

Only sufficiently strong candidates are promoted to anchors.

This dramatically reduces the search space while improving alignment robustness.

---

# 13. Anchor Sequence Alignment

Once anchors have been detected in both documents, the next objective is determining which anchors correspond to one another.

Unlike the original implementation, anchors are **not** matched greedily.

Instead, both anchor sequences are aligned using Dynamic Programming.

```
Original Anchors

A
B
C
D
E
↓
Dynamic Programming
↓
Modified Anchors

A
B
C
D
E
```

The algorithm evaluates the complete sequence rather than making local decisions.

This preserves the global ordering of the document and prevents incorrect matches caused by isolated insertions or deletions.

The output of this stage is an ordered collection of matched anchor pairs.

---

# 14. Logical Region Construction

Matched anchor pairs partition both documents into independent logical regions.

```
Anchor A
↓
Region 1
↓
Anchor B
↓
Region 2
↓
Anchor C
```

Each region represents the content bounded by two consecutive anchors.

Rather than aligning the entire document simultaneously, each region is treated as an independent alignment problem.

This design provides several advantages:

- localized recovery from errors
- improved alignment stability
- reduced computational complexity
- elimination of cascading alignment failures

Even if one region contains substantial edits, neighbouring regions remain unaffected.

---

# 15. Region-wise Dynamic Programming

Each logical region is aligned independently using a weighted Dynamic Programming algorithm.

For every pair of logical lines, the algorithm computes a similarity score using normalized textual similarity.

Possible operations include:

- Equal
- Replace
- Insert
- Delete

The algorithm constructs a Dynamic Programming matrix whose optimal path represents the best correspondence between both regions.

Unlike greedy alignment, Dynamic Programming evaluates all possible alignment paths before selecting the globally optimal solution.

This significantly improves robustness in documents containing:

- inserted paragraphs
- deleted sections
- paragraph reflow
- formatting modifications
- page layout changes

---

# 16. Traceback

Once the Dynamic Programming matrix has been completed, a traceback procedure reconstructs the optimal alignment path.

The traceback traverses the matrix from the final state back to the origin.

Each movement corresponds to one alignment operation.

```
Diagonal
↓
Equal / Replace
```

```
Up
↓
Delete
```

```
Left
↓
Insert
```

The recovered alignment sequence represents the most probable correspondence between logical lines.

---

# 17. Alignment Classification

Every recovered pair is assigned one of four alignment categories.

### EQUAL

Both logical lines correspond and contain sufficiently similar content.

---

### REPLACE

Both logical lines correspond but contain modified content.

---

### INSERT

A logical line exists only in the modified document.

---

### DELETE

A logical line exists only in the original document.

---

These alignment types allow downstream comparators to focus exclusively on relevant comparison scenarios.

For example:

- Formatting comparison is meaningful only for aligned pairs.
- Character comparison is meaningful only for replacement pairs.
- Insertion/Deletion comparison operates exclusively on inserted or deleted elements.

---

# 18. LogicalAlignedPair Generation

The final output of the alignment stage is an ordered sequence of `LogicalAlignedPair` objects.

Each object contains:

- Original logical line
- Modified logical line
- Alignment type
- Positional metadata

The sequence preserves the logical reading order of both documents while providing explicit correspondence between document elements.

This collection becomes the sole input to the Comparison Engine.

---

# 19. Advantages of the Robust Logical Aligner

Compared to traditional sequential line matching, the current aligner provides several improvements.

### Structural Awareness

Alignment is driven by document structure rather than physical position.

---

### Error Localization

Alignment mistakes remain confined to individual logical regions.

---

### Recovery after Insertions

Inserted or deleted content no longer causes the remainder of the document to become misaligned.

---

### Modular Design

Alignment remains completely independent from comparison logic.

This allows future improvements to either subsystem without affecting the other.

---

### Extensibility

Future versions can extend the aligner to support:

- paragraph-aware alignment
- semantic block alignment
- table-aware alignment
- OCR document alignment
- multilingual documents

without modifying the comparison engine.

---
# 20. Stage 5 — Comparison Engine

After logical alignment has been completed, the engine possesses a sequence of `LogicalAlignedPair` objects.

Each aligned pair represents two logical elements that have been determined to correspond to one another.

At this stage, no document differences have yet been identified.

The responsibility of the Comparison Engine is to analyze every aligned pair and determine **what has actually changed**.

Unlike the aligner, which establishes correspondence, the comparison engine classifies the nature of each modification.

---

# 21. Comparison Pipeline

The comparison process follows the pipeline below.

```
LogicalAlignedPairs
        ↓
Comparison Engine
        ↓
Comparator Dispatcher
        ↓
Character Comparator
Replace Comparator
Formatting Comparator
Number Comparator
Insertion / Deletion Comparator
        ↓
Difference Objects
```

Each comparator specializes in detecting one category of document change.

This modular design allows new comparison strategies to be introduced without modifying existing implementations.

---

# 22. Comparator Dispatcher

Rather than implementing one large comparison algorithm, the engine delegates comparison to specialized comparators.

Each aligned pair is examined independently.

Depending upon its alignment type, only the relevant comparators are executed.

Examples include:

### Equal

Possible formatting differences.

No insertion or deletion analysis.

---

### Replace

Character comparison

Word comparison

Number comparison

Formatting comparison

---

### Insert

Insertion comparator

---

### Delete

Deletion comparator

---

This selective execution significantly reduces unnecessary computation while keeping each comparator focused on a single responsibility.

---

# 23. Difference Detection

Whenever a comparator identifies a meaningful modification, it generates a `Difference` object.

Every detected difference follows a common structure regardless of its originating comparator.

The Difference model contains:

- Difference category
- Description
- Expected content
- Actual content
- Confidence score
- Original location
- Modified location
- Rendering metadata

This abstraction allows every downstream component to remain independent of the comparison logic.

---

# 24. Difference Categories

The current implementation supports the following categories.

### Character

Single-character or spelling modifications.

Example:

```
Policy
↓
Polciy
```

---

### Word

Word insertions, deletions, or replacements.

Example:

```
Policy Holder
↓
Customer
```

---

### Number

Numeric modifications.

Example:

```
5000
↓
6000
```

---

### Formatting

Visual formatting changes without textual modification.

Examples include:

- Font family
- Font size
- Text color

Future versions will additionally support:

- Bold
- Italic
- Underline
- Strikethrough

---

### Insert

Content appearing only in the modified document.

---

### Delete

Content removed from the original document.

---

# 25. Stage 6 — PDF Rendering

Once comparison has completed, the engine possesses a collection of Difference objects.

These objects are forwarded to the Rendering Engine.

The renderer performs no comparison.

Its sole responsibility is converting Difference objects into visual annotations.

```
Difference Objects
↓
Locate Bounding Boxes
↓
Generate Annotation
↓
Attach Metadata
↓
Annotated PDF
```

---

# 26. Rendering Strategy

Every Difference object contains sufficient positional information to determine its location inside the PDF.

Using this information, the renderer creates annotations preserving:

- Difference category
- Description
- Expected value
- Actual value

Visual annotations are overlaid onto a copy of the original PDF without modifying its underlying content.

This preserves document integrity while providing an intuitive review experience.

---

# 27. Stage 7 — Dashboard

The dashboard provides a lightweight graphical interface over the comparison pipeline.

Its responsibilities include:

- Accept user uploads.
- Execute the comparison pipeline.
- Display comparison statistics.
- Provide annotated PDF download.
- Present execution results.

Importantly, the dashboard contains no comparison logic.

All document processing remains encapsulated within the comparison engine.

This separation allows future deployment as:

- REST API
- Desktop application
- Microservice
- Cloud deployment

without architectural changes.

---

# 28. Complete Execution Flow

The complete execution pipeline can be summarized below.

```
Original PDF

Modified PDF
        │
        ▼
Unified PDF Extractor
        │
        ▼
Logical Documents
        │
        ▼
Robust Logical Aligner
        │
        ▼
LogicalAlignedPairs
        │
        ▼
Comparison Engine
        │
        ├──────────── Character Comparator
        ├──────────── Replace Comparator
        ├──────────── Formatting Comparator
        ├──────────── Number Comparator
        └──────────── Insert/Delete Comparator
        │
        ▼
Difference Objects
        │
        ▼
Rendering Engine
        │
        ▼
Annotated PDF
        │
        ▼
Dashboard Output
```

This pipeline represents the complete life cycle of every document processed by the comparison engine.

---

### Current Limitations

Despite substantial architectural improvements, several challenges remain before production deployment.

Current limitations include:

- Paragraph reflow still generates false positives.
- Tables are treated as ordinary text.
- Numbered lists require semantic understanding.
- Complex formatting changes are only partially detected.
- Semantic document structures are not yet reconstructed.

---
