test:
	semgrep --test ./

scan:
	semgrep scan \
		--metrics=off \
		--disable-version-check \
		--config "p/python" \
		--config .semgrep/ \
		--error \
		-c . \
		--exclude ../.semgrep/ \
		../src/
