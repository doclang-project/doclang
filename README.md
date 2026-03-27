# Doclang ISO standard

This repo keeps all the documentation for the ISO standardization of Doclang.

## ISO standard

The official ISO standard is described in the Markdown file [iso-standard.md](./iso-standard.md).

To create the Word document, simply run `uv run ./docling_iso/write_iso_draft.py`.

## XSD Schema

The XSD schema can be found in [doclang.xsd](./resources/schema/doclang.xsd).

To validate an XML file:
1. ensure it references the contains `xmlns="http://www.doclang.ai/schema/v1"` in the `doclang` element, e.g.:
    ```xml
    <doclang xmlns="http://www.doclang.ai/schema/v1">
        <!-- ... -->
    </doclang>
    ```
2. run `validate.py`, e.g. to check the test sample, from the `./resources/schema` directory run:
    ```shell
    uv run python ./validate.py test_input.xml doclang.xsd
    ```
