from chrome_bookmark import Tokenizer, Parser

if __name__ == "__main__":
    with open("input.html", "r", encoding="utf-8") as f:
        with open("output.html", "w", encoding="utf-8") as g:
            result = f.read()
            tokenizer = Tokenizer(result)
            parser = Parser(tokenizer)
            bookmark = parser.parse_bookmark()

            # swap directory name
            bookmark.file_object_list[0].content = "github"
            bookmark.file_object_list[0].file_object_list[0].content = "zhihu"

            result = str(bookmark)
            g.write(result)
