## Gender Bender

This library allows you to flip the gender of a string or eBook (only works with the `epub` format).  The motivation was to be able to examine gender norms in a fun way.

To use the `epub` format, I recommend the Calibre reader or the Kobo.



### Usage

_Python 3 only_

Get the repo:

```bash
git clone https://github.com/Garrett-R/gender_bender.git
cd gender_bender
pip install -r requirements.txt
```

It can be run as a script:

```bash
./main.py --input Lord_of_the_Flies.epub  --output Lady_of_the_Flies.epub
```

Or from python:

```python
from gender_bender import gender_bend_epub
gender_bend_epub('./Mythical_Man_Month.epub')
```

You can also gender-bend a string:

```python
from gender_bender import gender_bend
x = gender_bend("If Ivanka weren't my daughter, perhaps I'd be dating her.")

assert x == "If Ivan weren't my son, perhaps I'd be dating him."
```

If you'd like to choose the names yourself (recommended for translating a whole ebook), you can do:

```bash
./main.py --input The_Little_Mermaid.epub --interactive-naming
```
