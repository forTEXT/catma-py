# -*- coding: utf-8 -*-
"""
This modules converts the output of HotCorefDe
http://www.ims.uni-stuttgart.de/forschung/ressourcen/werkzeuge/HotCorefDe
to a CATMA Annotation Collection in TEI XML format.

@author: marco.petris@web.de
"""
import sys
import catma
import conll12
import hotcorefde


def convert_hotcorefde_to_catma(
        author, conll12_filename, tei_output_filename, sourcetext_filename=None):
    """
    author: The author of the Annotations.
    conll12_filename: The filename of the input file, the CoNLL-2012 anntotions.
    tei_output_filename: The filename of the output file.
    sourcetext_filename:
        The filename of the source text (optional). If absent the text gets
        constructed from the CoNLL-2012 input file.
    """

    text = None
    # load text if available
    if sourcetext_filename is not None:
        print("loading text...")
        txt_file = open(
            sourcetext_filename,
            mode="r",
            buffering=-1,
            encoding='utf-8',
            errors=None,
            newline='') #keep newlines as they are
        text = catma.remove_utf8bom(txt_file.read())
        txt_file.close()
        print("text loaded")
    # the default Tags for CoNLL-2012, the concrete pos Tags with 'POS' parent Tag
    # are written into this dictionary by the token-line handler
    # Properties are created as needed
    default_tags = {
        "pos_base": catma.Tag("POS", author=author),
        "sentence": catma.Tag("Sentence", author=author),
        "token": catma.Tag("Token", author=author),
        "lemma": catma.Tag("Lemma", author=author)
        }

    # a token-line handler for the default Tags
    default_tokenhandler = conll12.DefaultTokenHandler(
        tagset=default_tags, author=author, text=text)

    # HotCorefDe specific Tags, the concrete coreference Tags with 'coreference'
    # parent Tag will be written into this dictionary by the token-line handler
    # Properties are created as needed
    hotcoref_tags = {
        "coref_base": catma.Tag("Coreference", author=author),
        "genus": catma.Tag("Genus", author=author),
        "numerus": catma.Tag("Numerus", author=author)
        }

    # a token-line handler for HotCorefDe specific Tags
    hotcoref_tokenhandler = hotcorefde.HotCorefDeTokenHandler(
        tagset=hotcoref_tags, author=author, text=text)

    # parse the given CoNLL-2012 file
    # the given token handlers will contain the Tags and Annotations extracted
    # from the CoNLL-2012 input file
    print("parsing file for Tags and Annotations...")
    conll12.LineParser().parse_file(
        filename=conll12_filename,
        linehandlers=(default_tokenhandler, hotcoref_tokenhandler))
    print("parsing finished")

    # writing Tags and Annotation to a CATMA Annotation Collection in TEI-XML
    # format, the result will contain a 'CoNLL12 NLP' Tagset and a 'HotCorefDe'
    # Tagset and all the corresponding Annotations
    print("writing Tags and Annotations to TEI-XML...")
    writer = catma.TEIAnnotationWriter(
        len(text),
        "HotCorefDe Annotations", [
            catma.Tagset("CoNLL12 NLP", default_tags.values()),
            catma.Tagset("HotCorefDe", hotcoref_tags.values())],
        [default_tokenhandler.annotations, hotcoref_tokenhandler.annotations],
        author=author)
    writer.write_to_tei(tei_output_filename, write_on_stdout=False)

    print("conversion finished")


if __name__ == "__main__":
    SOURCETEXT_FILENAME = None

    if len(sys.argv) > 3:
        SOURCETEXT_FILENAME = sys.argv[3]

    convert_hotcorefde_to_catma("HotCorefDe", sys.argv[1], sys.argv[2], SOURCETEXT_FILENAME)
