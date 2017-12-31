# -*- coding: utf-8 -*-
"""
This module includes various function and classes to build CATMA Tagset, Tag and
Annotation structures. It also provides a writer that generates CATMA TEI XML
from these structures to import Annotation collections into CATMA http://www.catma.de

@author: marco.petris@web.de
"""
import uuid
import xml.etree.ElementTree as XML
import random
import datetime

# The version of the generated CATMA import/export file format
CATMA_TEI_VERSION = 4

def remove_utf8bom(text):
    """
    Removes all occurrences! of the utf8 Byte Order mark from the given text
    and returns the modified version.
    """

    return text.replace(u'\ufeff', "")

def generate_random_color():
    """
    Generates a random color as an integer representing an RGB color
	 consisting of the red component in bits 16-23, the green component in bits 8-15,
	 and the blue component in bits 0-7.
    """

    red = random.randrange(256)
    green = random.randrange(256)
    blue = random.randrange(256)
    return ((0 & 0xFF) << 24) \
        | ((red & 0xFF) << 16) \
        | ((green & 0xFF) << 8) \
        | ((blue & 0xFF) << 0)

def gettimestamp():
    """
    Returns a timestamp as str with milliseconds and timezone offset.
    """
    timestamp = datetime.datetime.now(
        datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        ).strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    return timestamp[:-8]+timestamp[-5:]

def get_catma_uuid_as_str(provider):
    """
    Returns the uuid of the given provider as a CATMA uuid as str.
    """
    return "CATMA_"+str(provider.uuid).upper()

class Tag(object):
    """
    Represents a CATMA Tag, i. e. the type or code of an Annotation.
    """
    def __init__(self, name, color=generate_random_color(), author="Unknown", parent=None):
        """
        Constructs a Tag with a name, an optional color which defaults to a 
        random color, an optional author which defaults to "Unknown" and an optional
        parent Tag which defaults to None for root Tags.
        """
        self.name = name
        self.uuid = uuid.uuid4()
        self.parent = parent
        self.color = color

        self.properties = {}
        self.add_or_update_property("catma_displaycolor", self.color, False)
        self.add_or_update_property("catma_markupauthor", author, False)

    def add_or_update_property(self, name, value, adhoc):
        if name not in self.properties.keys():
            values = set()
            if not adhoc:
                values.add(str(value))
            self.properties[name] = Property(name, values)
        if not adhoc:
            self.properties[name].values.add(str(value))


    def __str__(self):
        return self.name

class Property(object):
    def __init__(self, name, values):
        self.name = name
        self.values = values
        self.uuid = uuid.uuid4()

class Tagset(object):
    def __init__(self, name, tags):
        self.name = name
        self.uuid = uuid.uuid4()
        self.tags = tags
    def __str__(self):
        return self.name

class Annotation(object):
    def __init__(self, tag):
        self.uuid = uuid.uuid4()
        self.tag = tag
        self.properties = {}
        self.ranges = []
    def __str__(self):
        return str(self.tag) + "@" + str(self.ranges) + " with " + str(self.properties)

    def addproperty(self, name, value, adhoc=False):
        self.properties[name] = value
        self.tag.add_or_update_property(name, value, adhoc)


class Range(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def get_overlapping_range(self, other):
        if other.start == self.end or self.start == other.end:
            return None

        if self.is_in_between_inclusive_edge(other.start):
            if self.is_in_between_inclusive_edge(other.end):
                return Range(other.start, other.end)
            elif self.is_after(other.end):
                return Range(other.start, self.end)
        elif not self.is_after(other.start):
            if self.is_in_between_inclusive_edge(other.end):
                return Range(self.start, other.end)
            elif self.is_after(other.end):
                return Range(self.start, self.end)

        return None

    def is_in_between(self, other):
        return self.start >= other.start and self.end <= other.end

    def has_overlapping_range(self, other):
        return self.get_overlapping_range(other) is not None

    def get_overlapping_ranges(self, ranges):
        overlapping_ranges = list()
        for other in ranges:
            if self.has_overlapping_range(other):
                overlapping_ranges.append(other)
        return overlapping_ranges

    def get_disjoint_ranges(self, other):
        result = list()
        if self.is_in_between_exclusive_edge(other.start):
            result.append(Range(self.start, other.start))

            if self.is_in_between_exclusive_edge(other.end):
                result.append(Range(other.end, self.end))
        elif not self.is_after(other.end):
            result.append(Range(other.end, self.end))

        return result

    def is_in_between_inclusive_edge(self, point):
        return point >= self.start and point <= self.end

    def is_in_between_exclusive_edge(self, point):
        return point > self.start and point < self.end

    def is_after(self, point):
        return self.end < point

    def __hash__(self):
        return hash((self.start, self.end))

    def __eq__(self, other):
        return (self.start, self.end) == (other.start, other.end)

    def __ne__(self, other):
        return not self == other

    def __le__(self, other):
        if self.start <= other.start:
            return self.end <= other.end
        return False

    def __lt__(self, other):
        if self.start < other.start:
            return True
        elif self.start == other.start:
            return self.end < other.end

        return False

    def __ge__(self, other):
        if self.start >= other.start:
            return self.end >= other.end
        return False

    def __gt__(self, other):
        if self.start > other.start:
            return True
        elif self.start == other.start:
            return self.end > other.end

        return False
    def __str__(self):
        return "[" + str(self.start) + "," + str(self.end) + "]"

    @classmethod
    def as_ranges(cls, tupel_list):
        result = list()
        for other in tupel_list:
            result.append(Range(other[0], other[1]))
        return result


class TEIAnnotationWriter(object):
    def __init__(self, text, author, title, tagsets, annotations_list):
        self.text = text
        self.author = author
        self.title = title
        self.tagsets = tagsets
        self.annotations_list = annotations_list

    def write_to_tei(self, filename=None, write_on_stdout=True):
        documentid = uuid.uuid4()
        tei_el = XML.Element("TEI", {"xml:lang": "en", "xmlns": "http://www.tei-c.org/ns/1.0"})
        header_el = XML.SubElement(tei_el, "teiHeader")
        text_el = XML.SubElement(tei_el, "text")
        body_el = XML.SubElement(text_el, "body")
        ab_el = XML.SubElement(body_el, "ab", {"type": "catma"})

        self.write_filedesc(header_el)
        self.write_tagsets(header_el)
        self.write_annotations(text_el, ab_el, documentid)

        if write_on_stdout:
            XML.dump(tei_el)
        if filename is not None:
            #print(XML.tostring(tei_el, pretty_print=True))
            XML.ElementTree(tei_el).write(file_or_filename=filename, encoding="utf-8")

    def write_tagsets(self, tei_el):
        encodingdesc_el = XML.SubElement(tei_el, "encodingDesc")
        for tagset in self.tagsets:
            fsddecl_el = XML.SubElement(
                encodingdesc_el,
                "fsdDecl",
                {"xml:id": get_catma_uuid_as_str(tagset),
                 "n": tagset.name+" "+gettimestamp()})
            for tag in tagset.tags.values():
                attr = {"xml:id": get_catma_uuid_as_str(tag),
                        "n": gettimestamp(),
                        "type": get_catma_uuid_as_str(tag)}
                if tag.parent is not None:
                    attr["baseTypes"] = get_catma_uuid_as_str(tag.parent)

                fsdecl_el = XML.SubElement(
                    fsddecl_el,
                    "fsDecl",
                    attr)
                fsdescr_el = XML.SubElement(fsdecl_el, "fsDescr")
                fsdescr_el.text = tag.name

                for prop in tag.properties.values():
                    fdecl_el = XML.SubElement(
                        fsdecl_el,
                        "fDecl",
                        {"xml:id": get_catma_uuid_as_str(prop), "name": prop.name})

                    vrange_el = XML.SubElement(fdecl_el, "vRange")
                    vcoll_el = XML.SubElement(vrange_el, "vColl")
                    for val in prop.values:
                        str_el = XML.SubElement(vcoll_el, "string")
                        str_el.text = str(val)


    def write_filedesc(self, header_el):
        filedesc_el = XML.SubElement(header_el, "fileDesc")
        titlestmt_el = XML.SubElement(filedesc_el, "titleStmt")
        title_el = XML.SubElement(titlestmt_el, "title")
        title_el.text = self.title
        author_el = XML.SubElement(titlestmt_el, "author")
        author_el.text = self.author
        publicationstmt_el = XML.SubElement(filedesc_el, "publicationStmt")
        publisher_el = XML.SubElement(publicationstmt_el, "publisher")
        publisher_el.text = self.author
        sourcedesc_el = XML.SubElement(filedesc_el, "sourceDesc")
        p_el = XML.SubElement(sourcedesc_el, "p")
        p_el.text = self.title
        ab_el = XML.SubElement(sourcedesc_el, "ab")
        fs_el = XML.SubElement(ab_el, "fs", {"xml:id": "CATMA_TECH_DESC"})
        f_el = XML.SubElement(fs_el, "f", {"name": "version"})
        string_el = XML.SubElement(f_el, "string")
        string_el.text = str(CATMA_TEI_VERSION)


    def add_ptr(self, parent, documentid, anno_range):
        XML.SubElement(
            parent,
            "ptr",
            {"target":
             "catma://CATMA_"
                 +str(documentid).upper()
                 +"#char="+str(anno_range.start)
                 +","
                 +str(anno_range.end),
             "type": "inclusion"})

    def as_uuid_list(self, annotations):
        return ["#"+get_catma_uuid_as_str(anno) for anno in annotations]

    def merge_ranges(self, annotations):
        merged_ranges = {Range(0, len(self.text)): list()}
        counter = 0
        for anno in annotations:
            counter += 1
            for target_range in anno.ranges:
                affected_ranges = target_range.get_overlapping_ranges(
                    merged_ranges.keys())

                for affected_range in affected_ranges:

                    if affected_range.is_in_between(target_range):
                        merged_ranges[affected_range].append(anno)
                    else:
                        affected_annotations = merged_ranges.get(affected_range)

                        overlapping_range = affected_range.get_overlapping_range(target_range)

                        disjoint_ranges = affected_range.get_disjoint_ranges(target_range)

                        first_disjoint_range = disjoint_ranges[0]
                        merged_ranges[first_disjoint_range] = affected_annotations.copy()

                        if len(disjoint_ranges) == 2:
                            second_disjoint_range = disjoint_ranges[1]
                            merged_ranges[second_disjoint_range] = affected_annotations.copy()

                        affected_annotations.append(anno)
                        merged_ranges[overlapping_range] = affected_annotations
                        merged_ranges.pop(affected_range)

        return merged_ranges


    def write_annotations(self, text_el, ab_el, documentid):
        all_annotations = list()
        for annotations in self.annotations_list:
            all_annotations += annotations
        merged_ranges = self.merge_ranges(all_annotations)


        for anno_range in sorted(merged_ranges):
            annotations = merged_ranges[anno_range]
            if not annotations:
                self.add_ptr(ab_el, documentid, anno_range)
            else:
                seg = XML.SubElement(
                    ab_el,
                    "seg",
                    {"ana": " ".join(self.as_uuid_list(annotations))})
                self.add_ptr(seg, documentid, anno_range)

        for anno in all_annotations:
            self.write_annotation(text_el, anno)

    def write_annotation(self, text_el, anno):
        attributes = {
            "xml:id": get_catma_uuid_as_str(anno),
            "type": get_catma_uuid_as_str(anno.tag)}
        fs_el = XML.SubElement(text_el, "fs", attributes)
        self.write_anno_property(fs_el, "catma_markupauthor", self.author)
        self.write_anno_property(fs_el, "catma_displaycolor", str(anno.tag.color))

        for prop_key in anno.properties.keys():
            self.write_anno_property(fs_el, prop_key, str(anno.properties[prop_key]))

    def write_anno_property(self, fs_el, name, value):
        prop_el = XML.SubElement(fs_el, "f", {"name": name})
        prop_str_el = XML.SubElement(prop_el, "string")
        prop_str_el.text = value
