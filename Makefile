all: test

.PHONY: test clean
test:
	python test.py

clean:
	find . -name "*~" -o -name "*.pyc" | xargs rm -f
