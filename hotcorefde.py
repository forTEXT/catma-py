# -*- coding: utf-8 -*-
"""
Provides a token line handler for the conll12.LineParser to read the HotCorefDe
output (coreference, numerus and genus) into CATMA Annotations as generated
by http://www.ims.uni-stuttgart.de/forschung/ressourcen/werkzeuge/HotCorefDe

@author: marco.petris@web.de
"""
import re
import catma
import conll12

class Coref(object):
    """
    Helper class to keep track of coreferences during parsing.
    """
    PATTERN = re.compile(r"(\()?(\d+)(\))?")
    GROUP_OPENPAR = 1
    GROUP_INDEX = 2
    GROUP_CLOSEPAR = 3
    def __init__(self, value, absent_token_value):
        matchresult = Coref.PATTERN.match(value)

        self.isset = (value != absent_token_value)
        if self.isset:
            self.isopened = matchresult.group(Coref.GROUP_OPENPAR) is not None
            self.isclosed = matchresult.group(Coref.GROUP_CLOSEPAR) is not None
            self.index = int(matchresult.group(Coref.GROUP_INDEX))
        else:
            self.isopened = False
            self.isclosed = False
            self.index = -1

        self.startidx = -1
        self.endidx = -1

    def iscomplete(self):
        return self.isclosed and self.isopened

    def get_range(self):
        return catma.Range(self.startidx, self.endidx)

    def __str__(self):
        res = list()
        if self.isopened:
            res.append("(")
        res.append(str(self.index))
        if self.isclosed:
            res.append(")")
        res.append("[")
        res.append(str(self.startidx))
        res.append(",")
        res.append(str(self.endidx))
        res.append("]")

        return "".join(res)

class HotCorefDeTokenHandler(conll12.BaseTokenHandler):
    """
    A token line handler for the conll12.LineParser to read the HotCorefDe
    coreference, numerus and genus into CATMA Annotations, which can be
    retrieved by the 'annotations' property.
    """
    def __init__(self, tagset, author, text=None, tokensep="\t", absent_token_value="-"):
        """
        Constructs a HotCorefDeTokenHandler with a Tagset providing the
        Tags 'genus', 'numerus' and 'coref_base'.
        Details:
            genus:
                Column 8 in the COnLL-2012 format, custom addition by HotCorefDe
            numerus:
                Column 9 in the COnLL-2012 format, custom addition by HotCorefDe
            coref_base:
                Column 13. Each coreference gets its own Tag named Coreferenc[index]. With index
                being an incremented number starting with 0. The coreference Tags have
                coref_base as their parent Tag.
        """
        super().__init__(text=text)
        self.tagset = tagset
        self.author = author
        self.tokensep = tokensep
        self.absent_token_value = absent_token_value

        self.annotations = list()
        self.opencorefs = dict()

    def token(self, token_line, sentenceno):
        """
        This method gets called by the LineParser which provides the current
        token_line and the current sentenceno. It reads columns
        8, 9 and 13 into CATMA Annotation structures (property annotations).
        """
        entries = token_line.split(sep=self.tokensep)
        documentid = entries[0]
        partno = entries[1]
        wordno = entries[2]
        word = entries[3]
        pos = entries[4]
        parsebit = entries[5]
        numerus = entries[7]
        genus = entries[8]

        tokenrange = self.get_token_range(word)

        # genus annotation
        genus_anno = catma.Annotation(self.tagset.get("genus"))
        genus_anno.ranges.append(tokenrange)
        genus_anno.addproperty("partno", partno)
        genus_anno.addproperty("documentid", documentid)
        genus_anno.addproperty("wordno", wordno)
        genus_anno.addproperty("pos", pos)
        genus_anno.addproperty("parsebit", parsebit)
        genus_anno.addproperty("genus", genus)
        self.annotations.append(genus_anno)

        # numerus annotation
        numerus_anno = catma.Annotation(self.tagset.get("numerus"))
        numerus_anno.ranges.append(tokenrange)
        numerus_anno.addproperty("partno", partno)
        numerus_anno.addproperty("documentid", documentid)
        numerus_anno.addproperty("wordno", wordno)
        numerus_anno.addproperty("pos", pos)
        numerus_anno.addproperty("parsebit", parsebit)
        numerus_anno.addproperty("numerus", numerus)
        self.annotations.append(numerus_anno)

        # coreference annotations
        # may be multiple coreferences concatenated by |
        for entry in entries[13].strip().split("|"):
            coref = Coref(entry, self.absent_token_value)

            if coref.isset:
                if coref.iscomplete():
                    coref.startidx, coref.endidx = tokenrange.start, tokenrange.end
                    self.add_coref_anno(coref)
                elif coref.isopened:
                    if coref.index not in self.opencorefs.keys():
                        self.opencorefs[coref.index] = list()
                    coref.startidx = tokenrange.start
                    self.opencorefs[coref.index].append(coref)
                elif coref.isclosed:
                    try:
                        open_coref = self.opencorefs[coref.index].pop()
                        open_coref.endidx = tokenrange.end
                        self.add_coref_anno(open_coref)
                    except IndexError:
                        print(
                            "WARNING: ignoring dangling coreference "
                            + str(coref.index) + " at line " + token_line)

        self.current_text_pos = tokenrange.end


    def add_coref_anno(self, coref):
        key = "coref" + str(coref.index)
        if key not in self.tagset.keys():
            self.tagset[key] = \
                catma.Tag(
                    "Coref" + str(coref.index),
                    color=None,
                    author=self.author,
                    parent=self.tagset["coref_base"])
        coref_anno = catma.Annotation(self.tagset.get(key))
        coref_anno.ranges.append(coref.get_range())
        coref_anno.addproperty("index", coref.index)
        # coref_anno.addproperty("text", self.get_text()[coref.startidx:coref.endidx], adhoc=True)
        self.annotations.append(coref_anno)
