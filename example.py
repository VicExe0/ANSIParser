from ANSIParser import Parser

def main() -> None:
    text1 = Parser.parse("<#8000f0><bold>Hello! This is</bold></#f00040> <#7700ff><blink>ANSIParser</blink>!</#3c00f0>")
    text2 = Parser.parse("<reverse><bold><#000000:bg><#ffffff>By VicExe0</#000000></#ffffff:bg></bold></reverse>")

    print(text1)
    print(f"        {text2}")


if __name__ == "__main__":
    main()
