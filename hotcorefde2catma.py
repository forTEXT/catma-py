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
    if sourcetext_filename is not None:
        txt_file = open(
            sourcetext_filename,
            mode="r",
            buffering=-1,
            encoding='utf-8',
            errors=None,
            newline='')
        text = catma.remove_utf8bom(txt_file.read())
        txt_file.close()

    default_tags = {
        "pos_base": catma.Tag("POS", color=None, author=author),
        "sentence": catma.Tag("Sentence", color=None, author=author),
        "token": catma.Tag("Token", color=None, author=author),
        "lemma": catma.Tag("Lemma", color=None, author=author)
        }

    default_tokenhandler = conll12.DefaultTokenHandler(
        tagset=default_tags, author=author, text=text)

    hotcoref_tags = {
        "coref_base": catma.Tag("Coreference", color=None, author=author),
        "genus": catma.Tag("Genus", color=None, author=author),
        "numerus": catma.Tag("Numerus", color=None, author=author)
        }

    hotcoref_tokenhandler = hotcorefde.HotCorefDeTokenHandler(
        tagset=hotcoref_tags, author=author, text=text)

    conll12.LineParser().parse_file(
        filename=conll12_filename,
        linehandlers=(default_tokenhandler, hotcoref_tokenhandler))

    writer = catma.TEIAnnotationWriter(
        text,
        author,
        "HotCorefDe Annotations",
        (catma.Tagset("CoNLL12 NLP", default_tags), catma.Tagset("HotCorefDe", hotcoref_tags)),
        (default_tokenhandler.annotations, hotcoref_tokenhandler.annotations))
    writer.write_to_tei(tei_output_filename, write_on_stdout=False)

    print("conversion finished")


if __name__ == "__main__":
    SOURCETEXT_FILENAME = None

    if len(sys.argv) > 3:
        SOURCETEXT_FILENAME = sys.argv[3]

    convert_hotcorefde_to_catma("HotCorefDe", sys.argv[1], sys.argv[2], SOURCETEXT_FILENAME)
