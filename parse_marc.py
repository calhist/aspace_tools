# Script to parse and edit a MARC XML export from EOS for optimal import into ArchivesSpace
# by Bill Levay for California Historical Society
#
#
#
# see here for ASpace MARC import rules: https://github.com/archivesspace/archivesspace/blob/master/backend/app/converters/lib/marcxml_base_map.rb

import os, lxml.etree as ET, re

# is there a list we want to check against? Like records already in the system?
with open('exists.txt') as f:
    exists = f.readlines()
# you may also want to remove whitespace characters like `\n` at the end of each line
exists = [x.strip() for x in exists]

# you probably want to change these values
filename = 'photos'
# callnumber = 'MS'

tree = ET.iterparse(filename, events=('end', ), remove_blank_text=True)

# find the <record> nodes
for event, elem in tree:

	# PUNCTUATION
	if elem.text:
		# get rid of any and all trailing commas
		elem.text = elem.text.rstrip(',')

		# Remove any double spaces
		elem.text = elem.text.replace('  ', ' ')

	# for each record
	if elem.tag == '{http://www.loc.gov/MARC21/slim}record':

		# if there is no 300 field, add a placeholder so we don't get an ASpace import error
		if elem.find('{http://www.loc.gov/MARC21/slim}datafield[@tag="300"]') is None:
			extent = ET.Element('datafield', tag='300', ind1=' ', ind2=' ')
			extent_sub = ET.Element('subfield', code='a')
			extent_sub.text = 'placeholder'
			elem.append(extent)
			extent.append(extent_sub)

		# the filenames of the resulting xml files will be based on the call number
		identifier = elem.find('{*}datafield[@tag="852"]/{*}subfield[@code="j"]')
		identifier.set('code','k')

		# only process those records that actually match the call number prefix we're working with
		# if identifier.text.startswith(callnumber) and identifier.text not in exists:
		if identifier.text not in exists:
			identifier.text = identifier.text.rstrip('.').replace(':', '-')
			filename = format(identifier.text + ".xml")

			for el in elem:

				# PUNCTUATION
				# for 100s, 600s, and 700s
				if el.tag == '{http://www.loc.gov/MARC21/slim}datafield' and (el.get('tag').startswith('1') or el.get('tag').startswith('6') or el.get('tag').startswith('7')):
					for e in el.getchildren():
						# if there's a period at the end of the value, and it's not an initial, remove it
						if e.text.endswith('.') and (' ' not in e.text[-4:] or 'de' in e.text[-4:]):
							e.text = e.text.rstrip('.')
						# if there's a subfield $q, remove any parentheses
						if e.get('code') == 'q':
							e.text = e.text.lstrip('(').rstrip(')')

				if el.tag == '{http://www.loc.gov/MARC21/slim}datafield' and el.get('tag') == '110':
					for e in el.getchildren():
						e.text = e.text.rstrip('.')

				# this is really targeting the 245 field
				if el.tag == '{http://www.loc.gov/MARC21/slim}datafield' and el.get('tag').startswith('2'):
					for e in el.getchildren():
						# if there's a colon at the end of a title or the start of a subtitle, remove it
						if (e.get('code') == 'a' or e.get('code') == 'b') and e.text.endswith(':'):
							e.text = e.text.rstrip(':').rstrip()
						if (e.get('code') == 'a' or e.get('code') == 'b') and e.text.startswith(':'):
							e.text = e.text.lstrip(':').lstrip()
						# remove periods
						if e.get('code') == 'c' or e.get('code') == 'f' or e.get('code') == 'g':
							e.text = e.text.rstrip('.')
						# remove subfield $h -- we don't need [graphic] appended to title in ASpace
						if e.get('code') == 'h':
							e.getparent().remove(e)
						# remove subfield $k, but save the data to a general note
						if e.get('code') == 'k':
							note = ET.Element('datafield', tag='500', ind1=' ', ind2=' ')
							note_sub = ET.Element('subfield', code='a')
							note_sub.text = e.text
							elem.append(note)
							note.append(note_sub)
							# now we can remove this subfield
							e.getparent().remove(e)

				# noticing some bad punctuation in the provenance field; let's fix that
				if el.tag == '{http://www.loc.gov/MARC21/slim}datafield' and el.get('tag') == '541':
					for e in el.getchildren():
						if (e.get('code') == 'a' or e.get('code') == 'c') and e.text.endswith(';'):
							e.text = e.text.rstrip(';').rstrip()
						if e.get('code') == 'd' and e.text.endswith('.'):
							e.text = e.text.rstrip('.')

				# EXTENTS
				if el.tag == '{http://www.loc.gov/MARC21/slim}datafield' and el.get('tag') == '300':
					for e in el.getchildren():
						e.text = e.text.replace('[','').replace(']','')
						e.text = e.text.replace('v.', 'volumes').replace('p.','pages')
						if e.text.endswith('.') and ' ' not in e.text[-4:]:
							e.text = e.text.rstrip('.')
						if e.text.endswith(';'):
							e.text = e.text.rstrip(';').rstrip()

						# if there are multiple subfield $a's, we should separate 2nd one into a new 300 element
						extent_sub_a = None
						extent_sub_f = None
						if e.get('code') == 'a':
							for sib in e.itersiblings():
								if sib.get('code') == 'a':
									# we have a 2nd subfield a
									sib.text = sib.text.lstrip('(').rstrip(')')
									extent_sub_a = sib
									sib.getparent().remove(sib)
									
						# let's check for a 2nd subfield f
						if e.get('code') == 'f':
							for sib in e.itersiblings():
								if sib.get('code') == 'f':
									# we have a 2nd subfield f
									sib.text = sib.text.lstrip('(').rstrip(')')
									extent_sub_f = sib
									sib.getparent().remove(sib)

						if extent_sub_a is not None:
							extent = ET.Element('datafield', tag='300', ind1=' ', ind2=' ')
							elem.append(extent)
							extent.append(extent_sub_a)
						if extent_sub_f is not None:
							extent.append(extent_sub_f)
									

						# let's try some regex to separate out any parenthetical extents into another 300 element
						if '(' in e.text:
							m = re.search('(.*)\((.*)', e.text)
							if m is not None:
								value1 = m.group(1).rstrip()
								value2 = m.group(2).rstrip(')')
								e.text = value1

								if value2 and value2 is not '':
									extent = ET.Element('datafield', tag='300', ind1=' ', ind2=' ')
									extent_sub = ET.Element('subfield', code='a')
									extent_sub.text = value2
									elem.append(extent)
									extent.append(extent_sub)

				# DATES
				# look in control field 008 for dates
				# if none, see if the 245 field has subfields
				# if none, add 'undated'; fix manually in ASpace if appropriate
				if el.tag == '{http://www.loc.gov/MARC21/slim}controlfield' and el.get('tag') == '008':
					if el.text[7:8] != '1':
						for sib in el.itersiblings():
							if sib.tag == '{http://www.loc.gov/MARC21/slim}datafield' and sib.get('tag') == '245':
								if sib.find('{http://www.loc.gov/MARC21/slim}subfield[@code="f"]') is None and sib.find('{http://www.loc.gov/MARC21/slim}subfield[@code="g"]') is None:
									date = ET.Element('subfield', code='f')
									date.text = 'undated'
									sib.append(date)
									print '*** adding "undated" to', identifier.text

				# if creation date is approximate, add "fix circa date" as the date expression, then fix value manually in ASpace
				if el.tag == '{http://www.loc.gov/MARC21/slim}controlfield' and el.get('tag') == '008':
					if 'u' in el.text[7:11]:
						for sib in el.itersiblings():
							if sib.tag == '{http://www.loc.gov/MARC21/slim}datafield' and sib.get('tag') == '245':
								if sib.find('{http://www.loc.gov/MARC21/slim}subfield[@code="f"]') is None and sib.find('{http://www.loc.gov/MARC21/slim}subfield[@code="g"]') is None:
									date = ET.Element('subfield', code='f')
									date.text = 'fix circa date'
									sib.append(date)
									print '*** adding "fix circa date" to', identifier.text

				# 752 field
				# if this field is missing subfield $2, ASpace import throws an error
				if el.tag == '{http://www.loc.gov/MARC21/slim}datafield' and (el.get('tag') == '752' or el.get('tag') == '754'):
					if el.find('{http://www.loc.gov/MARC21/slim}subfield[@code="2"]') is None:
						# let's add subfield $2 with a value of 'naf'
						source = ET.Element('subfield', code='2')
						source.text = 'naf'
						el.append(source)

				# 656 field
				# if this field is missing subfield $2, ASpace import throws an error
				if el.tag == '{http://www.loc.gov/MARC21/slim}datafield' and el.get('tag') == '656':
					if el.find('{http://www.loc.gov/MARC21/slim}subfield[@code="2"]') is None:
						# let's delete the field altogether
						el.getparent().remove(el)

			# write out each <record> to a file
			print 'writing', filename
			with open(filename, 'wb') as f:
				f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
				f.write('<collection xmlns="http://www.loc.gov/MARC21/slim"\n\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n\txsi:schemaLocation="http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd">\n\t')
				f.write(ET.tostring(elem, pretty_print = True))

print 'ALL DONE!'