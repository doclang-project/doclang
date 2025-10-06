from pathlib import Path
from lark import Lark, Transformer, Tree

_GRAMMAR_PATH = Path(__file__).parent / "grammar.lark"

class _PruneNoneTransformer(Transformer):
    def __default__(self, data, children, meta):
        # Filter out None values from the children list
        filtered_children = [c for c in children if c is not None]
        # Recreate the tree with the filtered children
        return Tree(data, filtered_children, meta)

def _get_parser():
    with open(_GRAMMAR_PATH, "r") as f:
        dsl_grammar = f.read()
    return Lark(dsl_grammar)
