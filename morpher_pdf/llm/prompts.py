MARKDOWN_CONVERTER_PROMPT = """
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
- Maintain the style of figure descriptions:
  * Figure descriptions should be in the same line as the figure
  * Figure descriptions should be in bold text
- Maintain text styling:
  * Bold text → **text**
  * Italic text → *text*
  * Underlined text → <u>text</u>
- Keep all tables using Markdown table syntax
- Convert all mathematical formulas to LaTeX format enclosed in $$ for display math or $ for inline math
- Preserve lists (both ordered and unordered) with proper indentation
- Maintain paragraph spacing and line breaks

Return the converted text in clean Markdown format. 

Pay EXTRA attention to correct formatting of formulas.
Make sure all powers are on a correct position!!!

The text should be quoted within an xml tag like this:
<markdown>
...
</markdown>
"""
