# -*- coding: utf-8 -*-
"""
This module includes various function and classes to build CATMA Tagset, Tag and
Annotation structures. It also provides a writer that generates CATMA TEI XML
from these structures to import Annotation collections into CATMA http://www.catma.de
and a reader that consumes Annotation collection in CATMA TEI XML and builds the above
mentioned structures for further processing.
@author: marco.petris@web.de
"""
import uuid
import xml.etree.ElementTree as XML
import random
import datetime
import string

# The version of the generated CATMA import/export file format
CATMA_TEI_VERSION = 5
TEI_NAMESPACE_MAPPING = {"tei": "http://www.tei-c.org/ns/1.0"}


def remove_utf8bom(text: str) -> str:
    """
    Removes all occurrences! of the utf8 Byte Order mark from the given text
    and returns the modified version.
    
    :param text: a given text
    :return: the text without BOM
    """
    return text.replace(u'\ufeff', "")


def generate_random_color() -> int:
    """
    Generates a random color as an integer representing an RGB color
    consisting of the red component in bits 16-23, the green component in bits 8-15,
    and the blue component in bits 0-7.

    :return: an integer that represents the computed color
    """

    red = random.randrange(256)
    green = random.randrange(256)
    blue = random.randrange(256)
    return ((255 & 0xFF) << 24) \
           | ((red & 0xFF) << 16) \
           | ((green & 0xFF) << 8) \
           | ((blue & 0xFF) << 0)


def gettimestamp() -> str:
    """
    :return a timestamp as str with milliseconds and timezone offset with the format %Y-%m-%dT%H:%M:%S.%f%z
    """
    timestamp = datetime.datetime.now(
        datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    ).strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    return timestamp[:-8] + timestamp[-5:]


def get_catma_uuid_as_str(provider) -> str:
    """
    :return: the uuid of the given provider as a CATMA uuid as str.
    """
    return "CATMA_" + str(provider.uuid).upper()


def get_xml_node_id(node: XML) -> str:
    """
    Retrieves the xml:id of the given node.

    :param node: the XML node
    :return: the xml:id as a str or None
    """
    return node.get('{http://www.w3.org/XML/1998/namespace}id')


def get_uuid_from_catma_uuid_str(catma_uuid: str) -> uuid.UUID:
    """
    Retrieves a uuid from the given input

    :param catma_uuid: a CATMA uuid like CATMA_8DF8AB1D-002F-4693-AB9B-96DAF9D1BA87
    :return: the corresponding uuid object, e. g. 8DF8AB1D-002F-4693-AB9B-96DAF9D1BA87
    """

    if catma_uuid.startswith("CATMA"):
        return uuid.UUID(catma_uuid[6:])

    # CATMA 6 Tagset-ID starts with T, Document-ID starts with D, Collection-ID starts with C

    return uuid.UUID(catma_uuid[2:])

class Property(object):
    """
    Represents a CATMA Property of a Tag.
    """

    def __init__(self, name, values=(), prop_uuid: uuid.UUID = None):
        """
        Constructs a Property.

        :param name: the name of the Property
        :param values: the possible or proposed values of the Property, optional, defaults to an empty set
        :param prop_uuid: the uuid of the property, optional defaults to a newly generated uuid
        """
        self.name = name
        self.values = list(values)
        if prop_uuid is not None:
            self.uuid = prop_uuid
        else:
            self.uuid = uuid.uuid4()

    def __repr__(self):
        return self.name + " #" + str(self.uuid) + " " + str(self.values)


class Tag(object):
    """
    Represents a CATMA Tag, i. e. the type or code of an Annotation.
    """

    def __init__(self, name: str, tag_uuid: uuid.UUID = None, version: str = None, color: int = None,
                 color_prop_uuid:uuid.UUID=None, author: str = "empty", author_prop_uuid:uuid.UUID = None, parent=None):
        """
        Constructs a Tag.

        :param name: the name of the Tag
        :param tag_uuid: the uuid of the Tag, optional, defaults to a newly generated uuid
        :param version: a version string with the format %Y-%m-%dT%H:%M:%S.%f%z, optional, defaults to a new version
        :param color: the color of the Tag, optional, defaults to a random color
        :param color_prop_uuid: the uuid of the color Property, optional, defaults to a newly generated uuid
        :param author: the author of the Tag, optional, defaults to "empty"
        :param author_prop_uuid: the uuid of the author Property, optional, defaults to a newly generated uuid
        :param parent: the parent Tag, optional, defaults to None for root Tags
        """
        self.name = name
        if tag_uuid is not None:
            self.uuid = tag_uuid
        else:
            self.uuid = uuid.uuid4()

        if version is not None:
            self.version = version
        else:
            self.version = gettimestamp()

        self.parent = parent

        if color is None:
            self.color = generate_random_color()
        else:
            self.color = color

        self.properties = {}
        self.add_or_update_property(name="catma_displaycolor", value=str(self.color), prop_uuid=color_prop_uuid, adhoc=False)
        self.add_or_update_property(name="catma_markupauthor", value=author, prop_uuid=author_prop_uuid, adhoc=False)

    def add_or_update_property(self, name: str, value: str, prop_uuid: uuid.UUID=None, adhoc=True):
        """
        Adds a Property with the given name if not present. If the value is not an
        adhoc value it gets added to the list of possible values for the Property.

        :param name: the name of the Property
        :param value: the value of the Property
        :param prop_uuid: the uuid of the Property, optional, defaults to a newly generated uuid for new Properties
        :param adhoc: flag indicates if the value should be added to the list of proposed values (True) or not (False)
        """
        if name not in self.properties.keys():
            values = set()
            if not adhoc:
                values.add(str(value))
            self.properties[name] = Property(name=name, values=values, prop_uuid=prop_uuid)
        elif not adhoc and str(value) not in self.properties[name].values:
            self.properties[name].values.append(str(value))

    def add_property(self, property: Property):
        """
        Adds the Property to the this Tag.

        :param property: the Property to be added
        """
        self.properties[property.name] = property

    def get_path(self):
        """
        :return: the hierarchy path of this Tag, e.g. /myroottag/mytag
        """
        if self.parent is None:
            return "/" + self.name
        else:
            return self.parent.get_path() + "/" + self.name

    def __repr__(self):
        return self.name + " #" + str(self.uuid)


class Tagset(object):
    """
    Represents a CATMA Tagset.
    """

    def __init__(self, name: str, tags=(), version: str = None, tagset_uuid: uuid.UUID = None):
        """
        Constructs a Tagset.

        :param name: the name of the Tagset
        :param tags: a set of initial Tags
        :param version: a version string with the format %Y-%m-%dT%H:%M:%S.%f%z, optional, defaults to a new version
        :param tagset_uuid: the uuid of the Tagset, optional, defaults to a newly generated uuid
        """
        self.name = name
        if version is not None:
            self.version = version
        else:
            self.version = gettimestamp()
        if tagset_uuid is not None:
            self.uuid = tagset_uuid
        else:
            self.uuid = uuid.uuid4()

        self.tags = {}
        for tag in tags:
            self.tags[tag.uuid] = tag

    def __repr__(self):
        return self.name

    def add_tag(self, tag: Tag):
        """
        Adds a Tag to this Tagset.

        :param tag: the Tag to be added
        """
        self.tags[tag.uuid] = tag

    def get_tag_by_path(self, path: str) -> str:
        """
        :param path: the path of the Tag
        :return: the Tag for the given path or None if there is no such Tag
        """
        for tag in self.tags.values():
            if tag.get_path() == path:
                return tag

        return None


class Annotation(object):
    """
    Represents a CATMA Annotation, typed by a Tag. An Annotation has a collection
    of Ranges that reference the text segments and a dictionary of key-valueset properties.
    """

    def __init__(self, tag: Tag, anno_uuid: uuid.UUID = None):
        """
        Constructs an Annotation with its Tag.

        :param tag: the Tag for the Annotation
        :param anno_uuid: the uuid of the Annotation, optional, defaults to a newly generated uuid
        """
        if anno_uuid is not None:
            self.uuid = anno_uuid
        else:
            self.uuid = uuid.uuid4()
        self.tag = tag
        self.properties = {}
        self.ranges = []

    def __repr__(self):
        return str(self.tag) + "@" + str(self.ranges) + " with " + str(self.properties)

    def add_property(self, name: str, value: str, adhoc=False):
        """
        Adds a property value to the named property of this Annotation.
        If the value is not an adhoc value, it gets added to the possible values
        set of the Property definition of the Tag.

        :param name: the name of the Property
        :param value: the value of the Property
        :param adhoc: flag indicates if the value should also be added to the possible values of the Tag (False) or not (True)
        """
        if name not in self.properties.keys():
            self.properties[name] = set()

        self.properties[name].add(str(value))

        self.tag.add_or_update_property(name=name, value=value, adhoc=adhoc)


class Range(object):
    """
    Represents a segment of text by its start and end character offsets.
    """

    def __init__(self, start: int, end: int):
        """
        Constructs a Range with start and end character offsets.

        :param start: start offset
        :param end: end offset
        """
        self.start = start
        self.end = end

    def get_overlapping_range(self, other):
        """
        Returns the overlapping Range of ths Range and the other Range if there
        is one else None.

        :param other the other Range to test for
        """
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

    def is_in_between(self, other) -> bool:
        """
        :return: True if the other Range is in between this Range.
        """
        return self.start >= other.start and self.end <= other.end

    def has_overlapping_range(self, other) -> bool:
        """
        :return: True if this Range and the other Range have an overlapping Range.
        """
        return self.get_overlapping_range(other) is not None

    def get_overlapping_ranges(self, ranges) -> list:
        """
        :return: a possibly empty list of overlapping Ranges between this Range
        and the given Ranges.
        """
        overlapping_ranges = list()
        for other in ranges:
            if self.has_overlapping_range(other):
                overlapping_ranges.append(other)
        return overlapping_ranges

    def get_disjoint_ranges(self, other) -> list:
        """
        :return: zero, one or two disjoint Ranges between this Range and the
        other Range.
        """
        result = list()
        if self.is_in_between_exclusive_edge(other.start):
            result.append(Range(self.start, other.start))

            if self.is_in_between_exclusive_edge(other.end):
                result.append(Range(other.end, self.end))
        elif not self.is_after(other.end):
            result.append(Range(other.end, self.end))

        return result

    def is_in_between_inclusive_edge(self, point: int) -> bool:
        """
        :return: True if the given point is within the bounds of this Range edges
        included.
        """
        return point >= self.start and point <= self.end

    def is_in_between_exclusive_edge(self, point: int) -> bool:
        """
        :return: True if the given point is within the bounds of this Range edges
        excluded.
        """
        return point > self.start and point < self.end

    def is_after(self, point: int) -> bool:
        """
        :return: True if the given point is after the end of this Range.
        """
        return self.end < point

    def is_point(self) -> bool:
        """
        :return: true if this range represents a single point
        """
        return self.start == self.end

    def __hash__(self):
        return hash((self.start, self.end))

    def __eq__(self, other):
        """
        Equality by start and end offsets.
        """
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

    def __repr__(self):
        return "[" + str(self.start) + "," + str(self.end) + "]"

    @classmethod
    def as_ranges(cls, tupel_list: list) -> list:
        """
        :return: a list of Ranges out of the given list of pairs of start offset
        and end offset.
        """
        return [Range(other[0], other[1]) for other in tupel_list]

    @staticmethod
    def merge_ranges(sorted_ranges: list) -> list:
        """
        :param sorted_ranges: a list of Ranges sorted by start/end
        :return: a list of merged ranges, i. e. all contiguous ranges are combined into one
        """
        result = list()
        if len(sorted_ranges) == 0:
            return []

        cur_range = None

        for range in sorted_ranges:
            if cur_range is None:
                cur_range = range
            else:
                if cur_range.end == range.start:
                    cur_range = Range(cur_range.start, range.end)
                else:
                    result.append(cur_range)
                    cur_range = range

        result.append(cur_range)

        return result


def extract_range(target: str) -> Range:
    """
    Extracts a Range from a <ptr> target attribute.

    :param target: a <ptr> target like catma://CATMA_0854DF2F-9527-428E-B753-84C0710AFDA5#char=42,48
    :return: a Range with the target offsets
    """
    range_str = target[target.rfind("=") + 1:]
    range_offsets = range_str.split(",")
    return Range(int(range_offsets[0]), int(range_offsets[1]))


class TEIAnnotationWriter(object):
    """
    Writes CATMA Annotations along with their Tag information as a TEI XML formatted
    document. The format follows the CATMA TEI Import Export format as described here:
    http://catma.de/documentation/technical-specs/tei-export-format/
    """

    def __init__(self, text_length: int, title: str, tagsets: list, annotations_list: list, author: str = None,
                 documentid: str = None):
        """
        Constructs a TEIAnnotationWriter.

        :param text_length: the length of the annotated text in characters.
        :param title: the title of the resulting Collection
        :param tagsets: the participating tagsets
        :param annotations_list: a list of annotation lists
        :param author: the author of the resulting Collection, optional, defaults to "empty"
        :param documentid: the ID of the annotated document, optional, defaults to a newly generated uuid
        """

        self.text_length = text_length
        if author is not None:
            self.author = author
        else:
            self.author = "empty"
        self.title = title
        if documentid is not None:
            self.documentid = documentid
        else:
            self.documentid = uuid.uuid4()
        self.tagsets = tagsets
        self.annotations_list = annotations_list

    def write_to_tei(self, filename: str = None, write_on_stdout=True):
        """
        Writes the data of this TEIAnnotationWriter to a file with the given full
        filename. Writes also to stdout if write_on_stdout is True (default)

        :param filename: then full path of the output file
        :param write_on_stdout: if True the result is also printed to stdout
        """
        tei_el = XML.Element("TEI", {"xml:lang": "en", "xmlns": TEI_NAMESPACE_MAPPING["tei"]})
        header_el = XML.SubElement(tei_el, "teiHeader")
        text_el = XML.SubElement(tei_el, "text")
        body_el = XML.SubElement(text_el, "body")
        ab_el = XML.SubElement(body_el, "ab", {"type": "catma"})

        self.write_filedesc(header_el)
        self.write_tagsets(header_el)
        self.write_annotations(text_el, ab_el, self.documentid)

        if write_on_stdout:
            XML.dump(tei_el)
        if filename is not None:
            # print(XML.tostring(tei_el, pretty_print=True))
            XML.ElementTree(tei_el).write(file_or_filename=filename, xml_declaration=True, encoding="utf-8", method="xml")

    def write_tagsets(self, tei_el: XML):
        encodingdesc_el = XML.SubElement(tei_el, "encodingDesc")
        for tagset in self.tagsets:
            fsddecl_el = XML.SubElement(
                encodingdesc_el,
                "fsdDecl",
                {"xml:id": get_catma_uuid_as_str(tagset),
                 "n": tagset.name + " " + tagset.version})
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

    def write_filedesc(self, header_el: XML):
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

    def add_ptr(self, parent, documentid: str, anno_range: Range):
        XML.SubElement(
            parent,
            "ptr",
            {"target":
                 "catma://CATMA_"
                 + str(documentid).upper()
                 + "#char=" + str(anno_range.start)
                 + ","
                 + str(anno_range.end),
             "type": "inclusion"})

    def as_uuid_list(self, annotations: list) -> list:
        return ["#" + get_catma_uuid_as_str(anno) for anno in annotations]

    def merge_ranges(self, annotations: list) -> dict:
        # creates a dictionary of non overlapping ranges and their
        # corresponding annotations.
        merged_ranges = {Range(0, self.text_length): list()}
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

    def write_annotations(self, text_el: XML, ab_el: XML, documentid: str):
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

    def write_annotation(self, text_el: XML, anno: Annotation):
        attributes = {
            "xml:id": get_catma_uuid_as_str(anno),
            "type": get_catma_uuid_as_str(anno.tag)}
        fs_el = XML.SubElement(text_el, "fs", attributes)

        # add provided author if not already present
        if "catma_markupauthor" not in anno.properties:
            self.write_anno_property(fs_el, "catma_markupauthor", [self.author])

        # add color value from Tag if not already present
        if "catma_displaycolor" not in anno.properties:
            self.write_anno_property(fs_el, "catma_displaycolor", [str(anno.tag.color)])

        for prop_key in anno.properties.keys():
            self.write_anno_property(fs_el, prop_key, anno.properties[prop_key])

    def write_anno_property(self, fs_el: XML, name: str, values: list):
        prop_el = XML.SubElement(fs_el, "f", {"name": name})
        for value in values:
            prop_str_el = XML.SubElement(prop_el, "string")
            prop_str_el.text = value


class TEIAnnotationReader(object):
    """
    Reads an Annotation Collection with all Tagsets and Annotation to the CATMA data structures. The format of the input
    file must follow the CATMA TEI Import Export format as described here:
    http://catma.de/documentation/technical-specs/tei-export-format/
    After construction the reader provides a list of tagsets, a list of annotations and meta data such as version, title,
    author, publisher, description
    """
    def __init__(self, filename: str, no_ptr_refs_should_raise: bool = True):
        """
        Constructs the reader and loads the given file.

        :param filename: input file in CATMA TEI format
        """
        self.tagsets = []
        self.annotations = []

        XML.register_namespace("", TEI_NAMESPACE_MAPPING["tei"])
        doc = XML.parse(filename)

        self.read_metadata(doc)

        has_ptr_refs = doc.find("./tei:text/tei:body/tei:ab//tei:ptr", TEI_NAMESPACE_MAPPING) is not None
        if not has_ptr_refs and no_ptr_refs_should_raise:
            raise Exception("This collection does not use <ptr> references and is not supported by this parser!")
        elif has_ptr_refs:
            self.text_length, self.documentid = self.extract_pointer_document_properties(doc)

        self.read_tagsets(doc)
        self.read_annotations(doc)

    def read_metadata(self, doc: XML):
        version_node = doc.find(
            "./tei:teiHeader/tei:fileDesc/tei:sourceDesc/tei:ab/tei:fs/tei:f[@name='version']/tei:string",
            TEI_NAMESPACE_MAPPING)
        if version_node is not None:
            self.version = int(version_node.text)
        else:
            self.version = 0

        if self.version != CATMA_TEI_VERSION:
            raise Exception("This parser can only handle CATMA collections with version " + str(CATMA_TEI_VERSION))

        title_node = doc.find("./tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title", TEI_NAMESPACE_MAPPING)
        if title_node is not None:
            self.title = title_node.text
        else:
            self.title = "empty"

        author_node = doc.find("./tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:author", TEI_NAMESPACE_MAPPING)
        if author_node is not None:
            self.author = author_node.text
        else:
            self.author = "empty"

        publisher_node = doc.find("./tei:teiHeader/tei:fileDesc/tei:publicationStmt/tei:publisher",
                                  TEI_NAMESPACE_MAPPING)
        if publisher_node is not None:
            self.publisher = publisher_node.text
        else:
            self.publisher = "empty"

        description_node = doc.find("./tei:teiHeader/tei:fileDesc/tei:sourceDesc/tei:p", TEI_NAMESPACE_MAPPING)
        if description_node is not None:
            self.description = description_node.text
        else:
            self.description = "empty"

    def extract_pointer_document_properties(self, doc: XML) -> tuple:
        ptr_elements = doc.findall("./tei:text/tei:body/tei:ab//tei:ptr", TEI_NAMESPACE_MAPPING)
        last_ptr_element = ptr_elements[len(ptr_elements) - 1]
        target = last_ptr_element.get("target")
        last_range = extract_range(target)
        return last_range.end, self.extract_documentid(target)

    def get_tag(self, uuid: uuid.UUID) -> Tag:
        for tagset in self.tagsets:
            if uuid in tagset.tags:
                return tagset.tags[uuid]

        return None

    def read_annotations(self, doc: XML):
        annotation_nodes = doc.findall(".//tei:text/tei:fs", TEI_NAMESPACE_MAPPING)
        ranges_by_anno_uuid = self.read_segments(doc)

        for annotation_node in annotation_nodes:
            type = annotation_node.get("type")
            tag_uuid = get_uuid_from_catma_uuid_str(type)
            tag = self.get_tag(tag_uuid)
            anno_uuid_str = get_xml_node_id(annotation_node)
            anno_uuid = get_uuid_from_catma_uuid_str(anno_uuid_str)
            anno = Annotation(tag=tag, anno_uuid=anno_uuid)
            anno_ranges = ranges_by_anno_uuid[anno_uuid]
            anno.ranges = anno_ranges
            self.annotations.append(anno)

            property_nodes = annotation_node.findall("./tei:f", TEI_NAMESPACE_MAPPING)
            for property_node in property_nodes:
                name = property_node.get("name")

                for value_node in property_node.findall(".//tei:string", TEI_NAMESPACE_MAPPING):
                    anno.add_property(name, value_node.text, True)

    def read_segments(self, doc: XML):
        ranges_by_anno_uuid = {}
        for segment_node in doc.findall(".//tei:text/tei:body/tei:ab/tei:seg", TEI_NAMESPACE_MAPPING):
            ana = segment_node.get("ana")
            anno_range = self.extract_pointer_range(segment_node)
            if ana is not None:
                for annotation_uuid_ref in ana.split():
                    annotation_uuid = get_uuid_from_catma_uuid_str(annotation_uuid_ref[1:])
                    if not annotation_uuid in ranges_by_anno_uuid:
                        ranges_by_anno_uuid[annotation_uuid] = []
                    ranges_by_anno_uuid[annotation_uuid].append(anno_range)

        return ranges_by_anno_uuid

    def extract_pointer_range(self, segment_node: XML) -> Range:
        ptr_element = segment_node.find("./tei:ptr", TEI_NAMESPACE_MAPPING)
        target = ptr_element.get("target")
        return extract_range(target)

    def extract_documentid(selfs, target: str) -> str:
        return target[target.find("CATMA_") + 6:target.find("#")]

    def read_tagsets(self, doc: XML):
        tagset_nodes = doc.findall(".//tei:encodingDesc/tei:fsdDecl", TEI_NAMESPACE_MAPPING)
        for tagset_node in tagset_nodes:
            n_value = tagset_node.get("n")
            divider_pos = n_value.rfind(" ")
            tagset_name = n_value[0:divider_pos]
            version_string = n_value[divider_pos + 1:]
            tagset = Tagset(name=tagset_name, tags={}, version=version_string,
                            tagset_uuid=get_uuid_from_catma_uuid_str(get_xml_node_id(tagset_node)))
            self.read_tags(tagset_node, tagset)
            self.tagsets.append(tagset)

    def read_tags(self, tagset_node: XML, tagset: Tagset):
        tag_nodes = tagset_node.findall("./tei:fsDecl", TEI_NAMESPACE_MAPPING)
        uuid_to_parent_uuid_mapping = {}
        for tag_node in tag_nodes:
            description = ""
            description_node = tag_node.find("./tei:fsDescr", TEI_NAMESPACE_MAPPING)
            if description_node is not None and description_node.text is not None:
                description = description_node.text

            tag_uuid = get_uuid_from_catma_uuid_str(get_xml_node_id(tag_node))
            version = tag_node.get("n")

            author_node = tag_node.find("./tei:fDecl[@name='catma_markupauthor']", TEI_NAMESPACE_MAPPING)
            author = author_node.find(".//tei:string", TEI_NAMESPACE_MAPPING).text
            author_prop_uuid = get_uuid_from_catma_uuid_str(get_xml_node_id(author_node))

            color_node = tag_node.find("./tei:fDecl[@name='catma_displaycolor']", TEI_NAMESPACE_MAPPING)
            color = color_node.find(".//tei:string", TEI_NAMESPACE_MAPPING).text
            color_prop_uuid = get_uuid_from_catma_uuid_str(get_xml_node_id(color_node))

            parent_uuid_str = tag_node.get("baseTypes")

            tag = Tag(
                name=description,
                tag_uuid=tag_uuid,
                color=int(color),
                color_prop_uuid=color_prop_uuid,
                author=author,
                author_prop_uuid=author_prop_uuid,
                version=version)

            if parent_uuid_str is not None:
                uuid_to_parent_uuid_mapping[tag.uuid] = get_uuid_from_catma_uuid_str(parent_uuid_str)

            self.read_user_properties(tag_node, tag)

            tagset.add_tag(tag)

        for tag in tagset.tags.values():
            if tag.uuid in uuid_to_parent_uuid_mapping:
                tag.parent = tagset.tags.get(uuid_to_parent_uuid_mapping[tag.uuid])

    def read_user_properties(self, tag_node: XML, tag: Tag):
        property_nodes = tag_node.findall("./tei:fDecl", TEI_NAMESPACE_MAPPING)

        for property_node in property_nodes:
            if not property_node.get("name").startswith("catma_"):
                property_def = Property(name=property_node.get("name"),
                                        prop_uuid=get_uuid_from_catma_uuid_str(get_xml_node_id(property_node)))
                for value_node in property_node.findall(".//tei:string", TEI_NAMESPACE_MAPPING):
                    property_def.values.append(value_node.text)
                tag.add_property(property_def)


def merge_collections(collection_filename1, collection_filename2, oubput_filename, title=None, author=None):
    """
    Merges two Annotations Collections into one.

    :param collection_filename1: the full path of the first Collection
    :param collection_filename2: the full path of the second Collection
    :param oubput_filename: the full path of the resulting Collection
    :param title: the title of the resulting Collection, optional, defaults to the title of the first Collection
    :param author: the author of the resulting Collection, optional, defaults to the author of the first Collection
    """
    reader1 = TEIAnnotationReader(collection_filename1)
    reader2 = TEIAnnotationReader(collection_filename2)
    tagsets = list(reader1.tagsets)
    tagset_uuids = [tagset.uuid for tagset in tagsets]

    for tagset in reader2.tagsets:
        if tagset.uuid not in tagset_uuids:
            tagsets.append(tagset)

    if title is None:
        title = reader1.title

    if author is None:
        author = reader1.author

    writer = TEIAnnotationWriter(
        text_length=reader1.text_length,
        title=title,
        tagsets=tagsets,
        annotations_list=[reader1.annotations, reader2.annotations],
        author=author,
        documentid=reader1.documentid)

    writer.write_to_tei(oubput_filename)


def convert_ptr_refs_to_text(collection_filename: str, text_filename: str, output_filename: str):
    """
    Loads an Annotation Collection and a Source Document and replaces all pointer (<ptr>) occurrences in the Collection
    that point to the Source Document with their corresponding segment of text. The result is written to a file with the
    given output_filename. The Annotation Collection must belong to the Source Document!

    :param collection_filename: Name of the Annotation Collection
    :param text_filename:  Name of the Source Document
    :param output_filename: The name of the output file.
    """
    txt_file = open(text_filename, encoding="utf-8", newline="")
    text = txt_file.read()
    txt_file.close()

    XML.register_namespace("", TEI_NAMESPACE_MAPPING["tei"])

    collection_doc = XML.parse(collection_filename)

    ab_el = collection_doc.find(".//tei:text/tei:body/tei:ab", TEI_NAMESPACE_MAPPING)
    parent_map = {c: p for p in collection_doc.getroot().iter() for c in p}

    predecessor = None
    for child_el in ab_el:
        if child_el.tag == "{"+TEI_NAMESPACE_MAPPING["tei"]+"}ptr":
            anno_range = extract_range(child_el.get("target"))
            if predecessor is None:
                ab_el.text = text[anno_range.start:anno_range.end]
            else:
                predecessor.tail = text[anno_range.start:anno_range.end]
        elif child_el.tag == "{"+TEI_NAMESPACE_MAPPING["tei"]+"}seg":
            ptr_el = child_el[0]
            anno_range = extract_range(ptr_el.get("target"))
            child_el.text = text[anno_range.start:anno_range.end]
            predecessor = child_el

    for ptr_el in ab_el.findall(".//tei:ptr", TEI_NAMESPACE_MAPPING):
        parent = parent_map[ptr_el]
        parent.remove(ptr_el)

    XML.ElementTree(collection_doc.getroot()).write(
        file_or_filename=output_filename, xml_declaration=True, encoding="utf-8", method="xml")


class XMLSourceDocumentChunk(object):
    """
    Represents a chunk of text within the XML document, this can be either a node's text content or its tail content.
    """

    def __init__(self, start_pos: int, end_pos: int, node: XML=None, is_tail=False, is_newline = False):
        self.range = Range(start_pos, end_pos)
        self.node = node
        self.is_tail = is_tail
        self.is_newline = is_newline

    def get_range(self) -> int:
        return self.range

    def get_text(self, text_range: Range=None) -> str:
        """
        :param text_range: an optional range, if not given all text is returned
        :return: the text of this chunk, either all or within the given range
        """

        if self.is_newline:
            return '\n'

        if self.is_tail:
            if text_range is None:
                return self.node.tail
            return self.node.tail[text_range.start-self.range.start:text_range.end-self.range.start]
        else:
            if text_range is None:
                return self.node.text
            return self.node.text[text_range.start-self.range.start:text_range.end-self.range.start]

    def get_text_from(self, pos: int) -> str:
        """
        :param pos: a start position
        :return: the text from the given position to the end of the chunk
        """

        if self.is_newline and pos-self.range.start > 0:
            return '\n'
        elif self.is_newline:
            return ''

        if self.is_tail:
            return self.node.tail[pos-self.range.start:]
        else:
            return self.node.text[pos-self.range.start:]

    def get_text_up_to(self, pos: int) -> str:
        """
        :param pos: the end position
        :return: the text of this chunk up to the given position
        """

        if self.is_newline and pos-self.range.start > 0:
            return '\n'
        elif self.is_newline:
            return ''

        if self.is_tail:
            return self.node.tail[:pos-self.range.start]
        else:
            return self.node.text[:pos-self.range.start]

    def __repr__(self):
        return str(self.range) + ' ' + str(self.is_tail) + ' ' + str(self.is_newline) \
               + ('' if self.is_newline else ' ' + (self.node.tail if self.is_tail else self.node.text))

    def __hash__(self):
        return hash((self.range, self.is_tail, self.is_newline))

    def __eq__(self, other):
        """
        Equality by start and end offsets, tail flag and newline flag.
        """
        return (self.range, self.is_tail, self.is_newline) == (other.range, other.is_tail, other.is_newline)

    def __ne__(self, other):
        return not self == other

    def apply(self, annotation: Annotation, merged_range: Range, parent_map: map, recalculate_positions,
              element_name_from_tag_creator, attribute_name_from_property_creator):
        """
        Applies the given annotation to this chunk.
        :param annotation: the annotation to apply
        :param merged_range: the range of the annotated text
        :param parent_map: a mapping of child nodes to their parent
        :param recalculate_positions: a function that recalculates all positions of all chunks of all annotations after the application of the given annotation
        """
        # annotated text
        anno_text = self.get_text(merged_range)
        # non annotated text
        new_text_or_tail = self.get_text_up_to(merged_range.start)
        # non annotated tail
        anno_tail = self.get_text_from(merged_range.end)

        properties = {attribute_name_from_property_creator("annotationId"): get_catma_uuid_as_str(annotation),
             attribute_name_from_property_creator("tagId"): get_catma_uuid_as_str(annotation.tag),
             attribute_name_from_property_creator("tagPath"): annotation.tag.get_path()};

        for property_name in annotation.properties:
            properties[attribute_name_from_property_creator(property_name)] = ",".join(annotation.properties[property_name])

        anno_el = XML.Element(
            element_name_from_tag_creator(annotation.tag),
            properties)

        if self.is_tail:
            parent = parent_map[self.node]
            parent.insert(list(parent).index(self.node)+1, anno_el)

            parent_map[anno_el] = parent

            self.node.tail = new_text_or_tail
        else:
            self.node.insert(0, anno_el)

            parent_map[anno_el] = self.node

            self.node.text = new_text_or_tail

        anno_el.text = anno_text

        anno_text_chunk = XMLSourceDocumentChunk(merged_range.start, merged_range.end, anno_el, False)
        anno_tail_chunk = None

        if len(anno_tail) > 0:
            anno_el.tail = anno_tail
            anno_tail_chunk = XMLSourceDocumentChunk(merged_range.end, self.range.end, anno_el, True)
        old_range = self.range
        self.range = Range(self.range.start, merged_range.start)
        recalculate_positions(self, old_range, None, None, anno_text_chunk, anno_tail_chunk)

    def get_layer(self, parent_map: map):
        """
        :param parent_map: a mapping from node->parent node
        :return: the layer of this chunk, that is the chunk's node or its parent in case of a tail
        """
        if self.is_tail:
            return parent_map[self.node]
        else:
            return self.node


class XMLSourceDocumentPositionPointer(object):
    """
    A position pointer that gets forwarded when incremented by text/tail chunks or artificial newlines
    """
    def __init__(self, search_pos: int):
        """
        :param search_pos: the designated position of this pointer
        """
        self.search_pos = search_pos
        self.pos = 0
        self.chunks = list()
        self.locked = False

    def increment(self, node: XML, is_tail: bool) -> XMLSourceDocumentChunk:
        """
        Moves this pointer forward by the text amount of the given node text or tail.
        :param node: the node with text/tail content
        :param is_tail: true if content is in tail, false if content is in text
        :return: a chunk for the given node part
        """
        if not self.locked:
            start_pos = self.pos
            if is_tail:
                self.pos += len(node.tail)
            else:
                self.pos += len(node.text)

            self.chunks.append(XMLSourceDocumentChunk(start_pos, self.pos, node, is_tail=is_tail))

            if self.is_greater(self.search_pos):
                self.lock()

    def increment_by_newline(self):
        """
        Increments this pointer by an artificial newline
        :return: a chunk representing the atrificial newline
        """
        if not self.locked:
            start_pos = self.pos
            self.pos += 1
            self.chunks.append(XMLSourceDocumentChunk(start_pos, self.pos, is_newline=True))

            if self.is_greater(self.search_pos):
                self.lock()

    def is_greater(self, pos: int) -> bool:
        """
        :param pos: the position to test
        :return: true if the position this pointer points to is greater than the given position
        """
        return self.pos > pos

    def lock(self):
        """
        Locks this pointer to its current position. Further calls to increment won't have any effect anymore.
        """
        self.locked = True

    def is_locked(self) -> bool:
        """
        :return: true if this pointer is locked to its current position and cannot be moved forward anymore
        """
        return self.locked

    def get_max_matching_chunk(self):
        """
        :return: the chunk that is as close  as possible to the search position of this pointer coming from the left side
        """
        reversed_chunks =  list(self.chunks)
        reversed_chunks.reverse()
        passed_search_pos = False
        for chunk in reversed_chunks:
            is_in_range = chunk.get_range().is_in_between_inclusive_edge(self.search_pos)
            if not chunk.is_newline and (is_in_range or passed_search_pos):
                return chunk

            if is_in_range:
                passed_search_pos = True

    def get_min_matching_chunk(self):
        """
        :return: the chunk that is as close as possible to the search position of this pointer coming from the right side
        """
        last_chunk = None
        reversed_chunks =  list(self.chunks)
        reversed_chunks.reverse()
        for chunk in reversed_chunks:
            if not chunk.get_range().is_in_between_inclusive_edge(self.search_pos) and last_chunk is not None and not last_chunk.is_newline:
                return last_chunk
            last_chunk = chunk

        return last_chunk

    def recalculate(self, \
                              start_chunk: XMLSourceDocumentChunk, old_start_chunk_range: Range, \
                              end_chunk: XMLSourceDocumentChunk, old_end_chunk_range, \
                              anno_text_chunk: XMLSourceDocumentChunk, anno_tail_chunk: XMLSourceDocumentChunk):
        """
        Recalculates the chunks of this pointer according to the given information.
        :param start_chunk: the new start chunk to replace the old start chunk at old_start_chunk_range
        :param old_start_chunk_range: the start chunk's old range
        :param end_chunk: the new end chunk to replace the old end chunk at old_end_chunk_range
        :param old_end_chunk_range: the end chunk's old range
        :param anno_text_chunk: the new annotation's text chunk
        :param anno_tail_chunk:  the new annotation's end chunk
        """

        # find the old start chunk by the given old start chunk's range
        old_start_chunk = next((c for c in self.chunks if c.range == old_start_chunk_range), None)

        # find the old end chunk by the given old end chunk's range (if given at all)
        old_end_chunk = None
        if old_end_chunk_range is not None:
            old_end_chunk = next((c for c in self.chunks if c.range == old_end_chunk_range), None)

        idx = -1
        # is the given start chunk represented in this pointer's chunk list?
        if old_start_chunk is not None:
            idx = self.chunks.index(old_start_chunk)
            # set the new range of the start chunk
            old_start_chunk.range = start_chunk.range
        elif start_chunk in self.chunks:
            idx = self.chunks.index(start_chunk)

        if idx != -1:
            # if the search position of this pointer includes the annotated text chunk
            if anno_text_chunk.range.start <= self.search_pos:
                self.chunks.insert(idx+1,
                                   XMLSourceDocumentChunk(anno_text_chunk.range.start, anno_text_chunk.range.end,
                                                          anno_text_chunk.node, anno_text_chunk.is_tail))
                idx += 1

            # if there is no end chunk and the annotated tail chunk exists and is within the search position of this pointer
            # then include the annotated tail chunk
            if old_end_chunk_range is None and anno_tail_chunk is not None and anno_tail_chunk.range.start <= self.search_pos:
                self.chunks.insert(idx+1,
                                   XMLSourceDocumentChunk(anno_tail_chunk.range.start, anno_tail_chunk.range.end,
                                                          anno_tail_chunk.node, anno_tail_chunk.is_tail))

        # adjust the range of the old end chunk if there is any
        if old_end_chunk is not None:
            idx = self.chunks.index(old_end_chunk)

            old_end_chunk.range = end_chunk.range

            if anno_tail_chunk is not None and anno_tail_chunk.range.start <= self.search_pos:
                self.chunks.insert(idx + 1,
                                   XMLSourceDocumentChunk(anno_tail_chunk.range.start, anno_tail_chunk.range.end,
                                                          anno_tail_chunk.node, anno_tail_chunk.is_tail))


def has_text_content(node: XML) -> bool:
    """
    :param node: the node to test
    :return: true if the given node has non empty text content, else false
    """
    return node.text is not None and len(node.text.strip()) > 0


def has_tail_content(node: XML) -> bool:
    """
    :param node: the node to test
    :return: true if the given node has non empty tail content
    """
    return node.tail is not None and len(node.tail.strip()) > 0


class XMLSourceDocumentAnnotation(object):
    """
    A representation of a CATMA Annotation on top of a XML based Source Document.
    """

    def __init__(self, annotation: Annotation, range: Range,
                 start_pos: XMLSourceDocumentPositionPointer, end_pos: XMLSourceDocumentPositionPointer,
                 element_name_from_tag_creator, attribute_name_from_property_creator):
        self.annotation = annotation
        self.range = range
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.element_name_from_tag_creator = element_name_from_tag_creator
        self.attribute_name_from_property_creator = attribute_name_from_property_creator

    def __repr__(self):
        start_chunk = self.start_pos.get_max_matching_chunk()
        end_chunk = self.end_pos.get_min_matching_chunk()

        result = str(self.range) + ' annotationId ' + get_catma_uuid_as_str(self.annotation) + ' *'

        if start_chunk == end_chunk:
            result += start_chunk.get_text(self.range)
        else:
            result += start_chunk.get_text_from(self.range.start)
            include = False
            for chunk in self.end_pos.chunks:
                if chunk == start_chunk:
                    include = True
                elif chunk == end_chunk:
                    include = False
                elif include:
                    result += chunk.get_text()

            result += end_chunk.get_text_up_to(self.range.end)

        return result + '*'

    def get_chunks_for_layer(self, start_chunk: XMLSourceDocumentChunk, end_chunk: XMLSourceDocumentChunk, layer: XML, parent_map):
        """
        Collects and returns the chunks for the given layer.
        :param start_chunk: the start chunk, where this Annotation starts
        :param end_chunk:  the end chunk, where this Annotation ends
        :param layer: the layer we want chunks for
        :param parent_map: a mapping of child nodes to parent nodes
        :return: the chunks for the given layer
        """

        start_layer = start_chunk.get_layer(parent_map)
        end_layer = end_chunk.get_layer(parent_map)

        # the search for the correct parent layer
        # depends on when a layer appears first in the grouping
        # that's why we need to group all chunks by their layer
        # and not just the ones from the given layer

        chunks_by_layer = {start_layer: [start_chunk]}

        include = False
        for chunk in self.end_pos.chunks:
            if chunk == start_chunk:
                include = True  # start including the chunks into the map
            elif chunk == end_chunk:
                include = False  # stop including the chunks into the map
            elif include:
                if not chunk.is_newline:  # skip newline chunks
                    current_layer = chunk.get_layer(parent_map)

                    # try to find the top most node (layer) that is already included
                    # layers that are further down the tree get wrapped automatically then
                    parent_layer = current_layer
                    while parent_layer in parent_map:
                        if parent_layer in chunks_by_layer:
                            current_layer = parent_layer
                        if current_layer == end_layer or current_layer == start_layer or parent_layer  == end_layer:
                            break
                        parent_layer = parent_map[parent_layer]

                    if current_layer in chunks_by_layer:
                        chunks_by_layer[current_layer].append(chunk)
                    else:
                        chunks_by_layer[current_layer] = [chunk]

        if end_layer in chunks_by_layer:
            chunks_by_layer[end_layer].append(end_chunk)
        else:
            chunks_by_layer[end_layer] = [end_chunk]

        # return only the chunks from the given layer
        return chunks_by_layer[layer]

    def apply(self, parent_map: map, recalculate_positions):
        """
        Applies this annotation to the document which is represented by the chunks of its positions
        :param parent_map: a mapping of child nodes to their parents
        :param recalculate_positions: a function that recalculates the positions in all other annotations after this annotation has been applied
        """

        # get the chunk where the annotation currently starts
        start_chunk = self.start_pos.get_max_matching_chunk()
        # get the chunk where the annotation currently ends
        end_chunk = self.end_pos.get_min_matching_chunk()

        if start_chunk == end_chunk:
            # easy, all within one chunk, so we delegate to that chunk
            start_chunk.apply(self.annotation, self.range, parent_map, recalculate_positions,
                              self.element_name_from_tag_creator, self.attribute_name_from_property_creator)
        else:
            # hard, start_chunk and end_chunk are different

            # get the layers of the chunks, either their nodes or the corresponding parent nodes in case of tail chunks
            start_layer = start_chunk.get_layer(parent_map)
            end_layer = end_chunk.get_layer(parent_map)

            # get all layers involved,
            # the search for the correct parent layer
            # depends on when a layer appears first in the list!!!

            layers = [start_layer]
            include = False
            for chunk in self.end_pos.chunks:
                if chunk == start_chunk:
                    include = True # start including the layers
                elif chunk == end_chunk:
                    include = False # stop including the layers
                elif include:
                    if not chunk.is_newline: # skip newline chunks
                        layer = chunk.get_layer(parent_map)

                        # try to find the top most node (layer) that is already included
                        # layers that are further down the tree get wrapped automatically then
                        parent_layer = layer
                        while parent_layer in parent_map:
                            if parent_layer in layers:
                                layer = parent_layer
                            if layer == end_layer or parent_layer == end_layer:
                                break
                            parent_layer = parent_map[parent_layer]

                        if layer not in layers:
                            layers.append(layer)

            if end_layer not in layers:
                layers.append(end_layer)

            # for each layer we compute the annotated chunks and recalculate the positions
            for layer in layers:
                # get fresh start and end chunks because they might have changed during recalculation
                start_chunk = self.start_pos.get_max_matching_chunk()
                end_chunk = self.end_pos.get_min_matching_chunk()

                chunks = self.get_chunks_for_layer(start_chunk, end_chunk, layer, parent_map)

                layer_start_chunk = chunks[0]
                layer_end_chunk = chunks[len(chunks)-1]

                if layer_start_chunk == layer_end_chunk: # easy: start chunk and end chunk of the layer are the same
                    if layer_start_chunk == start_chunk: # start of the annotation, may be a partial chunk
                        start_chunk.apply(self.annotation, Range(self.range.start, start_chunk.range.end), parent_map,
                                          recalculate_positions, self.element_name_from_tag_creator, self.attribute_name_from_property_creator)
                    elif layer_start_chunk == end_chunk: # end of the annotation, may be a partial chunk
                        end_chunk.apply(self.annotation, Range(end_chunk.range.start, self.range.end), parent_map,
                                        recalculate_positions, self.element_name_from_tag_creator, self.attribute_name_from_property_creator)
                    elif not layer_start_chunk.range.is_point(): # somewhere in between, annotate full chunk if there actually is anything to annotate
                        layer_start_chunk.apply(self.annotation, Range(layer_start_chunk.range.start, layer_start_chunk.range.end), parent_map,
                                          recalculate_positions, self.element_name_from_tag_creator, self.attribute_name_from_property_creator)
                else:
                    # hard: calculate a modfied start chunk with the start of the annotation
                    # and a modified end chunk with the end of the annotation
                    layer_start_range = layer_start_chunk.range
                    if layer_start_chunk == start_chunk:
                        layer_start_range = Range(max(self.range.start, layer_start_chunk.range.start), start_chunk.range.end)

                    layer_end_range = layer_end_chunk.range
                    if layer_end_chunk == end_chunk:
                        layer_end_range = Range(layer_end_chunk.range.start, min(layer_end_chunk.range.end, self.range.end))

                    # annotated text of the start chunk
                    anno_text = layer_start_chunk.get_text(layer_start_range)
                    # non annotated text of the start chunk
                    new_layer_start_chunk_text_or_tail = layer_start_chunk.get_text_up_to(layer_start_range.start)

                    # annotated text of the end chunk
                    new_layer_end_chunk_tail = layer_end_chunk.get_text_up_to(min(layer_end_chunk.range.end, self.range.end))

                    # non annotated text trailing the new annotation
                    anno_tail = layer_end_chunk.get_text_from(self.range.end)

                    properties = {self.attribute_name_from_property_creator("annotationId"): get_catma_uuid_as_str(self.annotation),
                         self.attribute_name_from_property_creator("tagId"): get_catma_uuid_as_str(self.annotation.tag),
                         self.attribute_name_from_property_creator("tagPath"): self.annotation.tag.get_path()}

                    for property_name in self.annotation.properties:
                        properties[self.attribute_name_from_property_creator(property_name)] = ",".join(self.annotation.properties[property_name])

                    anno_el = XML.Element(
                        self.element_name_from_tag_creator(self.annotation.tag),
                        properties)

                    anno_el.text = anno_text
                    anno_el.tail = anno_tail

                    # set non annotated text of the start chunk
                    if layer_start_chunk.is_tail:
                        layer_start_chunk.node.tail = new_layer_start_chunk_text_or_tail
                    else:
                        layer_start_chunk.node.text = new_layer_start_chunk_text_or_tail

                    # set annotated text of the end chunk
                    layer_end_chunk.node.tail = new_layer_end_chunk_tail

                    # insert the new annotation element
                    if layer_start_chunk.node == layer: # the annotation start in the text of the layer node
                        layer.insert(0, anno_el)
                    else: # the annotation start in the tail of a child node of the layer node
                        layer.insert(list(layer).index(layer_start_chunk.node)+1, anno_el)

                    parent_map[anno_el] = layer

                    # reassign all inner chunk nodes to the annotation node
                    for chunk in chunks:
                        if not chunk == layer_start_chunk and not chunk == layer_end_chunk:
                            parent = parent_map[chunk.node]
                            if parent == layer:
                                if chunk.node in parent:
                                    parent.remove(chunk.node)
                                    anno_el.append(chunk.node)
                                    parent_map[chunk.node] = anno_el

                    # create new chunks for text and tail of the new annotation node
                    anno_text_chunk = XMLSourceDocumentChunk(layer_start_range.start, layer_start_range.end, anno_el, False)
                    anno_tail_chunk = None

                    if len(anno_tail) > 0:
                        anno_el.tail = anno_tail
                        anno_tail_chunk = XMLSourceDocumentChunk(self.range.end, layer_end_chunk.range.end, anno_el, True)

                    # adjust the ranges of start and end chunks of the current layers
                    # keep the old ranges to recalculate the positions in all other annotations
                    old_layer_start_chunk_range = layer_start_chunk.range
                    layer_start_chunk.range = Range(layer_start_chunk.range.start, layer_start_range.start)
                    old_layer_end_chunk_range = layer_end_chunk.range
                    layer_end_chunk.range = Range(layer_end_chunk.range.start, min(layer_end_chunk.range.end, self.range.end))

                    parent = parent_map[layer_end_chunk.node]
                    if parent == layer:
                        parent_map[layer_end_chunk.node].remove(layer_end_chunk.node)
                        anno_el.append(layer_end_chunk.node)
                        parent_map[layer_end_chunk.node] = anno_el

                    recalculate_positions(layer_start_chunk, old_layer_start_chunk_range, layer_end_chunk, old_layer_end_chunk_range, anno_text_chunk, anno_tail_chunk)

    def recalculate_positions(self, \
                              start_chunk: XMLSourceDocumentChunk, old_start_chunk_range: Range, \
                              end_chunk: XMLSourceDocumentChunk, old_end_chunk_range, \
                              anno_text_chunk: XMLSourceDocumentChunk, anno_tail_chunk: XMLSourceDocumentChunk):
        """
        Recalculates the positions of this annotation
        :param start_chunk: the new start chunk to replace the old start chunk at old_start_chunk_range
        :param old_start_chunk_range: the start chunk's old range
        :param end_chunk: the new end chunk to replace the old end chunk at old_end_chunk_range
        :param old_end_chunk_range: the end chunk's old range
        :param anno_text_chunk: the new annotation's text chunk
        :param anno_tail_chunk:  the new annotation's end chunk
        """
        self.start_pos.recalculate(start_chunk, old_start_chunk_range, end_chunk, old_end_chunk_range, anno_text_chunk, anno_tail_chunk)
        self.end_pos.recalculate(start_chunk, old_start_chunk_range, end_chunk, old_end_chunk_range, anno_text_chunk, anno_tail_chunk)


class XMLSourceDocument(object):
    """
    A XML based Source Document
    """
    def __init__(self, filename: str):
        self.doc = XML.parse(filename)
        self.parent_map = {el: parent for parent in self.doc.getroot().iter() for el in parent}
        self.document_annotations = list()

    def apply(self, annotations: list, element_name_from_tag_creator, attribute_name_from_property_creator):
        """
        Applies the given list of CATMA annotations to this document
        :param annotations: the annotations to apply
        """

        # for each annotation we create a XMLSourceDocumentAnnotation which points to the start and end chunks of the documnent
        for annotation in annotations:
            ranges = Range.merge_ranges(sorted(annotation.ranges))
            for range in ranges:
                # compute the start position of the annotation
                start_pos = XMLSourceDocumentPositionPointer(range.start)
                self.seek_position(self.doc.getroot(), start_pos);

                # compute the end position of the annotation
                end_pos = XMLSourceDocumentPositionPointer(range.end)
                self.seek_position(self.doc.getroot(), end_pos)

                self.document_annotations.append(XMLSourceDocumentAnnotation(
                    annotation, range, start_pos, end_pos, element_name_from_tag_creator, attribute_name_from_property_creator))

        for document_annotation in self.document_annotations:
            print("applying annotation: " + str(document_annotation))
            document_annotation.apply(self.parent_map, self.recalculate_positions)

    def recalculate_positions(self, \
                              start_chunk: XMLSourceDocumentChunk, old_start_chunk_range: Range, \
                              end_chunk: XMLSourceDocumentChunk, old_end_chunk_range, \
                              anno_text_chunk: XMLSourceDocumentChunk, anno_tail_chunk: XMLSourceDocumentChunk):
        for document_annotation in self.document_annotations:
            document_annotation.recalculate_positions(start_chunk, old_start_chunk_range, end_chunk, old_end_chunk_range, anno_text_chunk, anno_tail_chunk)

    def seek_position(self, parent_node: XML, current_pos: XMLSourceDocumentPositionPointer):

        if has_text_content(parent_node):
            current_pos.increment(parent_node, False)

        if current_pos.is_locked():
            return
        else:
            for child_node in parent_node:
                self.seek_position(child_node, current_pos)
                if current_pos.is_locked():
                    return

            if has_text_content(parent_node) or len(list(parent_node)) > 0:
                current_pos.increment_by_newline()

            if has_tail_content(parent_node):
                current_pos.increment(parent_node, True)


def create_default_element_name_from_tag(tag: Tag, non_ascii_character_mapper = lambda c : "_") -> str:
    result = []
    name = tag.name

    if name[0] in string.digits:
        result.append("T")
    for c in name:
        if c in string.ascii_letters + string.digits:
            result.append(c)
        else:
            result.append(non_ascii_character_mapper(c))
    return "".join(result)


def create_default_attribute_name_from_property(name: str, non_ascii_character_mapper = lambda c : "_") -> str:
    result = []

    if name[0] in string.digits:
        result.append("P")
    for c in name:
        if c in string.ascii_letters + string.digits:
            result.append(c)
        else:
            result.append(non_ascii_character_mapper(c))
    return "".join(result)


def apply_collection_to_xml_document(collection_filename: str, document_filename: str, output_filename: str,
                                     element_name_from_tag_creator=create_default_element_name_from_tag,
                                     attribute_name_from_property_creator=create_default_attribute_name_from_property,
                                     custom_namespace = None):
    """
    Applies all Annotations of the given Collection to the given XML based Source Document and writes the result to
    the output file.
    :param collection_filename: full path to the Collection file
    :param document_filename: full path to the XML based Source Document file
    :param output_filename: full path to the output file
    :param element_name_from_tag_creator: a function that takes a Tag and converts its name to a valid XML element name
    :param attribute_name_from_property_creator:  a function that takes a Property name and converts it to a valid XML attribute name
    :param custom_namespace: a tuple with a prefix and a URL like ("mn", "http://mynamespace.com/ns")
    :return:
    """
    collection_reader = TEIAnnotationReader(collection_filename)
    annotations = collection_reader.annotations

    element_name_from_tag_creator_with_ns = \
        element_name_from_tag_creator if custom_namespace is None else lambda tag : custom_namespace[0] + ":" + element_name_from_tag_creator(tag)

    attribute_name_from_property_creator_with_ns = \
        attribute_name_from_property_creator if custom_namespace is None else lambda prop_name : custom_namespace[0] + ":" + attribute_name_from_property_creator(prop_name)

    source_doc = XMLSourceDocument(document_filename)
    source_doc.apply(annotations, element_name_from_tag_creator_with_ns, attribute_name_from_property_creator_with_ns)

    if custom_namespace is not None:
        source_doc.doc.getroot().set("xmlns:"+custom_namespace[0], custom_namespace[1])

    # print(XML.tostring(source_doc.doc.getroot(),))
    source_doc.doc.write(file_or_filename=output_filename, xml_declaration=True, encoding="utf-8", method="xml")
