# PDF Mismatch Detection Agent

> **An AI-assisted modular document comparison framework capable of detecting textual, structural, formatting, OCR, and image-based differences between PDF documents.**

---

# Overview

The **PDF Mismatch Detection Agent** is a modular document analysis framework designed to compare two PDF documents and generate an explainable report of every detected mismatch.

Unlike conventional text-diff tools that compare plain text line by line, this project aims to understand the structure of a document before performing any comparison. Every PDF is first converted into a structured representation, preserving pages, text blocks, lines, spans, formatting metadata, and positional information. Only after this structured representation is built does the comparison process begin.

The architecture is intentionally divided into independent stages so that new comparison capabilities—such as OCR support, image comparison, semantic similarity, or formatting analysis—can be added without modifying the existing pipeline.

The project follows a **pipeline architecture**, where each stage performs one well-defined task and produces a standardized output for the next stage.

---

# Project Goals

The primary objective is to develop a production-ready document comparison framework capable of accurately identifying differences across multiple dimensions of a PDF document.

The system is designed to support both digital and scanned documents while remaining extensible for future AI-based comparison techniques.

Current and planned capabilities include:

### Text Comparison

* Character-level differences
* Word-level differences
* Sentence insertion and deletion
* Paragraph insertion and deletion
* Case sensitivity differences
* Hidden Unicode character detection
* Whitespace inconsistencies
* Typographical errors
* Spelling variations

---

### Formatting Comparison

* Font family changes
* Font size differences
* Font color differences
* Bold / Italic / Underline detection
* Text alignment
* Paragraph spacing
* Margin changes
* Layout inconsistencies

---

### OCR & Scanned Documents

* Printed scanned PDFs
* OCR-generated text comparison
* Noise-tolerant alignment
* OCR confidence integration
* Future handwritten document support

---

### Image Analysis

* Missing images
* Modified images
* Image similarity detection
* OCR extraction from embedded images
* Image text comparison

---

### Report Generation

The framework is designed to generate multiple report formats:

* Console output
* JSON
* HTML
* PDF summary
* Visual difference highlighting
* Machine-readable API responses

---

# Design Philosophy

This project is built around a few core software engineering principles.

## 1. Separation of Responsibilities

Each module has exactly one responsibility.

For example:

* Extractors only parse documents.
* Flatteners only transform document structures.
* Aligners only establish correspondence between documents.
* Comparators only identify differences.
* Report generators only present results.

No component performs the responsibility of another.

---

## 2. Immutable Extraction

The original document representation is never modified.

Instead of altering extracted text, later stages create additional representations while preserving the original content.

Example:

```text
Original Text

↓

Please   review

↓

Normalized Representation

↓

Please review
```

The original document remains untouched throughout the pipeline.

---

## 3. Modular Architecture

Every major stage is independent.

Future modules such as OCR, semantic comparison, or image analysis can be introduced without redesigning the existing pipeline.

This makes the framework highly extensible and easier to maintain.

---

## 4. Explainable AI

The system does not simply state that two documents are different.

Instead, every detected mismatch should answer:

* What changed?
* Where did it change?
* Why is it considered different?
* Which comparison module detected it?

This makes the comparison process transparent and suitable for auditing.

---

# High-Level Architecture

The current architecture follows the pipeline shown below.

```text
                         PDF Documents
                               │
                               ▼
                    Digital PDF Extractor
                               │
                               ▼
                          Document Model
                               │
                               ▼
                      Document Flattener
                               │
                               ▼
                        TextElement[]
                               │
                               ▼
                      Sequence Alignment
                               │
                               ▼
                        AlignedPair[]
                               │
                               ▼
                    Comparison Framework
                               │
      ┌────────────────────────┼────────────────────────┐
      │                        │                        │
      ▼                        ▼                        ▼
Insertion / Deletion    Replacement Dispatcher     Future Modules
      │                        │
      │                        ▼
      │               Character Analyzer
      │               Word Analyzer
      │               Case Analyzer
      │               Whitespace Analyzer
      │               Spelling Analyzer
      │               Formatting Analyzer
      │               Semantic Analyzer
      │
      └────────────────────────┬────────────────────────┘
                               ▼
                         Difference[]
                               │
                               ▼
                      Report Generation
```

Each stage produces a standardized output that becomes the input of the next stage.

---

# Current Project Structure

```text
pdf_mismatch/

├── comparators/
│   ├── analyzers/
│   │   ├── base_analyzer.py
│   │   ├── character.py
│   │   ├── word.py
│   │   ├── whitespace.py
│   │   ├── case.py
│   │   ├── spelling.py
│   │   └── formatting.py
│   │
│   ├── base.py
│   ├── insertion_deletion.py
│   ├── replace.py
│   └── text.py
│
├── data/
│   ├── document_A.pdf
│   ├── document_B.pdf
│   ├── document_C.pdf
│   └── document_D.pdf
│
├── extractors/
│   └── digital.py
│
├── models/
│   ├── aligned_pair.py
│   ├── difference.py
│   ├── document.py
│   ├── line.py
│   ├── page.py
│   ├── span.py
│   ├── text_block.py
│   └── text_element.py
│
├── output/
│
├── utils/
│   ├── flattener.py
│   ├── sequence_alignment.py
│   └── text_similarity.py (planned)
│
├── main.py
├── README.md
├── ARCHITECTURE.md
├── PROGRESS.md
└── requirements.txt
```

---

# Why This Architecture?

Traditional PDF comparison tools usually perform direct text comparisons after extracting raw text.

That approach struggles when:

* paragraphs move,
* sentences are inserted,
* OCR introduces noise,
* formatting changes without textual modifications,
* images contain important text.

Instead, this project transforms every PDF into a structured representation before performing any comparison.

This provides several advantages:

* Accurate document alignment
* Better formatting preservation
* Easier OCR integration
* Reusable comparison modules
* Improved report generation
* Cleaner software architecture

The comparison engine therefore operates on structured document objects rather than raw PDF files.

---

# Current Development Status

The project has successfully completed the foundation of the document processing pipeline.

### Completed

* Digital PDF extraction
* Structured document models
* Text hierarchy preservation
* Bounding box preservation
* Document flattening
* Sequence alignment
* Difference model
* Comparator framework
* Insertion / Deletion comparator

### Currently Under Development

* Replacement comparison framework
* Character analyzer
* Word analyzer
* Case analyzer
* Whitespace analyzer
* Spelling analyzer

These modules will form the core intelligence responsible for classifying textual differences.

# Document Processing Pipeline

The PDF Mismatch Detection Agent does **not** compare PDF files directly.

Instead, every document passes through a series of transformation stages that gradually convert an unstructured PDF into structured comparison objects. Each stage has a single responsibility and produces a standardized output for the next stage.

The complete processing pipeline is shown below.

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
Comparison Framework
 │
 ▼
Difference[]
 │
 ▼
Report Generator
```

This staged architecture makes the comparison engine independent of the original document source. Whether the input is a digital PDF, a scanned PDF, or OCR output, the downstream comparison pipeline remains unchanged.

---

# Document Parsing

The first stage of the pipeline converts the PDF into a structured object hierarchy.

Instead of extracting plain text, the parser preserves the logical structure of the document.

The hierarchy is represented as:

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

This hierarchy closely mirrors the internal representation returned by PyMuPDF while remaining independent of the extraction library.

---

# Document Model

The `Document` object represents an entire PDF.

Responsibilities:

* Store all document pages
* Preserve page order
* Act as the root object for the parsing pipeline

The Document model does not contain comparison logic. It is purely a structured representation of the source PDF.

---

# Page Model

Each Page represents one physical page inside the document.

Responsibilities

* Store page number
* Preserve page dimensions
* Store text blocks
* Maintain page ordering

Pages are intentionally independent from comparison logic so they can later support image extraction, annotations, tables, and OCR overlays.

---

# TextBlock Model

A TextBlock represents a logical paragraph or grouped text region.

Responsibilities

* Store block number
* Preserve block bounding box
* Store all contained lines
* Provide reconstructed block text

Blocks preserve the original reading order of the document.

---

# Line Model

The Line model represents one logical line of text.

Responsibilities

* Store line bounding box
* Store spans
* Reconstruct line text

Unlike block-level coordinates, every line maintains its own bounding box.

This allows future visual reports to highlight the exact location of detected differences.

Example:

```text
Expected

Managers should approve requests.

↓

Actual

Supervisors should approve requests.
```

The report generator will later highlight only the affected line instead of the entire paragraph.

---

# Span Model

Span is the smallest unit extracted from a digital PDF.

Each span stores formatting information associated with a continuous region of text.

Current metadata includes

* Text
* Font
* Font size
* Font color
* Bounding box

Future versions may additionally preserve

* Bold
* Italic
* Underline
* Background color
* Rotation
* Writing direction

Spans are primarily used by formatting analyzers.

---

# Why Preserve the Entire Hierarchy?

Many PDF comparison tools immediately convert documents into plain text.

While this simplifies text comparison, it permanently discards valuable information.

For example,

```text
Font
Size
Color
Alignment
Margins
Bounding Boxes
```

are impossible to recover once removed.

Instead, this project keeps the complete hierarchy throughout the extraction stage and only creates simplified representations later when required.

---

# Flattening Stage

Although the hierarchical document model is ideal for extraction, it is inefficient for comparison algorithms.

Therefore, the next stage converts the document into a linear sequence.

```text
Document

↓

TextElement[]
```

Flattening removes unnecessary nesting while preserving all positional metadata.

---

# TextElement

TextElement is the primary comparison unit used throughout the framework.

Every line of the document becomes one TextElement.

Each element stores:

* Unique ID
* Page number
* Block number
* Line number
* Original text
* Normalized text (future)
* Bounding box

Example

```text
ID: 17

Page: 2

Block: 5

Line: 1

Text:

Managers should approve leave requests.

Bounding Box:

(72.0, 280.5, 420.8, 302.1)
```

The unique identifier allows every difference to reference the original document without repeatedly storing location information.

---

# Why Compare Lines Instead of Words?

One possible design was to flatten the document into individual words.

After experimentation, line-level comparison was chosen for several reasons.

Advantages

* Better document context
* Lower computational overhead
* Easier sequence alignment
* Better report readability
* Preserves paragraph structure

Word-level analysis still occurs later, but only after corresponding lines have been aligned.

---

# Sequence Alignment

Once both documents have been flattened, they are aligned before any comparison takes place.

This is one of the most important architectural decisions in the project.

Without alignment, inserting a single sentence near the beginning of a document causes every following line to appear different.

Example

Document A

```text
Employee Handbook

Leave Policy

Working Hours
```

Document B

```text
Employee Handbook

New Introduction

Leave Policy

Working Hours
```

A naïve line-by-line comparison would incorrectly classify almost every remaining line as different.

Instead, the alignment stage establishes correspondence between the two documents.

---

# AlignedPair

Alignment produces a sequence of AlignedPair objects.

Each AlignedPair contains

* Pair index
* Left TextElement
* Right TextElement
* Alignment type

The alignment type may be one of:

```text
EQUAL

REPLACE

INSERT

DELETE
```

Example

```text
LEFT

Leave Policy

↓

RIGHT

Leave Policy

↓

Alignment

EQUAL
```

Example

```text
LEFT

—

↓

RIGHT

This sentence was inserted.

↓

Alignment

INSERT
```

This abstraction completely separates alignment from comparison.

---

# Why Alignment Happens Before Comparison

The comparison engine should never determine whether two lines correspond.

Its only responsibility is to analyze already-aligned content.

This separation offers several advantages.

* Prevents cascading mismatches
* Simplifies comparison algorithms
* Allows OCR documents to reuse the same pipeline
* Enables future semantic alignment algorithms

Future versions may replace the alignment algorithm without requiring any changes to the comparison modules.

---

# Immutable Data Flow

The framework follows an immutable processing strategy.

Every stage creates a new representation without modifying the previous one.

Example

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

Earlier stages remain unchanged throughout the pipeline.

This greatly simplifies debugging while preserving the original document for future analysis.

---

# Why This Transformation Pipeline?

Each transformation exists because different stages require different representations.

| Stage      | Best Representation   |
| ---------- | --------------------- |
| Extraction | Hierarchical Document |
| Comparison | TextElement[]         |
| Alignment  | AlignedPair[]         |
| Reporting  | Difference[]          |

Rather than forcing one data structure to solve every problem, each stage uses the representation most appropriate for its task.

This design keeps individual modules simple while allowing the entire framework to scale as additional comparison capabilities are introduced.

# Comparison Framework

After two documents have been aligned, the comparison framework becomes responsible for identifying and classifying every mismatch.

Rather than implementing one large comparison algorithm, the project follows a modular architecture where each component specializes in detecting one category of differences.

This approach improves maintainability, extensibility, and testing while allowing future AI models to be integrated with minimal changes.

The comparison framework is built around two primary abstractions:

* **Comparators**
* **Analyzers**

---

# Comparator Architecture

Comparators operate on an entire aligned document.

Input

```text
AlignedPair[]
```

Output

```text
Difference[]
```

Comparators are responsible for deciding **which aligned pairs require analysis**, while analyzers determine **what kind of difference exists**.

Current comparator hierarchy

```text
BaseComparator
        │
        ├── InsertionDeletionComparator
        │
        └── ReplaceComparator
```

---

## InsertionDeletionComparator

The first implemented comparator.

Responsibilities

* Detect inserted text
* Detect deleted text
* Convert alignment results into Difference objects

Since sequence alignment already identifies insertions and deletions, this comparator performs no additional analysis.

Its purpose is simply to transform alignment information into a standardized representation.

---

## ReplaceComparator

The ReplaceComparator acts as the central dispatcher for all replacement-based differences.

Responsibilities

* Iterate through aligned document pairs
* Select only AlignmentType.REPLACE entries
* Delegate analysis to specialized analyzers
* Collect all generated Difference objects

Unlike traditional comparison tools, ReplaceComparator does not determine what changed.

Instead, it coordinates the analysis process.

---

# Analyzer Framework

Analyzers operate on individual aligned pairs.

Input

```text
AlignedPair
```

Output

```text
Difference[]
```

Each analyzer is responsible for identifying one specific category of mismatch.

Current analyzer architecture

```text
ReplaceComparator
        │
        ├── CharacterAnalyzer
        ├── WordAnalyzer
        ├── CaseAnalyzer
        ├── WhitespaceAnalyzer
        ├── SpellingAnalyzer
        ├── FormattingAnalyzer
        ├── SemanticAnalyzer
        ├── NumberAnalyzer
        ├── DateAnalyzer
        └── ImageTextAnalyzer
```

Only the first analyzer is currently under implementation.

The remaining analyzers represent future development milestones.

---

# Character Analyzer

Purpose

Detect small character-level modifications between highly similar strings.

Typical examples include

```text
fox

↓

f0x
```

```text
EMP-1024

↓

EMP-1025
```

```text
Intelligence

↓

Inteligence
```

Rather than comparing every replacement at the character level, the analyzer first evaluates textual similarity.

Only highly similar strings undergo character-by-character analysis.

This prevents unrelated replacements from generating meaningless character differences.

---

# Word Analyzer

Responsibilities

* Word substitutions
* Word insertions
* Word deletions
* Word order changes

Example

```text
Managers

↓

Supervisors
```

---

# Case Analyzer

Detects changes involving letter casing.

Examples

```text
June

↓

june
```

```text
APPROVED

↓

Approved
```

---

# Whitespace Analyzer

Detects formatting differences caused by whitespace.

Examples

* Multiple spaces
* Missing spaces
* Leading whitespace
* Trailing whitespace
* Tab differences

Although these differences are often invisible to users, they can be significant in legal or technical documents.

---

# Spelling Analyzer

Detects spelling mistakes while ignoring intentional wording changes.

Examples

```text
Intelligence

↓

Inteligence
```

```text
Organisation

↓

Organization
```

Future versions may integrate dictionary-based or transformer-based spell checking.

---

# Formatting Analyzer

Unlike textual analyzers, this module compares formatting metadata extracted from spans.

Planned comparisons include

* Font family
* Font size
* Font color
* Bold
* Italic
* Underline
* Alignment
* Paragraph spacing
* Margins

Because formatting metadata is preserved during extraction, no additional parsing is required.

---

# Difference Model

Every comparison module ultimately produces Difference objects.

The Difference model serves as the universal representation of every detected mismatch.

This abstraction enables the reporting system to remain completely independent of the comparison algorithms.

Future Difference categories include

```text
Character

Word

Insertion

Deletion

Case

Whitespace

Spelling

Formatting

Image

OCR

Semantic

Number

Date
```

All future analyzers will generate the same standardized Difference representation.

---

# Future OCR Pipeline

Digital PDF comparison is only one part of the project.

Future versions will support scanned documents through OCR.

Pipeline

```text
Scanned PDF

↓

Image Extraction

↓

OCR Engine

↓

Document Reconstruction

↓

Document Model

↓

Existing Comparison Pipeline
```

Notice that OCR output is converted into the same Document model used by digital PDFs.

No changes are required in the alignment or comparison stages.

This design significantly reduces implementation complexity.

---

# Image Comparison Pipeline

Future versions will support comparison of embedded images.

The planned workflow is

```text
PDF

↓

Extract Images

↓

Image Matching

↓

OCR (if required)

↓

Image Analyzer

↓

Difference[]
```

Capabilities

* Missing images
* Modified images
* OCR text inside images
* Logo changes
* Signature comparison
* Visual similarity scoring

---

# Report Generation

The final stage of the pipeline converts Difference objects into human-readable reports.

Planned outputs include

* Terminal report
* JSON
* HTML
* PDF
* REST API responses

Future HTML reports will include

* Side-by-side document comparison
* Highlighted text differences
* Formatting overlays
* Bounding-box visualization
* Interactive navigation
* Difference filtering

---

# Why This Architecture Scales

The framework has been designed around interchangeable modules.

Adding a new comparison capability typically requires only

1. Creating a new analyzer
2. Registering it inside ReplaceComparator

No existing comparison logic needs to be modified.

This follows the Open/Closed Principle, allowing the framework to grow without increasing maintenance complexity.

---

# Installation

Clone the repository

```bash
git clone <repository-url>
cd pdf_mismatch
```

Create a virtual environment

```bash
python -m venv venv
```

Activate the environment

Linux

```bash
source venv/bin/activate
```

Windows

```cmd
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# Running the Project

Execute

```bash
python main.py
```

The current implementation performs

1. PDF extraction
2. Document parsing
3. Flattening
4. Sequence alignment
5. Insertion/deletion comparison

Future versions will automatically include additional analyzers as they are implemented.

---

# Project Roadmap

## Phase 1 — Foundation ✅

* Environment setup
* Digital PDF extraction
* Document models
* Flattening
* Sequence alignment
* Difference model
* Comparator framework
* Insertion/deletion comparison

---

## Phase 2 — Core Text Intelligence 🚧

* Character analyzer
* Word analyzer
* Case analyzer
* Whitespace analyzer
* Spelling analyzer
* Replace comparator integration

---

## Phase 3 — Formatting Intelligence

* Font comparison
* Color comparison
* Layout analysis
* Paragraph comparison
* Margin analysis

---

## Phase 4 — OCR Support

* Printed scanned PDFs
* OCR reconstruction
* Confidence-aware comparison

---

## Phase 5 — Image Intelligence

* Image extraction
* Image comparison
* OCR from embedded images
* Signature analysis
* Logo verification

---

## Phase 6 — Reporting

* Interactive HTML reports
* Visual annotations
* PDF summaries
* REST API
* Dashboard integration

---

# Design Principles

This project is guided by the following principles:

* Single Responsibility Principle
* Modular architecture
* Immutable data transformations
* Explainable comparison
* Extensible analyzer framework
* Standardized intermediate representations
* Reusable comparison pipeline
* AI-assisted document understanding

These principles ensure that the framework remains maintainable while continuing to expand with new comparison capabilities.

---

# Contributing

Contributions are welcome.

When adding new functionality:

* Keep modules focused on a single responsibility.
* Preserve immutable data transformations.
* Implement new comparison logic as analyzers whenever possible.
* Maintain compatibility with existing intermediate representations.
* Add tests for every new comparison module.

By following these guidelines, contributors can extend the framework without disrupting the existing architecture.

---

# Conclusion

The PDF Mismatch Detection Agent is evolving from a simple PDF comparison utility into a modular document analysis framework.

By separating extraction, alignment, comparison, and reporting into independent stages, the project establishes a scalable foundation capable of supporting traditional rule-based comparison as well as future AI-driven techniques such as semantic analysis, OCR, and multimodal document understanding.

The long-term vision is to provide an extensible, production-ready system capable of accurately comparing digital documents, scanned documents, and image-rich PDFs while producing detailed, explainable reports suitable for enterprise document verification workflows.
