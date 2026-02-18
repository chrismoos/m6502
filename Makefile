.PHONY: test test-klaus clean-test

test:
	uv run pytest test/test_runner.py -s -x
ifndef TESTCASE
	$(MAKE) test-klaus
endif

test-klaus:
	cd test && make -f Makefile.mcu_klaus run

clean-test:
	cd test && make -f Makefile.mcu_klaus clean
	rm -rf sim_build
