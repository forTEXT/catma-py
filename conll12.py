# -*- coding: utf-8 -*-
"""
Created on Sun Dec 31 13:10:42 2017

@author: mp
"""
import catma

class LineParser(object):
    """Parse CoNLL12 format"""

    def __init__(self):
        self.state_handler = self.search_line_block
        self.blockcounter = -1

    def in_line_block(self, file_line, linehandlers):
        if file_line == "" or file_line.isspace():
            return self.search_line_block
        elif file_line.startswith("#"):
            return self.in_line_block
        else:
            for linehandler in linehandlers:
                linehandler.token(file_line, self.blockcounter)

            return self.in_line_block

    def search_line_block(self, file_line, linehandlers):
        if file_line == "" or file_line.isspace() or file_line.startswith("#"):
            return self.search_line_block
        else:
            self.blockcounter += 1
            return self.in_line_block(file_line, linehandlers)

    def parse_file(self, filename, linehandlers=tuple()):
        file = open(filename, mode="r", encoding='utf-8')
        for line in file:
            self.state_handler = self.state_handler(
                catma.remove_utf8bom(line), linehandlers)
        file.close()

        for linehandler in linehandlers:
            if callable(getattr(linehandler, 'endoflines', None)):
                linehandler.endoflines()

class BaseTokenHandler(object):
    def __init__(self, text):
        self.text = text
        self.current_text_pos = 0

    def find_word(self, word):
        if isinstance(self.text, str):
            return self.text.find(word, self.current_text_pos)

        if self.text is None:
            self.text = list()
        else:
            self.current_text_pos += 1 #space separator

        self.text.append(word)

        return self.current_text_pos

    def get_token_range(self, word):
        startidx = self.find_word(word)
        endidx = startidx+len(word)
        return catma.Range(startidx, endidx)

    def get_text(self):
        if isinstance(self.text, str):
            return self.text

        return " ".join(self.text)

class DefaultTokenHandler(BaseTokenHandler):
    def __init__(self, tagset, author, text=None, tokensep="\t", absent_token_value="-"):
        super().__init__(text=text)
        self.tagset = tagset
        self.author = author
        self.tokensep = tokensep
        self.absent_token_value = absent_token_value

        self.current_sentence_no = -1
        self.current_sentence_anno = None
        self.current_sentence_startidx = -1

        self.annotations = list()

    def token(self, token_line, sentenceno):
        entries = token_line.split(sep=self.tokensep)
        documentid = entries[0]
        partno = entries[1]
        wordno = entries[2]
        word = entries[3]
        pos = entries[4]
        parsebit = entries[5]
        lemma = entries[6]

        tokenrange = self.get_token_range(word)

        # sentence annotation
        if self.current_sentence_no != sentenceno:
            self.close_sentence_anno()
            self.current_sentence_no = sentenceno
            self.current_sentence_anno = catma.Annotation(self.tagset.get("sentence"))
            self.current_sentence_anno.addproperty("partno", partno)
            self.current_sentence_anno.addproperty("documentid", documentid)
            self.current_sentence_anno.addproperty("sentenceno", self.current_sentence_no)
            self.annotations.append(self.current_sentence_anno)
            self.current_sentence_startidx = tokenrange.start

        # token annotation
        token_anno = catma.Annotation(self.tagset.get("token"))
        token_anno.ranges.append(tokenrange)
        token_anno.addproperty("partno", partno)
        token_anno.addproperty("documentid", documentid)
        token_anno.addproperty("wordno", wordno)
        token_anno.addproperty("pos", pos)
        token_anno.addproperty("parsebit", parsebit)
        self.annotations.append(token_anno)

        # POS annotation
        pos_tag = self.get_pos_tag(pos)
        pos_anno = catma.Annotation(pos_tag)
        pos_anno.ranges.append(tokenrange)
        pos_anno.addproperty("partno", partno)
        pos_anno.addproperty("documentid", documentid)
        pos_anno.addproperty("wordno", wordno)
        self.annotations.append(pos_anno)

        if lemma.strip() != self.absent_token_value:
            # Lemma annotation
            lemma_anno = catma.Annotation(self.tagset.get("lemma"))
            lemma_anno.ranges.append(tokenrange)
            lemma_anno.addproperty("partno", partno)
            lemma_anno.addproperty("documentid", documentid)
            lemma_anno.addproperty("wordno", wordno)
            lemma_anno.addproperty("lemma", lemma, adhoc=True)
            self.annotations.append(lemma_anno)

        self.current_text_pos = tokenrange.end


    def get_pos_tag(self, pos):
        if pos not in self.tagset:
            self.tagset[pos] = catma.Tag(
                pos,
                color=None,
                author=self.author,
                parent=self.tagset.get("pos_base"))

        return self.tagset[pos]

    def endoflines(self):
        self.close_sentence_anno()

    def close_sentence_anno(self):
        if self.current_sentence_no != -1:
            self.current_sentence_anno.ranges.append(
                catma.Range(self.current_sentence_startidx, self.current_text_pos))
