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
Directly cite the text on this image. Preserve all the text.

###TASK TWO
Directly cite the text on this image. Preserve all the text.
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
- Do not include any images in the output, only image descriptions. Instead of images, include ![description](image_url)

Return the converted text in clean Markdown format. 

Pay EXTRA attention to correct formatting of formulas.
Make sure all powers are on a correct position!!!
"""
