#!/usr/bin/env bash
# Pack a DocLang archive directory into a .dclx OPC ZIP file.
# Usage: ./utils/pack-archive.sh <source-dir> [output-file]

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <source-dir> [output-file]" >&2
  exit 1
fi

SRC=$(cd "$1" && pwd)
NAME=$(basename "$SRC")
OUT=${2:-"${NAME}.dclx"}

if [[ ! -f "$SRC/document.xml" ]]; then
  echo "Error: $SRC/document.xml not found" >&2
  exit 1
fi

if [[ "$OUT" != /* ]]; then
  OUT="$(pwd)/$OUT"
fi

STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

cp -R "$SRC"/. "$STAGE"/

if [[ ! -f "$STAGE/[Content_Types].xml" ]]; then
  cat > "$STAGE/[Content_Types].xml" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Default Extension="jpg" ContentType="image/jpeg"/>
  <Default Extension="jpeg" ContentType="image/jpeg"/>
  <Default Extension="webp" ContentType="image/webp"/>
  <Override PartName="/document.xml" ContentType="application/vnd.doclang.document+xml"/>
</Types>
EOF
fi

if [[ ! -f "$STAGE/_rels/.rels" ]]; then
  mkdir -p "$STAGE/_rels"
  cat > "$STAGE/_rels/.rels" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://doclang.ai/ns/package/2026/relationships/document"
    Target="document.xml"/>
</Relationships>
EOF
fi

rm -f "$OUT"
(
  cd "$STAGE"
  zip -r "$OUT" . \
    -x "*.DS_Store" \
    -x "__MACOSX/*" \
    -x "*/._*" \
    -x "._*"
)
echo "Created $OUT"
