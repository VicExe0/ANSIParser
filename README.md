# ANSIParser
ANSI color parser based on html-like tags

### Installation:
    Copy the `ANSIParser` module into your project.

### Tags usage:
    `content outside<tagname>content inside</tagname>content outside`

### Tags:
    `bold` - Make text inside bolder
    `dim` - Make text inside darker
    `italic` - Make text inside italic
    `underline` - Draw like under the text inside
    `blink` - Make text inside blink on and off
    `reverse` - Swap background color and foreground color
    `hide` - Make text inside invisible
    `strikethrough - Draw line through the text inside

### Custom colors and gradient:
    `<#ff0000>`...`</#ff0000>`  - Set text color inside to `#ff0000` (single color)
    `<#ff0000>`...`</#00ff00>`  - Color the text inside based on the gradient from `#ff0000` to `#00ff00`

### Priority
    Deeper nested color tags will be overwritten if they are inside another color tag and
    both are set to the same theme foreground/background color.

    #### Example: 
        `<#ff0000><#ff0000>Hello, World!</#00ff00></#ff0000>`
        Gradient inside will be overwritten by red color.
        Try to avoid that because previous color wont be removed,
        instead another will be applyed right after.

### Tags as text:
    If you want to preserve specific tag, place `\` right before
    the tag.
    
    #### Example:
        `\<bold>\</bold>` - wont register as a tag and `\` will be removed