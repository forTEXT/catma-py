# -*- coding: utf-8 -*-
"""
This module provides a LineParser for the CoNLL-2012 format. Quoting from the
http://conll.cemantix.org/2012/data.html

The *_conll files contain data in a tabular structure similar to that used by
previous CoNLL shared tasks. We are using a [tag]-based extension naming approch
where a [tag] is applied to the .conll file to name it, say .[tag]_conll.
The [tag] itself can have multiple components and serves to highlight the
characteristics of that .conll file. For example, the two tags that we use in
the data are "v0_gold" and "v0_auto". Each of it has two (parts separated by underscores).
The first one has the same value — "v0" in both cases and indicates the version of the file.
The second has two values "gold" and "auto". The "gold" indicates that the
annotation is that file is hand-annotated and adjudicated quality, whereas the
second means it was produced using a combination of automatic tools.
The contents of each of these files comprises of a set of columns.
Each column either representing a linear annotation on a sentence, for example,
a part of speech annotation which is one part of speech per word, and so one
column per layer (in this case part of speech), or there are multiple columns —
taken in sync with another column and representing the part that all other words
in the sentence play with respect to that word. This is the classic case of
predicate argument structure as introduced in the CoNLL-2005 shared task.
In this case the number of columns that represent that layer of annotation is
variable — one per each predicate. For convenience, we have kept the coreference
layer information in the very last column and the predicate argument structure
information in a variable number of columns preceeding that. The columns in
the *_conll file represent the following:

Column 	Type 	Description
1 Document ID:
    This is a variation on the document filename
2 Part number:
    Some files are divided into multiple parts numbered as 000, 001, 002, ... etc.
3 Word number
4 Word itself:
    This is the token as segmented/tokenized in the Treebank.
    Initially the *_skel file contain the placeholder [WORD] which gets replaced by
    the actual token from the Treebank which is part of the OntoNotes release.
5 Part-of-Speech
6 Parse bit:
 	This is the bracketed structure broken before the first open
     parenthesis in the parse, and the word/part-of-speech leaf replaced with a *.
     The full parse can be created by substituting the asterix with the "([pos] [word])"
     string (or leaf) and concatenating the items in the rows of that column.
7 Predicate lemma:
    The predicate lemma is mentioned for the rows for which we
    have semantic role information. All other rows are marked with a "-"
8 Predicate Frameset ID:
    This is the PropBank frameset ID of the predicate in Column 7.
9 Word sense:
    This is the word sense of the word in Column 3.
10 Speaker/Author:
    This is the speaker or author name where available.
    Mostly in Broadcast Conversation and Web Log data.
11 Named Entities:
    These columns identifies the spans representing various
    named entities.
12:N 	Predicate Arguments:
    There is one column each of predicate argument
    structure information for the predicate mentioned in Column 7.
N:
    Coreference

The LineParser takes a collection of line handlers which need to provide a token method
that gets called for each token line.

A DefaultTokenHandler parses columns 1-7 of the columns defined above into CATMA
Annotation structures.

A BaseTokenHandler provides base functionality for custom Token Handlers.

@author: marco.petris@web.de
"""
import catma

class LineParser(object):
    """Parses a file in CoNLL12 format."""

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
        """
        Parses the file with the given filename in CoNLL12 format. Each linehandler
        must provide a method named 'token' that takes the current token line and the
        current block number (i. e. the sentence number, zero based).

        If the linehandler also provides a method named 'endoflines' this method
        gets called after the end of lines has been reached.
        """
        file = open(filename, mode="r", encoding='utf-8')
        for line in file:
            self.state_handler = self.state_handler(
                catma.remove_utf8bom(line), linehandlers)
        file.close()

        for linehandler in linehandlers:
            if callable(getattr(linehandler, 'endoflines', None)):
                linehandler.endoflines()

class BaseTokenHandler(object):
    """
    Provides basic functionality for custom token line handlers.
    """
    def __init__(self, text):
        """
        Constructs the BaseTokenHandler with an optional text. text may be None,
        in that case find_word builds up a text from the search words.
        """
        self.text = text
        self.current_text_pos = 0

    def find_word(self, word):
        """
        Returns the character offset of the given word. If this handler has not been
        initialized with a text, then this method builds up a text from the word
        arguments in order of the calls of this method. The character offset is
        computed from this list, each word is separated by a single whitespace.
        Otherwise the given word is searched within in the text given at initialization
        starting with the offset from the last 'find_word' call (starting with 0).
        """
        if isinstance(self.text, str):
            return self.text.find(word, self.current_text_pos)

        if self.text is None:
            self.text = list()
        else:
            self.current_text_pos += 1 #space separator

        self.text.append(word)

        return self.current_text_pos

    def get_token_range(self, word):
        """
        Returns the start and end character offsets as a CATMA range by using the
        'find_word' method.
        """
        startidx = self.find_word(word)
        endidx = startidx+len(word)
        return catma.Range(startidx, endidx)

    def get_text(self):
        """
        Returns the text underlying this token line handler. This may either
        be the text given at initialization or the text constructed during 'get_token_range'
        calls.
        """
        if isinstance(self.text, str):
            return self.text

        return " ".join(self.text)

class DefaultTokenHandler(BaseTokenHandler):
    """
    The default line token handler for the CoNLL-2012 format. It reads columns
    1-7 into CATMA Annotation structures. See module description.
    """
    def __init__(self, tagset, author, text=None, tokensep="\t", absent_token_value="-"):
        """
        Constructs the DefaultTokenHandler with a CATMA Tagset containing Tags
        for columns 1-7 of the CoNLL-2012 format: 'sentence', 'token', 'pos_base'
        and 'lemma'.
        Details:
            sentence:
                properties['partno', 'documentid', 'sentenceno']
            token:
                properties['partno', 'documentid', 'wordno', 'pos', 'parsebit']
            lemma:
                properties['partno', 'documentid', 'wordno', 'lemma']
            pos_base: 
                A Tag for each POS is created with the name of the POS value 
                and pos_base as parent.
        author: the author of the resulting Annotations.
        text: 
            The text that gets annotated (optional).In case of absence the text 
            is constructed from the CoNLL-2012 word (column 4).
        tokensep: Defaults to '\t'.
        absent_token_value: Represents an absent token value, depends to '-'
        """
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
        """
        This method gets called by the LineParser which provides the current
        token_line and the current sentenceno. It reads columns
        1-7 into CATMA Annotation structures (property annotations).
        """
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
            self.current_sentence_anno.add_property("partno", partno)
            self.current_sentence_anno.add_property("documentid", documentid)
            self.current_sentence_anno.add_property("sentenceno", self.current_sentence_no)
            self.annotations.append(self.current_sentence_anno)
            self.current_sentence_startidx = tokenrange.start

        # token annotation
        token_anno = catma.Annotation(self.tagset.get("token"))
        token_anno.ranges.append(tokenrange)
        token_anno.add_property("partno", partno)
        token_anno.add_property("documentid", documentid)
        token_anno.add_property("wordno", wordno)
        token_anno.add_property("pos", pos)
        token_anno.add_property("parsebit", parsebit)
        self.annotations.append(token_anno)

        # POS annotation
        pos_tag = self.get_pos_tag(pos)
        pos_anno = catma.Annotation(pos_tag)
        pos_anno.ranges.append(tokenrange)
        pos_anno.add_property("partno", partno)
        pos_anno.add_property("documentid", documentid)
        pos_anno.add_property("wordno", wordno)
        self.annotations.append(pos_anno)

        if lemma.strip() != self.absent_token_value:
            # Lemma annotation
            lemma_anno = catma.Annotation(self.tagset.get("lemma"))
            lemma_anno.ranges.append(tokenrange)
            lemma_anno.add_property("partno", partno)
            lemma_anno.add_property("documentid", documentid)
            lemma_anno.add_property("wordno", wordno)
            lemma_anno.add_property("lemma", lemma, adhoc=True)
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
