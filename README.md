## Gender Bender

This library allows you to flip the gender of or a string or eBook (only works with the `epub` format).  The motivation was to be able to examine gender norms in a fun way.

To use the `epub` format, I recommend the Calibre reader or the Kobo. 

### Book collection

**TODO**

The script has been run on these books already, found in the examples directory:

> Olivia Twist
> Of Mice and Women
> Charlie's Web
> John Eyre
> Danielle Copperfield
> Dawn Quixote
> Bob's Adventures in Wonderland
> Francinestein / Fannystein / Francescastein


### Usage
_Python 3 only_

Get the repo:

```bash
git clone https://github.com/Garrett-R/gender_bender.git
cd gender_bender
```

It can be run as a script:

```bash
./main.py --input Lord_of_the_Flies.epub  --output Lady_of_the_Flies.epub
```

Or from python3:

```python
from gender_bender import gender_bend_epub
gender_bend_epub('./Mythcial_Man_Month.epub')
```

You can also gender-bend a string:

```python
from gender_bender import gender_bend
gender_bend('I suffer not a woman to teach, nor to usurp authority over the man, but to be in silence.')
```

Note: The script will need help flipping the names (but will provide a suggestion each time for conevenience).

### TODO

- Is there some way to also examine other underrepresented groups like transsexuals?
- Options for better automation of the name guessing
