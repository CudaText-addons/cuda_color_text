Plugin for CudaText.
Gives commands to colorize text fragments with several styles,
by background color and/or font style (italic/bold/strikeout/underline).

Configuration
-------------

To configure, call menu item in the "Options/ Settings-plugins / Color Text"
to edit config file. Options in section [op] are boolean, values 0/1 for off/on.

- all_words: Colorize all occurrences of fragment.
     When this option is on (ie "all_words=1"), you can just click
     the word, without selecting it first.
- case_sensitive: Case-sensitive search for other occurrences.
- whole_words: Colorize only those occurrences, which are whole words.
- show_on_map: Show added colored marks also on micro-map.

Section [colors] contains keys "1" to "6" to define attributes for commands
"Apply style 1" ... "Apply style 6". Format of each value: few comma-separated
strings: color_background,color_font,color_border,font_styles

- 'color_*' is empty or HTML color token like #aabbcc or #abc.
- 'font_styles' is empty or combination of chars:
  'b' for bold
  'i' for italic
  's' for strikeout
  'u' for underline
  'o' for all 4 borders


Helper file
-----------

Plugin saves applied attribs to the helper file: <original_filename>.cuda-colortext
(near the original file) and restores attribs later on file opening.
On applying attrib, plugin marks file as "modified", it is Ok, it's needed
to allow saving of the helper file.
You can delete the helper file, to forget about all added attribs.


Authors
-------

- Alexey Torgashin (CudaText)
- Khomutov Roman (@iRamSoft on GitHub)
License: MIT
