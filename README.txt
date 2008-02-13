**************
Transmogrifier 
**************

.. contents::

Transmogrifier provides support for building pipelines that turn one thing
into another. Specifically, transmogrifier pipelines are used to convert and
import legacy content into a Plone site. It provides the tools to construct
pipelines from multiple sections, where each section processes the data
flowing through the pipe.

A "transmogrifier pipeline" refers to a description of a set of pipe sections,
slotted together in a set order. The stated goal is for these sections to
transform data and ultimately add content to a Plone site based on this data.
Sections deal with tasks such as sourcing the data (from textfiles, databases,
etc.) and characterset conversion, through to determining portal type,
location and workflow state.

Note that a transmogrifier pipeline can be used to process any number of
things, and is not specific to Plone content import. However, it's original
intent is to provide a pluggable way to import legacy content.

Installation
************

See docs/INSTALL.txt for installation instructions.

Credits
*******

Development sponsored by
    Elkjøp Nordic AS
    
Design and development
    `Martijn Pieters`_ at Jarn_
    
Project name
    A transmogrifier_ is fictional device used for transforming one object 
    into another object. The term was coined by Bill Waterson of Calvin and 
    Hobbes fame.
    
.. _Martijn Pieters: mailto:mj@jarn.com
.. _Jarn: http://www.jarn.com/
.. _Transmogrifier: http://en.wikipedia.org/wiki/Transmogrifier
