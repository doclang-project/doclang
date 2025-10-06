from xml.sax.saxutils import escape
from pathlib import Path
from docling_iso.parser import _PruneNoneTransformer, _get_parser
import xml.dom.minidom
from xml.sax.saxutils import escape
from pathlib import Path
from pydantic import BaseModel
import yaml

from .test_data_gen_flag import GEN_TEST_DATA

class Fixture(BaseModel):
    doctags: str
    output: str

class FixtureSet(BaseModel):
    fixtures: list[Fixture] = []

inputs = [
    "<doctag><group><title>My title here</title><text>My text here</text></group></doctag>",

    "<doctag><list><list_item>Single item</list_item></list></doctag>",
    "<doctag><list><list_item>First item</list_item><list_item>Second item</list_item></list></doctag>",
    "<doctag><list><list_item><italic>Single italic item</italic></list_item></list></doctag>",
    "<doctag><list><list_item><text>First paragraph</text><text>Another paragraph</text></list_item></list></doctag>",
    # "<doctag><group><list_item><italic>Single italic item</italic></list_item></group></doctag>": "group",  # TODO: here list item is interpreted as text_content, could be a feature
    # "<doctag><list><st item</list_item><list_item><italic>Second item</italic></list_item></list></doctag>": "list",  # TODO: fix this

    "<doctag><title><location_12/><location_42/><location_24/><location_19/>Title</title></doctag>",
    "<doctag><section_header>This is my section</section_header></doctag>",
    "<doctag><text>My text</text></doctag>",
    "<doctag><caption>Caption</caption></doctag>",
    "<doctag><title><italic>Welcome</italic></title></doctag>",
    # "<doctag><title>hi <italic>Welcome</italic></title></doctag>": "title",  # TODO: fix this

    "<doctag><bold>foo</bold></doctag>",
    "<doctag><italic>bar</italic></doctag>",
    "<doctag><bold><italic>baz</italic></bold></doctag>",
    "<doctag><bold><code><python/>print('Hello')</code></bold></doctag>",

    "<doctag><code>This is some code.</code></doctag>",
    "<doctag><code>This is more code.\nIt has two lines.</code></doctag>",
    "<doctag><code></code></doctag>",
    "<doctag><code>print('Hello world')</code></doctag>",
    "<doctag><code><python/>print('Hello')</code></doctag>",
    "<doctag><code><python/><![CDATA[hi</code>]]></code></doctag>",
    "<doctag><code><python/><![CDATA[]]></code></doctag>",
    "<doctag><code><python/><![CDATA[]]]]><![CDATA[>]]></code></doctag>",
    "<doctag><code><python/><![CDATA[]]>]]></code></doctag>",
    "<doctag><code><python/><![CDATA[This contains ]]> in the middle]]></code></doctag>",
    "<doctag><code><java/><location_12/><location_42/><location_24/><location_19/>system.out.println(\"Hello\")</code></doctag>",
    "<doctag><code>system.out.println(\"Hello\")<java/></code></doctag>",
    "<doctag><code lang='python'>Hi</code></doctag>",
    # "<doctag><code><javascript/>console.log('unsupported')</code></doctag>": "code",  # TODO: fix this: should still be code
    "<doctag><code>Tag mismatch</formula></doctag>",

    "<doctag><formula>This is some formula.</formula></doctag>",
    "<doctag><formula></formula></doctag>",

    "<doctag>This is just regular text.</doctag>",
    # "<doctag><other>Undefined tag</other></doctag>": "text_content",  # TODO: fix this
    # "<doctag><unbalanced</doctag>": "text_content",  # TODO: fix this
    "<doctag></doctag>",
    # "<doctag>foo<page_break/>bar</doctag>": "raw_text",  # TODO: fix this 👈
]



def test_parser():
    parser = _get_parser()
    exp_path = Path(__file__).parent / "data" / "test_data.yaml"
    fixture_set = FixtureSet(fixtures=[])

    if GEN_TEST_DATA:
        for text in inputs:
            out = None
            try:
                tree = parser.parse(text)
            except Exception as e:
                inp = text
                out = f"Raised {e.__module__}.{e.__class__.__name__}."

            if out is None:
                inp = xml.dom.minidom.parseString(text).documentElement.toprettyxml(indent="  ").strip()
                tree = _PruneNoneTransformer().transform(parser.parse(text))  # prune optional nodes not populated by the parser
                out = tree.pretty().replace("\t", "  ").strip()
            fixture_set.fixtures.append(Fixture(doctags=inp, output=out))

        exp_path.write_text(fixture_set.model_dump_json(indent=2))
        with open(exp_path, "w") as f:
            yaml.dump(fixture_set.model_dump(), f, default_style="|")

        # generate report
        report_content = ["<ol>"]
        for fixture in fixture_set.fixtures:
            report_content.append(f"<li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>{escape(fixture.doctags)}</code></pre></td><td><pre><code>{escape(fixture.output)}</code></pre></td></tr></table>")
        report_content.append("</ol>")

        with open(exp_path.with_suffix(".md"), "w") as f:
            f.write("".join(report_content))

    else:
        with open(exp_path, "r") as f:
            fixture_set = FixtureSet.model_validate(yaml.load(f, Loader=yaml.SafeLoader))
        assert len(fixture_set.fixtures) == len(inputs)
        for fixture, inp in zip(fixture_set.fixtures, inputs):
            is_error = False
            try:
                tree = parser.parse(inp)
            except Exception as e:
                is_error = True
                assert fixture.output == f"Raised {e.__module__}.{e.__class__.__name__}."

            if not is_error:
                assert fixture.doctags == xml.dom.minidom.parseString(inp).documentElement.toprettyxml(indent="  ").strip()
                assert fixture.output == (_PruneNoneTransformer().transform(tree)).pretty().replace("\t", "  ").strip()
