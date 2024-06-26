include $(REPO_PATH)/defines.make

PYTHON3_MODULES := python3-modules

PYTHON3_MODULES_INSTALL_DIR := $(INTERMEDIATE_INSTALL_BASE)/$(PYTHON3_MODULES)
PYTHON3_MODULES_BUILD_DIR := $(BAZEL_BIN)/omd/packages/$(PYTHON3_MODULES)/$(PYTHON3_MODULES)

PYTHON3_MODULES_INTERMEDIATE_INSTALL := $(BUILD_HELPER_DIR)/$(PYTHON3_MODULES)-install-intermediate
PYTHON3_MODULES_INSTALL := $(BUILD_HELPER_DIR)/$(PYTHON3_MODULES)-install

PACKAGE_PYTHON3_MODULES_PYTHON_DEPS := $(OPENSSL_CACHE_PKG_PROCESS) $(PYTHON_CACHE_PKG_PROCESS) $(PYTHON3_MODULES_CACHE_PKG_PROCESS)

# Used by other OMD packages
PACKAGE_PYTHON3_MODULES_DESTDIR    := $(PYTHON3_MODULES_INSTALL_DIR)
PACKAGE_PYTHON3_MODULES_PYTHONPATH := $(PACKAGE_PYTHON3_MODULES_DESTDIR)/lib/python$(PYTHON_MAJOR_DOT_MINOR)/site-packages
# May be used during omd package build time. Call sites have to use the target
# dependency "$(PACKAGE_PYTHON3_MODULES_PYTHON_DEPS)" to have everything needed in place.
PACKAGE_PYTHON3_MODULES_PYTHON         := \
	PYTHONPATH="$$PYTHONPATH:$(PACKAGE_PYTHON3_MODULES_PYTHONPATH):$(PACKAGE_PYTHON_PYTHONPATH)" \
	LDFLAGS="$$LDFLAGS $(PACKAGE_PYTHON_LDFLAGS)" \
	LD_LIBRARY_PATH="$$LD_LIBRARY_PATH:$(PACKAGE_PYTHON_LD_LIBRARY_PATH):$(PACKAGE_OPENSSL_LD_LIBRARY_PATH)" \
	$(PACKAGE_PYTHON_EXECUTABLE)

$(PYTHON3_MODULES_INSTALL): $(INTERMEDIATE_INSTALL_BAZEL)
	$(PACKAGE_PYTHON_EXECUTABLE) -m compileall \
	    -f \
	    --invalidation-mode=checked-hash \
	    -s "$(PACKAGE_PYTHON3_MODULES_PYTHONPATH)/" \
	    "$(PACKAGE_PYTHON3_MODULES_PYTHONPATH)/"
	$(RSYNC) --times $(PYTHON3_MODULES_INSTALL_DIR)/ $(DESTDIR)$(OMD_ROOT)/

