import re
from abc import ABC, abstractmethod
from typing import List, Dict


WHITE_SPACE = 0
TAG = 1
CONTENT = 2

token_pairs = [
    (r"\s", WHITE_SPACE),
    (r"<[\s\S]*?>", TAG),
    (r"[^<>]+", CONTENT),
]

COMMENT = 0
LABEL = 1


class Token:

    def __init__(self, token_type: int, text: str, pos: int):
        self.token_type = token_type
        self.text = text
        self.pos = pos

    def get_tag_type(self) -> int:
        """make sure tag type"""
        if self.text.startswith("<!"):
            return COMMENT
        else:
            return LABEL

    def get_label_type(self) -> str:
        """make sure label type"""
        index = self.text.find(" ", 1)
        index = len(self.text) - 1 if index == -1 else index
        return "<%s>" % self.text[1:index]

    def get_label_attribute(self) -> Dict[str, str]:
        """make sure label type"""
        attribute_pairs = self.text[1:-1].split(" ")
        attribute_pairs = [attribute_pair for attribute_pair in attribute_pairs if "=" in attribute_pair]
        attribute = {}
        for attribute_pair in attribute_pairs:
            idx = attribute_pair.find("=")
            k = attribute_pair[:idx]
            v = attribute_pair[idx+1:][1:-1]
            attribute[k.lower()] = v
        return attribute

    def __str__(self):
        a = "Token(token_type=%d, text=%s, pos=%d)"
        b = (self.token_type, self.text, self.pos)
        return a % b

    __repr__ = __str__


class Tokenizer:

    def __init__(self, html):
        self.html = html

    def __iter__(self):
        pos = 0
        while pos < len(self.html):
            html = self.html[pos:]
            for token_regex, token_type in token_pairs:
                r = re.match(token_regex, html)
                if r is not None:
                    text = r.group()
                    yield Token(token_type, text, pos)
                    pos += r.end()
                    break
            else:
                raise Exception("invalid token at %d" % pos)


class FileObject(ABC):

    def __init__(self, content: str, file_object_list: List['FileObject']):
        self.content = content
        self.file_object_list = file_object_list

    @abstractmethod
    def __str__(self):
        raise NotImplemented


class BookMark(FileObject):

    def __init__(self,
                 content: str,
                 file_object_list: List[FileObject],
                 add_date: str,
                 last_modified: str,
                 personal_toolbar_folder: str):
        super(BookMark, self).__init__(content, file_object_list)
        self.add_date = add_date
        self.last_modified = last_modified
        self.personal_toolbar_folder = personal_toolbar_folder

    def __str__(self):
        t = (self.add_date, self.last_modified, self.personal_toolbar_folder, self.content)

        s = ""
        s += "<!DOCTYPE NETSCAPE-Bookmark-file-1>\n"
        s += "<!-- This is an automatically generated file.\n"
        s += "     It will be read and overwritten.\n"
        s += "     DO NOT EDIT! -->\n"
        s += "<META HTTP-EQUIV=\"Content-Type\" CONTENT=\"text/html; charset=UTF-8\">\n"
        s += "<TITLE>Bookmarks</TITLE>\n"
        s += "<H1>Bookmarks</H1>\n"
        s += "<DL><p>\n"
        s += "    <DT><H3 ADD_DATE=\"%s\" LAST_MODIFIED=\"%s\" PERSONAL_TOOLBAR_FOLDER=\"%s\">%s</H3>\n" % t
        s += "    <DL><p>\n"

        for file_object in self.file_object_list:
            lines = str(file_object)
            lines = lines.split("\n")
            for line in lines:
                s += "        " + line + "\n"

        s += "    </DL><p>\n"
        s += "</DL><p>"
        return s

    def __repr__(self):
        a = "BookMark(content=%s, file_object_list=%s, add_date=%s, last_modified=%s, personal_toolbar_folder=%s)"
        b = (self.content, self.file_object_list, self.add_date, self.last_modified, self.personal_toolbar_folder)
        return a % b


class Directory(FileObject):

    def __init__(self,
                 content: str,
                 file_object_list: List[FileObject],
                 add_date: str,
                 last_modified: str):
        super(Directory, self).__init__(content, file_object_list)
        self.add_date = add_date
        self.last_modified = last_modified

    def __str__(self):
        t = (self.add_date, self.last_modified, self.content)

        s = ""
        s += "<DT><H3 ADD_DATE=\"%s\" LAST_MODIFIED=\"%s\">%s</H3>\n" % t
        s += "<DL><p>\n"

        for file_object in self.file_object_list:
            lines = str(file_object)
            lines = lines.split("\n")
            for line in lines:
                s += "    " + line + "\n"

        s += "</DL><p>"
        return s

    def __repr__(self):
        a = "Directory(content=%s, file_object_list=%s, add_date=%s, last_modified=%s)"
        b = (self.content, self.file_object_list, self.add_date, self.last_modified)
        return a % b


class File(FileObject):

    def __init__(self,
                 content: str,
                 file_object_list: List[FileObject],
                 href: str,
                 add_date: str,
                 icon: str):
        super(File, self).__init__(content, file_object_list)
        self.href = href
        self.add_date = add_date
        self.icon = icon

    def __str__(self):
        s = ""
        s += "<DT><A HREF=\"%s\" ADD_DATE=\"%s\"" % (self.href, self.add_date)
        if self.icon is not None:
            s += " ICON=\"%s\"" % self.icon
        s += ">%s</A>" % self.content
        return s

    def __repr__(self):
        a = "File(name=%s, href=%s, add_date=%s)"
        b = (self.content, self.href, self.add_date)
        return a % b


class Parser:

    def __init__(self, tokenizer: Tokenizer):
        self.tokenizer = iter(tokenizer)
        self.tokens = []

    def next(self):
        while True:
            token = next(self.tokenizer)
            if token.token_type != WHITE_SPACE and (token.token_type != TAG or token.get_tag_type() != COMMENT):
                break
        self.tokens.append(token)

    def step(self):
        if len(self.tokens) == 0:
            self.next()

    def consume(self):
        if len(self.tokens) > 0:
            self.tokens = self.tokens[1:]

    def token(self, index: int) -> Token:
        return self.tokens[index]

    def assert_equal(self, token, token_type: int, tag_type: int = None, label_type_list: List[str] = []):
        if token.token_type == token_type:
            if tag_type is None or token.get_tag_type() == tag_type:
                if len(label_type_list) == 0 or token.get_label_type() in label_type_list:
                    return
        raise Exception("fail assert for token %s" % token)

    def parse_bookmark(self):
        while True:
            self.step()
            if self.token(0).token_type == TAG:
                if self.token(0).get_tag_type() == LABEL:
                    if self.token(0).get_label_type() == "<DT>":
                        break
            self.consume()

        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["<DT>"])
        self.consume()
        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["<H3>"])
        attributes = self.token(0).get_label_attribute()
        self.consume()
        self.step()
        self.assert_equal(self.token(0), CONTENT)
        content = self.token(0).text
        self.consume()
        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["</H3>"])
        self.consume()
        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["<DL>"])
        self.consume()
        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["<p>"])
        self.consume()

        bookmark = BookMark(
            content=content,
            file_object_list=[],
            add_date=attributes["add_date"],
            last_modified=attributes["last_modified"],
            personal_toolbar_folder=attributes["personal_toolbar_folder"]
        )
        while True:
            self.step()
            self.assert_equal(self.token(0), TAG, LABEL, ["<DT>", "</DL>"])
            label_type = self.token(0).get_label_type()
            if label_type == "<DT>":
                self.next()
                self.assert_equal(self.token(1), TAG, LABEL, ["<H3>", "<A>"])
                label_type = self.token(1).get_label_type()
                if label_type == "<H3>":
                    bookmark.file_object_list.append(self.parse_directory())
                else:
                    bookmark.file_object_list.append(self.parse_file())
            else:
                break

        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["</DL>"])
        self.consume()
        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["<p>"])
        self.consume()

        return bookmark

    def parse_directory(self):
        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["<DT>"])
        self.consume()
        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["<H3>"])
        attributes = self.token(0).get_label_attribute()
        self.consume()
        self.step()
        self.assert_equal(self.token(0), CONTENT)
        content = self.token(0).text
        self.consume()
        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["</H3>"])
        self.consume()
        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["<DL>"])
        self.consume()
        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["<p>"])
        self.consume()

        directory = Directory(
            content=content,
            file_object_list=[],
            add_date=attributes["add_date"],
            last_modified=attributes["last_modified"]
        )
        while True:
            self.step()
            self.assert_equal(self.token(0), TAG, LABEL, ["<DT>", "</DL>"])
            label_type = self.token(0).get_label_type()
            if label_type == "<DT>":
                self.next()
                self.assert_equal(self.token(1), TAG, LABEL, ["<H3>", "<A>"])
                label_type = self.token(1).get_label_type()
                if label_type == "<H3>":
                    directory.file_object_list.append(self.parse_directory())
                else:
                    directory.file_object_list.append(self.parse_file())
            else:
                break

        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["</DL>"])
        self.consume()
        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["<p>"])
        self.consume()

        return directory

    def parse_file(self):
        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["<DT>"])
        self.consume()
        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["<A>"])
        attributes = self.token(0).get_label_attribute()
        self.consume()
        self.step()
        self.assert_equal(self.token(0), CONTENT)
        content = self.token(0).text
        self.consume()
        self.step()
        self.assert_equal(self.token(0), TAG, LABEL, ["</A>"])
        self.consume()

        file = File(
            content=content,
            file_object_list=[],
            href=attributes["href"],
            add_date=attributes["add_date"],
            icon=attributes.get("icon", None)
        )
        return file
