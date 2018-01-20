# ArchiveSpace tools

## parse_marc.py

### The scenario

We need to export collection records as MARC XML from EOS, our ILS, and import into ArchivesSpace.

Where we saw import errors with our MARC XML:

* Incorrect namespaces
* Missing date
* Missing extent
* Missing subfield $2 for 752 field

### What it does

* Takes single EOS-exported MARC XML consisting of one or more records and splits it into single MARC XML files named with the call number, and with proper namespaces.
* Moves the call number from 852 subfield $j to $k; ASpace ignores subfield $j for some reason.
* Cleans up lots of punctuation!
* If there are multiple extents in the 300 field that describe the whole (e.g., "1 box (0.25 linear ft.)"), separates them out so they import as discrete extents in ASpace. Script does not, at this point, separate out partial extents
* If there is no 300 field at all, inserts a 300 with the text “placeholder”
* Prevents 245 subfield $k from being appended to the ASpace title, and creates a 500 note with this value instead.
* If there is no date in control field 008 (characters #8-11 in the string), and also no date in 245 subfield $f or $g, adds a subfield $f of "undated." This prevents records with no date from throwing an error during import.
* If there is a circa date in control field 008 (e.g., “188u”) and no date in 245 subfield $f or $g, adds a subfield $f of “fix circa date.”
* If there is a 752 or 754 field in the MARC record, ASpace expects to see subfield $2, the “source of heading or term,” even though this subfield is not required by MARC. Thus, the script will insert a subfield $2 with “naf” as the value.

### How to use it

1. Export records from EOS as MARC XML
2. Open parse_marc.py in your text editor
3. Change the value in line 10 to match your filename
4. Change the value in line 11 to match the call number prefix you're working with (e.g., MS, PC)
5. Open up a command prompt, navigate to the directory of the script, and run it with "python parse_marc.py"
6. Script will create individal MARC XML files for each record in the EOS export