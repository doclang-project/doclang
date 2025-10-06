<ol><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;group&gt;
    &lt;title&gt;My title here&lt;/title&gt;
    &lt;text&gt;My text here&lt;/text&gt;
  &lt;/group&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  group
    title
      text_content  My title here
    text
      text_content  My text here</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;list&gt;
    &lt;list_item&gt;Single item&lt;/list_item&gt;
  &lt;/list&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  list
    list_item
      text_content  Single item</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;list&gt;
    &lt;list_item&gt;First item&lt;/list_item&gt;
    &lt;list_item&gt;Second item&lt;/list_item&gt;
  &lt;/list&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  list
    list_item
      text_content  First item
    list_item
      text_content  Second item</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;list&gt;
    &lt;list_item&gt;
      &lt;italic&gt;Single italic item&lt;/italic&gt;
    &lt;/list_item&gt;
  &lt;/list&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  list
    list_item
      italic
        text_content  Single italic item</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;list&gt;
    &lt;list_item&gt;
      &lt;text&gt;First paragraph&lt;/text&gt;
      &lt;text&gt;Another paragraph&lt;/text&gt;
    &lt;/list_item&gt;
  &lt;/list&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  list
    list_item
      text
        text_content  First paragraph
      text
        text_content  Another paragraph</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;title&gt;
    &lt;location_12/&gt;
    &lt;location_42/&gt;
    &lt;location_24/&gt;
    &lt;location_19/&gt;
    Title
  &lt;/title&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  title
    brect
      12
      42
      24
      19
    text_content  Title</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;section_header&gt;This is my section&lt;/section_header&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  section_header
    text_content  This is my section</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;text&gt;My text&lt;/text&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  text
    text_content  My text</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;caption&gt;Caption&lt;/caption&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  caption
    text_content  Caption</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;title&gt;
    &lt;italic&gt;Welcome&lt;/italic&gt;
  &lt;/title&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  title
    italic
      text_content  Welcome</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;bold&gt;foo&lt;/bold&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  bold
    text_content  foo</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;italic&gt;bar&lt;/italic&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  italic
    text_content  bar</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;bold&gt;
    &lt;italic&gt;baz&lt;/italic&gt;
  &lt;/bold&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  bold
    italic
      text_content  baz</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;bold&gt;
    &lt;code&gt;
      &lt;python/&gt;
      print('Hello')
    &lt;/code&gt;
  &lt;/bold&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  bold
    code
      language_name  python
      text_content  print('Hello')</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;code&gt;This is some code.&lt;/code&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  code
    text_content  This is some code.</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;code&gt;This is more code.
It has two lines.&lt;/code&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  code
    text_content  This is more code.
It has two lines.</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;code/&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  code
    text_content</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;code&gt;print('Hello world')&lt;/code&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  code
    text_content  print('Hello world')</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;code&gt;
    &lt;python/&gt;
    print('Hello')
  &lt;/code&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  code
    language_name  python
    text_content  print('Hello')</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;code&gt;
    &lt;python/&gt;
&lt;![CDATA[hi&lt;/code&gt;]]&gt;  &lt;/code&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  code
    language_name  python
    text_content
      cdata_section
        cdata_content  hi&lt;/code&gt;</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;code&gt;
    &lt;python/&gt;
  &lt;/code&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  code
    language_name  python
    text_content
      cdata_section</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;code&gt;
    &lt;python/&gt;
&lt;![CDATA[]]]]&gt;&lt;![CDATA[&gt;]]&gt;  &lt;/code&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  code
    language_name  python
    text_content
      cdata_section
        cdata_content  ]]
      cdata_section
        cdata_content  &gt;</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;&lt;code&gt;&lt;python/&gt;&lt;![CDATA[]]&gt;]]&gt;&lt;/code&gt;&lt;/doctag&gt;</code></pre></td><td><pre><code>Raised lark.exceptions.UnexpectedCharacters.</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;&lt;code&gt;&lt;python/&gt;&lt;![CDATA[This contains ]]&gt; in the middle]]&gt;&lt;/code&gt;&lt;/doctag&gt;</code></pre></td><td><pre><code>Raised lark.exceptions.UnexpectedCharacters.</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;code&gt;
    &lt;java/&gt;
    &lt;location_12/&gt;
    &lt;location_42/&gt;
    &lt;location_24/&gt;
    &lt;location_19/&gt;
    system.out.println(&amp;quot;Hello&amp;quot;)
  &lt;/code&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  code
    language_name  java
    brect
      12
      42
      24
      19
    text_content  system.out.println("Hello")</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;&lt;code&gt;system.out.println("Hello")&lt;java/&gt;&lt;/code&gt;&lt;/doctag&gt;</code></pre></td><td><pre><code>Raised lark.exceptions.UnexpectedCharacters.</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;code lang="python"&gt;Hi&lt;/code&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  code
    language_name  python
    text_content  Hi</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;&lt;code&gt;Tag mismatch&lt;/formula&gt;&lt;/doctag&gt;</code></pre></td><td><pre><code>Raised lark.exceptions.UnexpectedCharacters.</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;formula&gt;This is some formula.&lt;/formula&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  formula
    text_content  This is some formula.</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;
  &lt;formula/&gt;
&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  formula
    text_content</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag&gt;This is just regular text.&lt;/doctag&gt;</code></pre></td><td><pre><code>doctag
  text_content  This is just regular text.</code></pre></td></tr></table><li/><table><tr><th>doctags</th><th>output</th></tr><tr><td><pre><code>&lt;doctag/&gt;</code></pre></td><td><pre><code>doctag
  text_content</code></pre></td></tr></table></ol>