from typing import Tuple, Optional, List, Any, NoReturn
from functools import lru_cache

from .consts import ANSI_PATTERN, HEX_PATTERN

import re

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

@lru_cache
def cleanTextLen( value: str ) -> Tuple[int, str]:
    clean = ANSI_PATTERN.sub('', value)

    return len(clean), clean

@lru_cache
def interpolateColors( start: List[int], end: List[int], length: int, step: int ) -> Tuple[int, int, int]:
    ratio = step / (length - 1) if length > 1 else 0

    r = round(start[0] + (end[0] - start[0]) * ratio)
    g = round(start[1] + (end[1] - start[1]) * ratio)
    b = round(start[2] + (end[2] - start[2]) * ratio)

    return ( r, g, b )

@lru_cache
def getHexColor( value: str ) -> Optional[Tuple[int, int, int]]:
    if HEX_PATTERN.fullmatch(value) is None:
        return None
    
    color = value.lstrip("#")

    return tuple( int(color[i:i+2], 16) for i in ( 0, 2, 4 ) )

def containsNode( node: Node ) -> bool:
    for item in node.content:
        if isinstance(item, Node):
            return True
        
        if isinstance(item, Token):
            continue

    return False

def extractTextContent( node: Node ) -> str:
    return "".join(map(lambda x: x.value, node.content[1:-1]))

def deepAppend( arr: List[Any], item: Any, depth: int ) -> NoReturn:
    curr = arr

    while depth > 0:
        curr = curr[-1]
        depth -= 1
    
    curr.append(item)


def skipANSI( text: str, index: int ) -> Tuple[str, int]:
    sliced = text[index:]

    m_pos = sliced.find("m")

    if m_pos == -1:
        raise ValueError("Unclosed ANSI sequence")
    
    m_pos += 1

    return ( sliced[:m_pos], index + m_pos )