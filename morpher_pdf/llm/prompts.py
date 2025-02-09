MARKDOWN_CONVERTER_PROMPT = """
Do two independent tasks "task one" and "task two" and place the result of those into these tags <task_one>...</task_one>, <task_two>...<task_two>.

Examples:
<task_one>
this is the plain text from an image
</task_one>

<task_two>
### Header of the text
text
...
</task_two>

### TASK ONE
Directly cite the text on this image. Preserve all the text. Don't include page number, but preserve numbers for formulas, tables, figures, and other resources. Mark places where images should be included

###TASK TWO
Directly cite the text on this image. Preserve all the text. Don't include page number, but preserve numbers for formulas, tables, figures, and other resources. Mark places where images should be included
Convert this PDF page image to Markdown format. The text should be the same text you output in "task one"

Follow these formatting rules:
- Preserve all original formatting and layout
- Never automatically complete the text. If the sentence is not complete, leave it as is.
- Always keep the original text in the same order. If the text is not complete, leave it as is.
- If the page starts with a fraction of a sentence or a paragraph, keep it as is. Do not cut it off.
- NEVER cut off the text at the beginning of the page.
- If the page starts without a heading and follows by the text with a heading, preserve the text before the heading.
- Convert headings based on their visual hierarchy:
  * Main titles → # (h1)
  * Subtitles → ## (h2)
  * Sub-subtitles → ### (h3)
  * Maintain numbers of headings which indicate the hierarchy of the document
- Maintain the style of figure descriptions:
  * Figure descriptions should be in the same line as the figure
  * Figure descriptions should be in bold text
- Maintain the style of table descriptions:
  * Table descriptions should be in bold text
- Maintain text styling:
  * Bold text → **text**
  * Italic text → *text*
  * Underlined text → <u>text</u>
- Keep all tables using Markdown table syntax
- Convert all mathematical formulas to LaTeX format enclosed in $$ for display math or $ for inline math
- Preserve lists (both ordered and unordered) with proper indentation
- Maintain paragraph spacing, but do not add extra new lines within paragraphs
- If sentences are within a paragraph, prioritize generating them on the same line, do not break them into separate lines
- Instead of images on the page, include html image tags with following sources {images} into the text where they should be. Preserve with of an image relative to the one on the page. Images are in the same order they are on the page:
 * Example on how to include images:
    <task_two>
    some text
    <img src="image_name.png" alt="drawing" width="image_width_in_pixels"/>
    some text
    </task_two>

Return the converted text in clean Markdown format. 

Pay EXTRA attention to correct formatting of formulas.
Make sure all powers are on a correct position!!!
"""

MARKDOWN_JUDGE_PROMPT = """
Your goal is to correct mistakes in PDF to markdown translation. Take the text in markdown provided and an image of a PDF page, and check this text on correctness. Return the corrected version of the text. Put everything into <task_two>....</task_two> xml tags. 

Here are some instruction for converting PDF to MD: 
<rules>

Follow these formatting rules:
- Preserve all original formatting and layout
- Never automatically complete the text. If the sentence is not complete, leave it as is.
- Always keep the original text in the same order. If the text is not complete, leave it as is.
- If the page starts with a fraction of a sentence or a paragraph, keep it as is. Do not cut it off.
- NEVER cut off the text at the beginning of the page.
- If the page starts without a heading and follows by the text with a heading, preserve the text before the heading.
- Convert headings based on their visual hierarchy:
  * Main titles → # (h1)
  * Subtitles → ## (h2)
  * Sub-subtitles → ### (h3)
  * Maintain numbers of headings which indicate the hierarchy of the document
- Maintain the style of figure descriptions:
  * Figure descriptions should be in the same line as the figure
  * Figure descriptions should be in bold text
- Maintain the style of table descriptions:
  * Table descriptions should be in bold text
- Maintain text styling:
  * Bold text → **text**
  * Italic text → *text*
  * Underlined text → <u>text</u>
- Keep all tables using Markdown table syntax
- Convert all mathematical formulas to LaTeX format enclosed in $$ for display math or $ for inline math
- Preserve lists (both ordered and unordered) with proper indentation
- Maintain paragraph spacing, but do not add extra new lines within paragraphs
- If sentences are within a paragraph, prioritize generating them on the same line, do not break them into separate lines
- Instead of images on the page, include html image tags with following sources {images} into the text where they should be. Preserve with of an image relative to the one on the page. Images are in the same order they are on the page:
 * Example on how to include images:
    <task_two>
    some text
    <img src="image_name.png" alt="drawing" width="image_width_in_pixels"/>
    some text
    </task_two>
</rules>
"""



MARKDOWN_CONVERTER_PROMPT_GEMINI_2 = """
Directly cite the text on this image. Preserve all the text. Don't include page number, but preserve numbers for formulas, tables, figures, and other resources. Mark places where images should be included
Convert this PDF page image to Markdown format.

Follow these formatting rules:
- Preserve all original formatting and layout
- Never automatically complete the text. If the sentence is not complete, leave it as is.
- Always keep the original text in the same order. If the text is not complete, leave it as is.
- If the page starts with a fraction of a sentence or a paragraph, keep it as is. Do not cut it off.
- NEVER cut off the text at the beginning of the page.
- If the page starts without a heading and follows by the text with a heading, preserve the text before the heading.
- Convert headings based on their visual hierarchy:
  * Main titles → # (h1)
  * Subtitles → ## (h2)
  * Sub-subtitles → ### (h3)
  * Maintain numbers of headings which indicate the hierarchy of the document
- Maintain the style of figure descriptions:
  * Figure descriptions should be in the same line as the figure
  * Figure descriptions should be in bold text
- Maintain the style of table descriptions:
  * Table descriptions should be in bold text
- Maintain text styling:
  * Bold text → **text**
  * Italic text → *text*
  * Underlined text → <u>text</u>
- Keep all tables using Markdown table syntax
- Convert all mathematical formulas to LaTeX format enclosed in $$ for display math or $ for inline math
- Preserve lists (both ordered and unordered) with proper indentation
- Maintain paragraph spacing, but do not add extra new lines within paragraphs
- If sentences are within a paragraph, prioritize generating them on the same line, do not break them into separate lines
- Instead of images on the page, include html image tags with following sources {images} into the text where they should be. Preserve with of an image relative to the one on the page. Images are in the same order they are on the page:
 * Example on how to include images:
    <task_two>
    some text
    <img src="image_name.png" alt="drawing" width="image_width_in_pixels"/>
    some text
    </task_two>
- Always add a newline after the table:
  * Example:
    <task_two>
    some text
    | Table col       | col2 | col3 | col4 |
    |--------------|---------|---------|---------|
    | table content  | table content | table content | table content |
    | table content        | table content| table content | table content |
    
    some text
    </task_two>
- Don't add page number to the text.
- Preserve numbers for formulas, tables, figures, and other resources(except page number).

Return the converted text in clean Markdown format. 

Pay EXTRA attention to correct formatting of formulas.
Make sure all powers are on a correct position!!!

Place the result into <task_two>...</task_two> tags.
Example:
<task_two>
...
</task_two>
"""

MARKDOWN_CONVERTER_PROMPT_GEMINI_2_v1 = """
<prompt>
  <task_description>Convert a PDF page image to Markdown format while preserving all text and formatting. Insert image placeholders where appropriate.</task_description>
  
  <main_rules>
    <rule>Directly cite all text from the image</rule>
    <rule>Preserve all text in its original form</rule>
    <rule>Exclude page numbers</rule>
    <rule>Exclude page number from the text</rule>
    <rule>Don't add page number to the text</rule>
    <rule>Mark locations where images should be inserted</rule>
    <rule>If the text is long, do not add newlines to the text within one paragraph. Keep it in one line</rule>
    <rule>If the text within one paragraph is long, keep it in one line</rule>
    <rule>If the text within one paragraph is long, NEVER break it into separate lines</rule>
  </main_rules>

  <text_preservation_rules>
    <rule>Don't use <br> tag for newlines</rule>
    <rule>If the page layout is split into two columns, read the first column first, then the second column</rule>
    <rule>Never complete text automatically - preserve incomplete sentences as they appear</rule>
    <rule>Maintain original text order</rule>
    <rule>Preserve incomplete sentences/paragraphs at page start</rule>
    <rule>Never truncate text at page beginning</rule>
    <rule>Keep text appearing before headings when page starts without a heading</rule>
    <rule>Preserve numbers for formulas, tables, figures, and other resources(except page number)</rule>
    <rule>If the text is long, do not add newlines to the text within one paragraph. Keep it in one line</rule>
    <rule>When you see a drawing, don't try to convert it into text, replace it with image tag</rule>
    <rule>Don't convert drawings into text, replace drawings with image tag</rule>
    <rule>Don't convert graphs into text, replace graphs with image tag</rule>
    <rule>Don't convert diagrams into text, replace graphs with image tag</rule>
  </text_preservation_rules>

  <heading_hierarchy>
    <rule>Main titles → # (h1)</rule>
    <rule>Subtitles → ## (h2)</rule>
    <rule>Sub-subtitles → ### (h3)</rule>
    <rule>Preserve heading numbers indicating document hierarchy</rule>
  </heading_hierarchy>

  <element_styling>
    <figures>
      <rule>Place descriptions on same line as figure</rule>
      <rule>Use bold text for descriptions</rule>
    </figures>
    
    <tables>
      <rule>Use bold text for descriptions</rule>
      <rule>Add newline after each table</rule>
    </tables>
    
    <text_formatting>
      <rule>Bold text → **text**</rule>
      <rule>Italic text → *text*</rule>
      <rule>Underlined text → <u>text</u></rule>
    </text_formatting>

    <special_elements>
      <rule>Use Markdown table syntax for all tables</rule>
      <rule>Convert mathematical formulas to LaTeX format using $$ for display math or $ for inline math</rule>
      <rule>Preserve lists with proper indentation</rule>
      <rule>Maintain paragraph spacing without extra lines within paragraphs</rule>
      <rule>Keep sentences within a paragraph on the same line</rule>
    </special_elements>
  </element_styling>

  <math>
    <rules>
      <rule>Convert mathematical formulas to LaTeX format using $$ for display math or $ for inline math</rule>
      <rule>Every formula should be represented in LaTeX format</rule>
      <rule>Preserve numbers for formulas</rule>
      <rule>~ sign should be represented as \sim</rule>
    </rules>
    <examples>
      <example>
        $\delta$
      </example>
    </examples>
  </math>

  <code_formatting>
    <rules>
      <rule>Programming code should be surrounded by ```</rule>
      <rule>Proper tabulation should be used for code</rule>
      <rule>Add newline before and after code block</rule>
      <rule>Never put tables with the code block</rule>
      <rule>When you see a table, don't cover it with code block</rule>
    </rules>
    <examples>
      <example>
        ```python
        def factorial(n):
            if n == 0:
                return 1
            else:
                return n * factorial(n - 1)
        ```
      </example>
      <example>
        some text

        ```
        algorithm or pseudocode
        ```

        some text
      </example>
    </examples>
  </code_formatting>

  <table_formatting>
    <rules>
      <rule>Add newline after each table</rule>
      <rule>Add newline before each table</rule>
      <rule>Never surround table with ```</rule>
    </rules>
    <examples>
      <example>
        some text

        | Table col       | col2 | col3 | col4 |
        |--------------|---------|---------|---------|
        | table content  | table content | table content | table content |
        | table content        | table content| table content | table content |
      
        some text
      </example>
    </examples>
  </table_formatting>

  <image_insertion>
    <format>
      <![CDATA[
      <img src="image_name.png" alt="drawing" width="image_width_in_pixels"/>
      ]]>
    </format>
    <rules>
      <rule>When you see a drawing, don't try to convert it into text, replace it with image tag</rule>
      <rule>Don't convert drawings into text, replace drawings with image tag</rule>
      <rule>Don't convert graphs into text, replace graphs with image tag</rule>
      <rule>Don't convert diagrams into text, replace graphs with image tag</rule>
      <rule>Insert images in order of appearance</rule>
      <rule>Preserve relative image width from original page</rule>
      <rule>Use image sources from {images}</rule>
      <rule>If you see something which is visibly and image, don't convert it into text, replace it with image tag</rule>
    </rules>
  </image_insertion>

  <page_titles>
    <rule>Whenever you see a title like the one in page_titles list, replace it with the header from page_titles with the same formatting</rule>
    <rule>page_titles: {page_titles}</rule>
  </page_titles>

  <output_format>
    <rule>Place converted text within <task_two>...</task_two> tags</rule>
    <rule>Use clean Markdown format</rule>
    <rule>Ensure correct formula formatting, especially power positions</rule>
  </output_format>
</prompt>

<example>
  <task_two>
  [Converted content would appear here]
  </task_two>
</example>
"""