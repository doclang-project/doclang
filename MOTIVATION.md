# Motivation

The motivation for this new markup language is twofold:

1. It is created from the ground up to be able to represent complex, multimodal content with visual grounding in plain text with markup
2. It is created with the express purpose to be compatible with LLM tokenizers, i.e. use a markup structure that maps naturally and efficiently between DocLang elements and LLM tokens.

As a consequence of point 2, this standard ensures that there is a limited number or tags and attributes. In general, we intend that the number of syntax tokens should not exceed 1000. The latter is not a strong bound, but rather a direction.

There is an exception for meta-data markup. Meta-data is not intended to be heavily used or produced by LLMs, so it is in general possible to include an expanded set of protected markup tokens. Nevertheless, we do want to normalize as much as possible this representation.

Such requirements preclude us from using existing markup languages such as Markdown (incomplete scope), HTML (not concise enough), LaTeX (ambiguity of representation) etc.

<figure style="text-align: left">
    <img src="resources/html_v_otsl.png"
         alt="HTML vs OTSL" style="width:700px">
    <figcaption>Example in pure table structure representation, omitting content of cells, when comparing HTML to DocLang (OTSL tags). HTML sequence is both longer and uses more tokens than DocLang</figcaption>
</figure>

<!-- TODO: update image text for DocLang: replace <section> with <heading>, add CDATA in <code> -->
<figure style="text-align: left">
    <img src="resources/doclang_example.png"
         alt="HTML vs OTSL" style="width:1000px">
    <figcaption>Examples of real-world document fragments and their DocLang representation</figcaption>
</figure>

A specific class of related formats is the one operating on the OCR level, including [PageXML](https://github.com/PRImA-Research-Lab/PAGE-XML), [ALTO XML](https://github.com/altoxml), and [hOCR](https://github.com/kba/hocr-spec).

Beyond certain low-level similarities (e.g. presence of bounding box information), the DocLang format is significantly differentiated as it is designed to be AI-native:

- The above-mentioned formats focus on OCR processing, e.g. for archives, browser display, or other types of OCR/HTR pipelines, while DocLang is designed for LLM/VLM generation, with token efficiency in mind.
- Whereas these formats are primarily concerned with the geometric locations of the various spans of text, DocLang also places a strong focus on the semantic meaning and internal structure of the involved complex components, providing various native elements for headings, formulas, code, etc. and also rich table structure support (incl. table headings, spanned cells, etc.), this way capturing richer context for generative AI applications to leverage.
