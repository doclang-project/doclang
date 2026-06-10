## [v0.6.0](https://github.com/doclang-project/doclang/releases/tag/v0.6.0)

* improve spec export, minor test renaming (#91)
* allow full sem. body in `<picture>`, add `<tabular>` for chart tables (#90)
  * **BREAKING CHANGE**: chart-specific element body preamble shape changed from `<table>` -> `<src>` to `<src>` -> `<tabular>`

## [v0.5.0](https://github.com/doclang-project/doclang/releases/tag/v0.5.0)

* refine spec recommendations, add example fixes, BibTeX citation, PyPI metadata (#88)
* add `<layer>`, document tokenization guidelines (#87)

## [v0.4.0](https://github.com/doclang-project/doclang/releases/tag/v0.4.0)

* refine public API and reorganize validator docs (#85)
* update spec example picture, add fixture (#84)
* enforce field scope rules, expand recommendation guidance (#83)
* improve `<location>` handling, various spec refinements (#82)
* add version to spec, rescope example showing planned feature (#81)
* refine `<picture>` subclassing, update examples (#80)
* add CI, enhance dev env and validation tools (#79)
* Update spec.md
* extend `<picture>` documentation, detail `src.uri`, improve `<smiles>`
* clarify `<picture>`/`<src>`, update default class/label & picture labels
* improve documentation of `<formula>`, `<superscript>` & `<subscript>`
* limit scope that goes into package sdist
* enable package versioning w/out Git info
* add `<label>`, document recommended values
* refactor spec for clarity and correctness
* refine repo layout
* enhance `location@value` validation in schema and documentation
* remove `<floating_group>` from validator
* align `field_heading@level` spec
* align `heading@level` constraints
* add `<custom>`, defer `<meta>`
* sync validator w.r.t. `<layer>`
* add `<default_resolution>` to validator, add tests, align `<h_thread>`
* add `<page_break>` to validator, add tests
* refactor spec, separating out planned features
* fix typo
* add missing caption test
* restor broken image link
* refactor terminology, move `<caption>` to element head
* minor test improvements
* add `<thread>` validation & tests
* add cross-reference support, refactor hyperlink support
* refine terminology
* enhance release preparation, add changelog
* switch to dynamic versioning, document release process
* improve semantic element nesting handling
* add content element to virtual text schema
* update version retrieval method
* Update ISO standard contributor table

## [v0.3.0](https://github.com/doclang-project/doclang/releases/tag/v0.3.0)

* add table index class and version sync utility
* add virtual text support to lists and tables, incl. validation

## [v0.2.0](https://github.com/doclang-project/doclang/releases/tag/v0.2.0)

* chore: align lists, tables, groups, headings
* fix table structure description and examples
* restructure specification incl. appendices, auto-inject ref data


## [v0.1.0](https://github.com/doclang-project/doclang/releases/tag/v0.1.0)

* Initial version
