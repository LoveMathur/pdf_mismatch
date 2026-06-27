# Architecture Document

## PDF Mismatch Detection Agent

---

# Purpose of this Document

This document describes the internal software architecture of the **PDF Mismatch Detection Agent**.

Unlike the README, which focuses on project overview and usage, this document explains the engineering decisions behind the implementation.

Its objectives are to

* document architectural decisions,
* explain data flow,
* describe module responsibilities,
* provide extension guidelines,
* assist future contributors,
* preserve implementation rationale.

This document should be considered the technical reference for the project.

---

# Architectural Vision

The objective of this project is **not simply to compare two PDF files**.

The objective is to build a **modular document intelligence framework** capable of understanding, comparing, and reporting differences across multiple document modalities.

Future supported document types include

* Digital PDFs
* OCR-generated documents
* Printed scanned documents
* Handwritten documents
* Image-rich PDFs
* Hybrid digital/OCR documents

The comparison engine itself should remain independent of the document source.

This principle drives almost every architectural decision in the project.

---

# Core Design Philosophy

The framework is built around five fundamental principles.

---

## 1. Separation of Responsibilities

Every module performs exactly one task.

Example

```text
DigitalPDFExtractor

↓

Extracts PDF content only.
```

It does **not**

* compare text,
* normalize content,
* generate reports,
* perform OCR.

Similarly,

```text
SequenceAligner
```

only establishes correspondence between documents.

It never determines whether two aligned lines are actually different.

This principle dramatically reduces coupling between components.

---

## 2. Immutable Processing Pipeline

Every processing stage creates a **new representation** instead of modifying existing objects.

Pipeline

```text
PDF

↓

Document

↓

TextElement[]

↓

AlignedPair[]

↓

Difference[]
```

Each stage remains unchanged after creation.

Advantages

* Easier debugging
* Better reproducibility
* Clear audit trail
* Independent testing
* Simpler reasoning

The original document always remains available.

---

## 3. Progressive Abstraction

The framework gradually transforms the document into increasingly abstract representations.

Example

```text
Raw PDF

↓

Structured Document

↓

Comparison Elements

↓

Alignment

↓

Differences

↓

Human Report
```

Every transformation removes complexity that is unnecessary for the next stage while preserving essential information.

---

## 4. Modular Intelligence

Rather than implementing one large comparison algorithm, intelligence is distributed across many specialized analyzers.

Example

```text
Character Analyzer

↓

Word Analyzer

↓

Whitespace Analyzer

↓

Formatting Analyzer
```

Each analyzer focuses on one category of document differences.

This significantly improves maintainability.

---

## 5. Explainability

Every detected mismatch should answer

* What changed?
* Where did it change?
* Why is it considered different?
* Which module detected it?

The framework prioritizes explainability over opaque scoring.

This is particularly important for enterprise document verification.

---

# High-Level Architecture

The entire framework follows a layered architecture.

```text
                        ┌─────────────────────┐
                        │     PDF Files       │
                        └──────────┬──────────┘
                                   │
                                   ▼
                    ┌─────────────────────────┐
                    │  Extraction Layer       │
                    └──────────┬──────────────┘
                               │
                               ▼
                    ┌─────────────────────────┐
                    │ Document Representation │
                    └──────────┬──────────────┘
                               │
                               ▼
                    ┌─────────────────────────┐
                    │ Transformation Layer    │
                    └──────────┬──────────────┘
                               │
                               ▼
                    ┌─────────────────────────┐
                    │ Alignment Layer         │
                    └──────────┬──────────────┘
                               │
                               ▼
                    ┌─────────────────────────┐
                    │ Comparison Framework    │
                    └──────────┬──────────────┘
                               │
                               ▼
                    ┌─────────────────────────┐
                    │ Difference Objects      │
                    └──────────┬──────────────┘
                               │
                               ▼
                    ┌─────────────────────────┐
                    │ Report Generation       │
                    └─────────────────────────┘
```

Each layer depends only on the layer immediately before it.

No layer directly accesses internal implementation details of another layer.

---

# Architectural Layers

The project consists of six primary layers.

---

## Layer 1 — Extraction

Responsibilities

* Read PDF files
* Parse document structure
* Preserve formatting
* Preserve positional information

Output

```text
Document
```

Modules

```text
extractors/
```

Future extensions

* OCR extractor
* Image extractor
* Table extractor

---

## Layer 2 — Representation

Responsibilities

Represent document content independently of extraction technology.

Objects

```text
Document

Page

TextBlock

Line

Span
```

This layer contains no comparison logic.

Its only responsibility is representing document structure.

---

## Layer 3 — Transformation

Responsibilities

Convert hierarchical structures into comparison-friendly representations.

Transformation

```text
Document

↓

TextElement[]
```

Advantages

* Faster traversal
* Simpler algorithms
* Easier testing
* Reduced complexity

---

## Layer 4 — Alignment

Responsibilities

Determine correspondence between two documents.

Transformation

```text
TextElement[]

↓

AlignedPair[]
```

Supported alignment

* Equal
* Replace
* Insert
* Delete

This layer solves document synchronization before any comparison occurs.

---

## Layer 5 — Comparison

Responsibilities

Analyze aligned content.

Current architecture

```text
Comparator

↓

Analyzer

↓

Difference
```

The comparison layer does **not** perform extraction or alignment.

It assumes those stages have already been completed.

---

## Layer 6 — Reporting

Responsibilities

Present detected differences.

Future outputs

* Console
* HTML
* JSON
* PDF
* REST API

Because every analyzer produces the same Difference model, reporting remains independent of comparison logic.

---

# End-to-End Data Flow

The following diagram illustrates the complete lifecycle of a document through the framework.

```text
PDF
 │
 ▼
DigitalPDFExtractor
 │
 ▼
Document
 │
 ▼
DocumentFlattener
 │
 ▼
TextElement[]
 │
 ▼
SequenceAligner
 │
 ▼
AlignedPair[]
 │
 ▼
Comparators
 │
 ▼
Analyzers
 │
 ▼
Difference[]
 │
 ▼
Report Generator
```

Notice that every stage consumes one representation and produces another.

This minimizes coupling between components.

---

# Project Package Responsibilities

Each package has a clearly defined responsibility.

---

## extractors/

Responsible for reading external document sources.

Current

```text
DigitalPDFExtractor
```

Future

* OCRExtractor
* ImageExtractor

---

## models/

Defines every shared data structure.

Examples

* Document
* Page
* TextBlock
* Line
* Span
* TextElement
* AlignedPair
* Difference

These classes are intentionally independent of business logic.

---

## utils/

Contains reusable infrastructure.

Current

* Flattener
* Sequence Alignment

Future

* Text similarity
* Geometry utilities
* OCR helpers
* Image utilities

Utilities should never contain comparison-specific logic.

---

## comparators/

Coordinates document comparison.

Responsibilities

* Traverse aligned pairs
* Delegate analysis
* Collect Difference objects

Comparators do not implement detailed comparison algorithms themselves.

---

## analyzers/

Contain the intelligence of the framework.

Each analyzer specializes in one comparison category.

Examples

* Character
* Word
* Spelling
* Formatting

Future analyzers

* Numbers
* Dates
* Currency
* Tables
* Images
* OCR

---

## output/

Stores generated reports.

Future outputs

* HTML
* JSON
* PDF

---

# Dependency Direction

The project follows one-way dependencies.

```text
Extractors

↓

Models

↓

Utilities

↓

Comparators

↓

Analyzers

↓

Reporting
```

Lower layers never depend on higher layers.

This significantly improves maintainability.

---

# Architectural Benefits

The chosen architecture provides several important advantages.

## Extensibility

New analyzers can be added without modifying existing modules.

---

## Maintainability

Small modules are easier to understand and test.

---

## Reusability

Intermediate representations can be reused by future pipelines.

---

## Testability

Every layer can be independently validated.

---

## Scalability

Future OCR, image comparison, semantic analysis, and AI integration require minimal architectural changes.

---

# Architectural Maturity

At the current stage of development, the system architecture is considered stable.

The core pipeline

```text
Extraction

↓

Transformation

↓

Alignment

↓

Comparison

↓

Reporting
```

is expected to remain unchanged throughout the remainder of development.

Future work will focus on increasing the intelligence of the comparison engine rather than redesigning the overall architecture.

This stability provides a solid foundation for implementing advanced analyzers, OCR support, image comparison, semantic reasoning, and enterprise-grade reporting in future iterations.

# Internal Data Architecture

The PDF Mismatch Detection Agent is fundamentally a **data transformation pipeline**.

Rather than comparing PDF files directly, the framework progressively transforms document information into increasingly specialized data structures.

Every transformation exists for a specific purpose.

This section documents every major object in the system, its responsibilities, lifecycle, and relationship to other components.

---

# Object Lifecycle

Every PDF processed by the framework follows the same lifecycle.

```text
PDF File
    │
    ▼
Document
    │
    ▼
Page
    │
    ▼
TextBlock
    │
    ▼
Line
    │
    ▼
Span
    │
    ▼
TextElement
    │
    ▼
AlignedPair
    │
    ▼
Difference
    │
    ▼
Report
```

Notice that every object has a shorter lifespan than the previous one.

Higher-level objects preserve document structure.

Lower-level objects simplify comparison.

---

# Layer 1 — Document Representation

The Document layer represents the source document exactly as it exists after extraction.

It is intentionally rich in information and closely mirrors the logical structure of the original PDF.

Hierarchy

```text
Document
│
├── Page
│     │
│     ├── TextBlock
│     │      │
│     │      ├── Line
│     │      │      │
│     │      │      ├── Span
```

No comparison logic exists at this layer.

---

# Document Object

Purpose

Represents one complete PDF document.

Responsibilities

* Store document metadata
* Preserve page ordering
* Act as the root object
* Own every page

Relationships

```text
Document

↓

Page[]
```

The Document object never stores comparison results.

Its responsibility ends immediately after flattening.

---

# Page Object

Purpose

Represents one physical page.

Responsibilities

* Store page number
* Store page dimensions
* Own text blocks
* Preserve page ordering

Relationships

```text
Page

↓

TextBlock[]
```

Future Extensions

* Images
* Tables
* Annotations
* Drawings
* OCR overlays

Pages intentionally remain independent of comparison logic.

---

# TextBlock Object

Purpose

Represent logical groups of text.

Examples

```text
Introduction

This paragraph...

↓

One TextBlock
```

Responsibilities

* Store block identifier
* Preserve block bounding box
* Store contained lines

Relationships

```text
TextBlock

↓

Line[]
```

Blocks improve readability while preserving paragraph structure.

---

# Line Object

Purpose

Represent one logical line of text.

Responsibilities

* Store line text
* Preserve line bounding box
* Store spans

Relationships

```text
Line

↓

Span[]
```

Unlike block-level coordinates, line-level bounding boxes enable highly accurate visual highlighting during report generation.

---

# Span Object

Purpose

Represent text sharing identical formatting.

Example

```text
Hello World
^^^^^ ^^^^^

Two spans
```

Responsibilities

Store

* text
* font
* font size
* color
* bounding box

Future metadata

* bold
* italic
* underline
* rotation
* opacity

Spans are primarily consumed by formatting analyzers.

---

# Why Preserve the Entire Hierarchy?

One possible design was to immediately convert every document into plain text.

Example

```text
PDF

↓

String
```

Although simple, this permanently discards valuable information.

Lost information includes

* formatting
* fonts
* colors
* alignment
* geometry
* page layout

Recovering this information later would be impossible.

Therefore the hierarchy remains intact until flattening.

---

# Layer 2 — Comparison Representation

The hierarchical document model is ideal for parsing.

It is not ideal for comparison.

Traversing multiple nested objects for every comparison operation would unnecessarily complicate later algorithms.

Therefore the framework introduces a second representation.

```text
Document

↓

TextElement[]
```

---

# TextElement

Purpose

Represent one comparison unit.

Current strategy

One logical line becomes one TextElement.

Responsibilities

Store

* unique identifier
* page number
* block number
* line number
* original text
* normalized text (future)
* bounding box

Example

```text
ID

17

Page

2

Block

5

Line

1

Text

Managers should approve leave requests.
```

The TextElement becomes the primary unit consumed by the alignment engine.

---

# Why Compare Lines?

Alternative considered

```text
Word[]

↓

Comparison
```

Problems

* larger datasets
* poor context
* harder alignment
* excessive object count

Current strategy

```text
Line

↓

TextElement
```

Word-level comparison still occurs later, but only after corresponding lines have been aligned.

---

# Layer 3 — Alignment Representation

After flattening, both documents exist as ordered sequences.

Example

```text
Document A

↓

TextElement[]
```

```text
Document B

↓

TextElement[]
```

These sequences are then synchronized.

Output

```text
AlignedPair[]
```

---

# AlignedPair

Purpose

Represent correspondence between two documents.

Each AlignedPair contains

* pair index
* left element
* right element
* alignment type

Alignment types

```text
EQUAL

REPLACE

INSERT

DELETE
```

Example

```text
LEFT

Manager

↓

RIGHT

Supervisor

↓

Alignment

REPLACE
```

---

# Why Introduce AlignedPair?

Without alignment, every comparison module would first need to determine whether two lines correspond.

This would duplicate identical logic across every analyzer.

Instead

```text
SequenceAligner

↓

AlignedPair
```

solves correspondence once.

Every analyzer benefits.

---

# Layer 4 — Difference Representation

Difference is the final internal representation before reporting.

Purpose

Represent one detected mismatch.

Current fields

* pair index
* difference category
* expected
* actual
* confidence

Future metadata

* character position
* word index
* page region
* similarity score
* analyzer identifier
* formatting attributes

The Difference object intentionally contains no presentation logic.

It is purely structured data.

---

# Why Separate Difference from Reporting?

One possible design

```text
Comparator

↓

Print
```

Problems

* impossible to reuse
* impossible to serialize
* impossible to build APIs
* impossible to generate multiple report formats

Current strategy

```text
Comparator

↓

Difference

↓

Report
```

Now

* HTML
* JSON
* CLI
* PDF

all consume exactly the same Difference objects.

---

# Object Ownership

Object ownership follows strict parent-child relationships.

```text
Document

owns

↓

Page
```

```text
Page

owns

↓

TextBlock
```

```text
TextBlock

owns

↓

Line
```

```text
Line

owns

↓

Span
```

After flattening

```text
TextElement
```

becomes an independent representation.

It does not own Line objects.

Instead it references the information required for comparison.

---

# Memory Strategy

The project intentionally duplicates small amounts of data to simplify downstream algorithms.

Example

Instead of repeatedly traversing

```text
Document

↓

Page

↓

Block

↓

Line
```

comparison modules directly receive

```text
TextElement
```

This trades minimal additional memory usage for significantly simpler code and faster execution.

---

# Immutable Transformations

Every transformation follows the same rule.

Never modify the previous representation.

Example

```text
Document

↓

TextElement
```

creates new objects.

The original Document remains untouched.

Likewise

```text
TextElement

↓

AlignedPair
```

creates another representation.

No stage mutates previous objects.

Benefits

* reproducibility
* debugging
* thread safety
* easier testing

---

# Data Transformation Philosophy

Every stage exists because each problem requires a different representation.

| Stage      | Representation             |
| ---------- | -------------------------- |
| Extraction | Document                   |
| Parsing    | Page / Block / Line / Span |
| Comparison | TextElement                |
| Alignment  | AlignedPair                |
| Reporting  | Difference                 |

Rather than forcing one object to solve every problem, the framework continuously transforms data into the representation best suited for the current stage.

This keeps individual algorithms simple while making the entire pipeline significantly easier to extend.

---

# Lifecycle Summary

The lifecycle of every document can therefore be summarized as

```text
PDF
 │
 ▼
Document
 │
 ▼
Page
 │
 ▼
TextBlock
 │
 ▼
Line
 │
 ▼
Span
 │
 ▼
TextElement
 │
 ▼
AlignedPair
 │
 ▼
Difference
 │
 ▼
Report
```

This progression from **rich document representation** to **minimal reporting objects** forms the backbone of the entire framework.

Every future feature—including OCR, image comparison, semantic analysis, layout analysis, and AI-assisted validation—will build upon this lifecycle without requiring changes to the existing object model.

# Comparison Engine Architecture

The Comparison Engine is the core intelligence of the PDF Mismatch Detection Agent.

Its responsibility is **not** to determine document correspondence. That responsibility has already been completed by the Sequence Alignment layer.

Instead, the Comparison Engine analyzes already aligned document elements and classifies every detected mismatch into meaningful categories.

Input

```text
AlignedPair[]
```

Output

```text
Difference[]
```

The Comparison Engine is intentionally designed as a modular framework rather than a single comparison algorithm.

---

# Comparison Pipeline

The complete comparison workflow is illustrated below.

```text
AlignedPair[]
        │
        ▼
InsertionDeletionComparator
        │
        ▼
ReplaceComparator
        │
        ▼
Character Analyzer
Word Analyzer
Case Analyzer
Whitespace Analyzer
Spelling Analyzer
Formatting Analyzer
Semantic Analyzer
        │
        ▼
Difference[]
        │
        ▼
Report Generator
```

Notice that every stage performs one highly specialized task.

---

# Comparator Architecture

Comparators operate on an entire aligned document.

Responsibilities

* Traverse aligned pairs
* Filter relevant alignment types
* Dispatch work to analyzers
* Collect Difference objects

Comparators intentionally contain almost no business logic.

Instead, they coordinate the comparison process.

Current comparators

```text
BaseComparator

↓

InsertionDeletionComparator

↓

ReplaceComparator
```

Future comparators may include

* TableComparator
* ImageComparator
* MetadataComparator
* AnnotationComparator

---

# Why Separate Comparators and Analyzers?

One possible architecture was

```text
CharacterComparator

↓

Entire Document
```

WordComparator

↓

Entire Document

This would require every comparator to repeatedly iterate through the document and determine which aligned pairs should be analyzed.

Instead

```text
ReplaceComparator

↓

CharacterAnalyzer

↓

WordAnalyzer

↓

FormattingAnalyzer
```

The filtering occurs only once.

Benefits

* Less duplicated code
* Better maintainability
* Easier testing
* Cleaner extension points

---

# Analyzer Architecture

Analyzers perform the actual comparison.

Responsibilities

* Inspect one aligned pair
* Detect one category of differences
* Produce Difference objects

Input

```text
AlignedPair
```

Output

```text
Difference[]
```

Every analyzer specializes in one comparison domain.

Current architecture

```text
Character Analyzer

Word Analyzer

Case Analyzer

Whitespace Analyzer

Spelling Analyzer

Formatting Analyzer
```

Future analyzers

```text
Number Analyzer

Date Analyzer

Currency Analyzer

Header Analyzer

Footer Analyzer

Table Analyzer

Image Text Analyzer

OCR Confidence Analyzer

Semantic Analyzer
```

This modular structure allows new analyzers to be added without modifying existing ones.

---

# Sequence Alignment Strategy

The alignment layer is one of the most important architectural components.

Purpose

Determine correspondence between two documents before comparison begins.

Without alignment

```text
Document A

A

B

C

D
```

Document B

```text
A

X

B

C

D
```

Naive comparison

```text
A = A

B ≠ X

C ≠ B

D ≠ C
```

Every remaining line becomes mismatched.

Current strategy

```text
Sequence Alignment

↓

AlignedPair
```

Result

```text
A = A

—

↓

X

B = B

C = C

D = D
```

Only one insertion is detected.

This significantly improves comparison accuracy.

---

# Difference Generation

Every analyzer produces standardized Difference objects.

Example

```text
Difference

↓

Type

Character

↓

Expected

1024

↓

Actual

1025
```

The reporting layer never interacts directly with analyzers.

Instead

```text
Analyzer

↓

Difference

↓

Report
```

This separation makes reporting technology-independent.

---

# Report Generator Architecture

The reporting layer converts Difference objects into human-readable outputs.

Planned architecture

```text
Difference[]

↓

Report Builder

↓

Formatter

↓

Output
```

Supported outputs

```text
Console

JSON

HTML

PDF

REST API
```

Future report generators can be implemented without modifying comparison logic.

---

# OCR Integration Strategy

A major design objective is supporting scanned PDFs without redesigning the comparison engine.

Planned workflow

```text
Scanned PDF

↓

Image Extraction

↓

OCR Engine

↓

Document Reconstruction

↓

Document

↓

Existing Pipeline
```

Notice that OCR simply becomes another extractor.

Everything after Document remains identical.

Advantages

* Shared pipeline
* Minimal duplicated code
* Consistent Difference objects
* Simplified testing

---

# Image Comparison Architecture

Future versions will compare images independently of text.

Pipeline

```text
PDF

↓

Extract Images

↓

Image Matching

↓

OCR (optional)

↓

Image Analyzer

↓

Difference[]
```

Planned capabilities

* Missing images
* Modified images
* OCR from embedded images
* Logo verification
* Signature comparison
* Diagram comparison

Image analyzers will integrate with the same reporting framework used by text analyzers.

---

# Extension Guide

One of the primary design goals of this project is extensibility.

Adding a new analyzer requires only four steps.

---

## Step 1

Create a new analyzer.

Example

```text
CurrencyAnalyzer
```

---

## Step 2

Implement

```python
analyze(pair)
```

---

## Step 3

Return Difference objects.

---

## Step 4

Register the analyzer inside ReplaceComparator.

No other module requires modification.

This follows the Open/Closed Principle.

---

# Design Patterns

The framework intentionally incorporates several well-established software design patterns.

---

## Pipeline Pattern

Every processing stage produces input for the next.

```text
Extraction

↓

Transformation

↓

Alignment

↓

Comparison

↓

Reporting
```

---

## Composite Pattern

The document hierarchy forms a natural tree.

```text
Document

↓

Page

↓

TextBlock

↓

Line

↓

Span
```

Each level owns the level beneath it.

---

## Strategy Pattern

Different analyzers implement different comparison strategies.

Examples

* Character strategy
* Word strategy
* Formatting strategy

All share a common interface.

---

## Factory Pattern (Future)

Future extractors

```text
Digital PDF

↓

OCR

↓

Image
```

can be instantiated through a common factory.

---

## Adapter Pattern (Future)

External AI services

OCR engines

Language models

Embedding models

can be integrated through adapters without changing internal logic.

---

# Performance Considerations

The current implementation prioritizes correctness over optimization.

Future optimizations include

* Parallel page extraction
* Lazy loading
* Cached similarity calculations
* Concurrent analyzers
* OCR batching
* Incremental document comparison

Performance improvements will be implemented only after feature completeness.

---

# AI Integration Roadmap

Although the current implementation primarily relies on deterministic algorithms, the architecture has been designed to accommodate AI-assisted analysis.

Potential future integrations include

### OCR

Printed documents

Handwritten documents

---

### Semantic Analysis

Sentence embeddings

Meaning preservation

Paraphrase detection

---

### LLM Validation

Explain detected differences

Summarize reports

Classify document changes

Generate executive summaries

---

### Vision Models

Image similarity

Diagram comparison

Signature validation

Stamp detection

---

# Scalability Considerations

The framework is expected to evolve beyond simple PDF comparison.

Potential enterprise features include

* Batch document comparison
* Cloud deployment
* REST APIs
* Database integration
* User authentication
* Audit logs
* Version tracking
* Enterprise dashboards

The current architecture intentionally isolates business logic from infrastructure to simplify future expansion.

---

# Architectural Summary

The PDF Mismatch Detection Agent has been designed as a layered, modular, and extensible document intelligence framework.

Rather than implementing a monolithic comparison algorithm, the project separates extraction, transformation, alignment, comparison, and reporting into independent layers connected through standardized intermediate representations.

Key architectural characteristics include

* Immutable data transformations
* Layered architecture
* Modular analyzers
* Reusable comparison pipeline
* Technology-independent reporting
* OCR-ready design
* AI-ready extension points
* Standardized Difference model

This architecture enables the framework to evolve from a digital PDF comparison utility into a comprehensive document intelligence platform capable of supporting OCR, image analysis, semantic comparison, and enterprise-scale document verification workflows without requiring major structural redesign.
