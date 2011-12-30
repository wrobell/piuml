RSYNC=rsync -zcav \
	--exclude=\*~ --exclude=.\* \
	--delete-excluded --delete-after \
	--no-owner --no-group \
	--progress --stats

homepage: .homepage-stamp
epydoc: .epydoc-stamp
sphinx: .sphinx-stamp

doc: .homepage-stamp .epydoc-stamp .sphinx-stamp

.homepage-stamp:
	$(RSYNC) doc/homepage build

.epydoc-stamp:
	epydoc --config=doc/epydoc.conf --no-private --simple-term --verbose

.sphinx-stamp:
	sphinx-build-3 doc build/homepage/doc
	sphinx-build-3 -b epub doc doc-tmp-epub
	cp doc-tmp-epub/*.epub build/homepage/doc
	cp doc/user/*.pdf build/homepage/doc/user/

upload-doc:
	$(RSYNC) build/homepage/ wrobell@maszyna.it-zone.org:~/public_html/piuml

