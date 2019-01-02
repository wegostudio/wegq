import re
from .WXBizMsgCrypt import *


def parse_xml(xml):
    """
    Convert the XML to dict
    """

    if not xml:
        return {}

    if type(xml) is bytes:
        xml = xml.decode("utf8")

    return {k: v for v,k in re.findall('\<.*?\>\<\!\[CDATA\[(.*?)\]\]\>\<\/(.*?)\>', xml)}
