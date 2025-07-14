from typing import List, Tuple, Optional

from .utils import Token, Node, cleanTextLen, deepAppend, containsNode, extractTextContent, getHexColor, skipANSI, interpolateColors
from .consts import TAG_PATTERN, THEME_BACKGROUND, THEME_FOREGROUND, TAGS, ANSI_RESET

class Parser:
    @staticmethod
    def parse( text: str ) -> str:
        """
        Parse the expression.

        ### Args:
            `text:` `str` - expression to parse

            
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
            If you want to preserve specific tag, place `\\` right before
            the tag.
            
            #### Example:
                `\\<bold>\\</bold>` - wont register as a tag and `\\` will be removed
        """
        tokens = lexer(text)

        root = parser(tokens)

        result = evaluator(root)

        return str(result)
    
    @staticmethod
    def clear( text: str ) -> str:
        """
        Remove any ANSI escape characters and return plain string.

        ### Args:
            `text`: `str` - string to clear
        """
        _, clean = cleanTextLen(text)
        return clean
    
    @staticmethod
    def cleanLength( text: str ) -> int:
        """
        Count how many characters are in the string excluding ANSI escape characters.

        ### Args:
            `text`: `str` - string to count
        """
        amount, _ = cleanTextLen(text)
        return amount
    

def lexer( text: str ) -> List[Token]:
    tokens = [ Token("<>", "tag") ]
    prev = None

    for match in TAG_PATTERN.finditer(text):
        content = match.group()
        
        if content.startswith("<") and content.endswith(">"):
            token = Token(content, "tag")

        else:
            if prev and prev.type == "text":
                prev.value += content
                continue

            token = Token(content, "text")

        tokens.append(token)
        prev = token

    tokens.append(Token("</>", "tag"))

    return tokens
            

def parser( tokens: List[Token] ) -> Node:
    weights = []

    depth = 0
    for token in tokens:
        if token.type == "text":
            deepAppend(weights, token, depth)

        elif token.closing:
            if depth == 0:
                raise SyntaxError("Invalid tag closing.")

            deepAppend(weights, token, depth)
            depth -= 1

        else:
            deepAppend(weights, [token], depth)
            depth += 1

    if depth != 0:
        raise SyntaxError("Tag not closed.")
    
    root = Node(weights)

    return root


def evaluator( root: Node ) -> str:
    while containsNode(root):
        _, deepest, parent, index = findDeepestNode(root)

        result: Token = evalNode(deepest)
        parent.content[index] = result

    return root.content[0]


def findDeepestNode(node: Node, depth: int = 0, parent: Optional[Node] = None, index: Optional[int] = None) -> Tuple[int, Node, Node, int]:
    max_depth = depth
    deepest = node
    deepest_parent = parent
    deepest_index = index

    for i, child in enumerate(node.content):
        if isinstance(child, Node):
            d, n, p, idx = findDeepestNode(child, depth + 1, node, i)
            
            if d > max_depth:
                max_depth = d
                deepest = n
                deepest_parent = p
                deepest_index = idx

    return max_depth, deepest, deepest_parent, deepest_index
    

def evalNode( node: Node ) -> Token:
    open_tag = node.content[0].value
    close_tag = node.content[-1].value
    text_content = extractTextContent(node)

    hex_open = getHexColor(open_tag)
    hex_close = getHexColor(close_tag)
    is_same_tag = open_tag == close_tag
    is_valid_colors = hex_open is not None and hex_close is not None
    theme = THEME_BACKGROUND if open_tag.endswith(":bg") and close_tag.endswith(":bg") else THEME_FOREGROUND

    if not is_valid_colors:
        if is_same_tag:
            ansi = TAGS.get(open_tag)

            if ansi is None:
                raise SyntaxError(f"Unknown tag {open_tag}.")
            
            return Token(f"{ansi}{text_content}{ANSI_RESET}", "text")

        raise SyntaxError("Invalid hex colors.")

    visible_len, _ = cleanTextLen(text_content)
    total_len = len(text_content)

    result = ""
    index = 0
    step = 0

    while index < total_len:
        char = text_content[index]

        if char == '\x1b':
            ansi_color, index = skipANSI(text_content, index)
            result += ansi_color
            continue

        r, g, b = hex_open if is_same_tag else interpolateColors(hex_open, hex_close, visible_len, step)
        result += f"\x1b[{theme};2;{r};{g};{b}m{char}"

        index += 1
        step += 1

    result += ANSI_RESET

    return Token(result, "text")
