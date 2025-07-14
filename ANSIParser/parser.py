from typing import List, Tuple, Any, NoReturn, Optional
from functools import lru_cache
import re

TAG_PATTERN = re.compile(r"(?<!\\)<\/?\#?[:\w]+>|\<|[^<]+", re.DOTALL)
HEX_PATTERN = re.compile(r"^(?:\#[0-9a-fA-F]{6}(:bg)?)$")
ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*m')
ANSI_RESET = "\x1b[0m"
TAGS = {
    "": "", # Container
    "bold": "\x1b[1m",
    "dim": "\x1b[2m",
    "italic": "\x1b[3m",
    "underline": "\x1b[4m",
    "blink": "\x1b[5m",
    "reverse": "\x1b[7m",
    "hide": "\x1b[8m",
    "strikethrough": "\x1b[9m"
}

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
            If you want to preserve specific tag, place `\` right before
            the tag.
            
            #### Example:
                `\<bold>\</bold>` - wont register as a tag and `\` will be removed
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


class Stack:
    def __init__( self ) -> None:
        self.stack = []

    def top( self ) -> Any:
        return self.stack[-1]

    def empty( self ) -> bool:
        return len(self.stack) == 0

    def pop( self ) -> Any:
        return self.stack.pop()

    def push( self, value: Any ) -> NoReturn:
        self.stack.append(value)

    def __len__( self ) -> int:
        return len(self.stack)
    
    def __str__( self ) -> str:
        return str(self.stack)


class Token:
    def __init__( self, value: str, type: str ):
        self.value = value
        self.type = type

        if type == "text":
            self.value = re.sub(r'\\<(\/?\w+)>', r'<\1>', value)

        elif type == "tag":
            self.closing = True if value[1] == "/" else False

            prefix_len = 2 if self.closing else 1

            self.value = value[prefix_len:-1]

    def __repr__( self ) -> str:
        return f"{self.type}({self.value})"
    
    def __str__( self ) -> str:
        return str(self.value)


class Node:
    def __init__(self, tokens: List[Token] ) -> None: 
        self.content = []

        for token in tokens:
            if isinstance(token, Token):
                self.content.append(token)
            
            else:
                self.content.append(Node(token))

    def __len__( self ) -> int:
        return len(self.content)

    def __str__( self ) -> str:
        res = list(map(str, self.content))

        return str(res)
    

def lexer( text: str ) -> List[Token]:
    tokens = [ Token("<>", "tag") ]
    prev = None

    for m in TAG_PATTERN.finditer(text):
        s = m.group()

        if s.startswith("<") and s.endswith(">"):
            token = Token(s, "tag")

        else:
            if prev and prev.type == "text":
                prev.value += s
                continue

            token = Token(s, "text")

        tokens.append(token)
        prev = token

    tokens.append(Token("</>", "tag"))

    return tokens
            

def parser( tokens: List[Token] ) -> Node:
    weights = []
    stack = Stack()

    depth = 0
    for token in tokens:
        if token.type == "text":
            deepAppend(weights, token, depth)

        elif token.closing:
            if stack.empty():
                raise SyntaxError("Invalid tag placement.")

            stack.pop()
            deepAppend(weights, token, depth)
            depth -= 1

        else:
            stack.push(token)
            deepAppend(weights, [token], depth)
            depth += 1


    if not stack.empty() or depth != 0:
        raise SyntaxError("Invalid tag closing.")
    
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
        

def deepAppend( arr: List[Any], item: Any, depth: int ) -> NoReturn:
    curr = arr

    while depth > 0:
        curr = curr[-1]
        depth -= 1
    
    curr.append(item)

@lru_cache
def hexToRGB( hex_color: str ) -> Tuple[int, int, int]:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

@lru_cache
def cleanTextLen( value: str ) -> Tuple[int, str]:
    clean = ANSI_REGEX.sub('', value)

    return len(clean), clean


def containsNode( node: Node ) -> bool:
    for item in node.content:
        if isinstance(item, Node):
            return True
        
        if isinstance(item, Token):
            continue

    return False

@lru_cache
def interpolateColors( start: List[int], end: List[int], length: int, step: int ) -> Tuple[int, int, int]:
    ratio = step / (length - 1) if length > 1 else 0

    r = round(start[0] + (end[0] - start[0]) * ratio)
    g = round(start[1] + (end[1] - start[1]) * ratio)
    b = round(start[2] + (end[2] - start[2]) * ratio)

    return ( r, g, b )

def evalNode( node: Node ) -> Token:
    open_tag: str = node.content[0].value
    close_tag = node.content[-1].value
    hex_tag1 = bool(HEX_PATTERN.fullmatch(open_tag))
    hex_tag2 = bool(HEX_PATTERN.fullmatch(close_tag))

    text_values = [ node.content[i].value for i in range(1, len(node.content) - 1) ]

    text_content = ''.join(text_values)

    theme = 48 if open_tag.endswith(":bg") and close_tag.endswith(":bg") else 38
    same_color = bool(open_tag == close_tag)

    if open_tag == close_tag and not (hex_tag1 and hex_tag2):
        ansi = TAGS.get(open_tag, None)

        if ansi is None:
            raise SyntaxError(f"Unknown tag {open_tag}.")
        
        return Token(f"{ansi}{text_content}{ANSI_RESET}", "text")

    if hex_tag1 is None or hex_tag2 is None:
        raise SyntaxError("Invalid hex colors.")
    
    start = hexToRGB(open_tag)
    end = hexToRGB(close_tag)

    length, _ = cleanTextLen(text_content)
    total_length = len(text_content)

    result = ""

    index = 0
    step = 0

    while index < total_length:
        item = text_content[index]

        if item == '\x1b':
            c_end = index + 1

            while c_end < total_length and text_content[c_end] != 'm':
                c_end += 1

            c_end += 1

            result += text_content[index:c_end]
            index = c_end
            continue

        r, g, b = start if same_color else interpolateColors(start, end, length, step)

        result += f"\x1b[{theme};2;{r};{g};{b}m{item}"

        step += 1
        index += 1

    result += ANSI_RESET

    return Token(result, "text")



        

