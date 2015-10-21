import xml.etree.ElementTree as ET


def read_xml(xmlfile):

	tree = ET.parse(xmlfile)
	root = tree.getroot()

	profile = {}
	profile['profile_ports'] = []

	profile['applicationName'] = root.find("ApplicationName").text
	profile['vendor'] = root.find("Vendor").text
	profile['version'] = root.find("Version").text

	for entry in root.iter('Entry'):
		profile_entry = {}
		for child in entry:
			profile_entry[child.tag] = child.text
		profile['profile_ports'].append(profile_entry)

	return profile

profile = read_xml("application_map_SCOM2012R2.xml")
print profile