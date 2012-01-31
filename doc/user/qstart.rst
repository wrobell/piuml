Quick Start
===========

Using of piUML consists of 3 simple steps

- describe model in piUML language using text editor of your choice
- set the layout (*note:* in the future layout management will be more
  automatic and shall require a bit of adjustment only)
- run piUML software to generate diagram

Let's take a simple model of reader and publication as shown on diagram
`ex-reader`_.

.. _ex-reader:

.. uml-diagram:: doc/examples/reader
    :align: center

    Example of reader and publication model diagram

The description of the model using piUML language is as follows

.. literalinclude:: /examples/reader.pml
    :linenos:

Notice the ``:layout:`` section changing the default layout of
``Publication`` and ``Book`` classes from horizontal to vertical.

Save the file as ``reader.pml`` and generate diagram in PDF format with piUML::

    piuml reader.pml

View the resulting file ``reader.pdf`` with PDF viewer.

.. vim: sw=4:et:ai
