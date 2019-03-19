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
    return uuid.UUID(catma_uuid[6:])

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
    def __init__(self, filename: str):
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
        if not has_ptr_refs:
            raise Exception("This collection does not use <ptr> references and is not supported by this parser!")

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