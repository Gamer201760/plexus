import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def sheets(path):
    with ZipFile(path) as archive:
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings = [''.join(item.itertext()) for item in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        relationships = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {item.attrib['Id']: item.attrib['Target'] for item in relationships}
        for sheet in workbook.find('m:sheets', NS):
            target = targets[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            filename = target.lstrip('/') if target.startswith('/') else 'xl/' + target
            root = ET.fromstring(archive.read(filename))
            rows = []
            for row in root.find('m:sheetData', NS):
                values = {}
                for cell in row:
                    column = re.sub(r'\d', '', cell.attrib['r'])
                    value = cell.findtext('m:v', '', NS)
                    if cell.attrib.get('t') == 's' and value:
                        value = strings[int(value)]
                    elif cell.attrib.get('t') == 'inlineStr':
                        value = ''.join(cell.find('m:is', NS).itertext())
                    values[column] = value
                rows.append((int(row.attrib['r']), values))
            yield sheet.attrib['name'], rows
