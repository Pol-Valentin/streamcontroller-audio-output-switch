# Makefile for Audio Output Switch StreamController Plugin

# Plugin configuration
PLUGIN_ID = com_pol_audio_switch
PLUGIN_NAME = Audio Output Switch

# StreamController paths
SC_PLUGINS_DIR = $$HOME/.var/app/com.core447.StreamController/data/plugins
PLUGIN_DEST = $(SC_PLUGINS_DIR)/$(PLUGIN_ID)

# Current directory
CURRENT_DIR = $(shell pwd)

.PHONY: help install uninstall clean link unlink status

help:
	@echo "Audio Output Switch Plugin - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install      - Install plugin to StreamController plugins directory"
	@echo "  uninstall    - Remove plugin from StreamController"
	@echo "  link         - Create symbolic link for development (recommended)"
	@echo "  unlink       - Remove symbolic link only"
	@echo "  clean        - Remove Python cache files and generated icons"
	@echo "  status       - Check plugin installation status"
	@echo "  help         - Show this help message"

install:
	@echo "Installing $(PLUGIN_NAME)..."
	@mkdir -p $(SC_PLUGINS_DIR)
	@if [ -L "$(PLUGIN_DEST)" ]; then \
		echo "Symbolic link exists, removing it first..."; \
		rm -f "$(PLUGIN_DEST)"; \
	fi
	@if [ -d "$(PLUGIN_DEST)" ]; then \
		echo "Plugin directory exists, removing it..."; \
		rm -rf "$(PLUGIN_DEST)"; \
	fi
	@echo "Copying plugin files..."
	@cp -r $(CURRENT_DIR) $(PLUGIN_DEST)
	@echo "Plugin installed at $(PLUGIN_DEST)"
	@echo ""
	@echo "Please restart StreamController to load the plugin."

link:
	@echo "Creating symbolic link for $(PLUGIN_NAME)..."
	@mkdir -p $(SC_PLUGINS_DIR)
	@if [ -d "$(PLUGIN_DEST)" ] && [ ! -L "$(PLUGIN_DEST)" ]; then \
		echo "Plugin directory exists (not a link), removing it..."; \
		rm -rf "$(PLUGIN_DEST)"; \
	fi
	@if [ -L "$(PLUGIN_DEST)" ]; then \
		echo "Symbolic link already exists, recreating..."; \
		rm -f "$(PLUGIN_DEST)"; \
	fi
	@ln -s $(CURRENT_DIR) $(PLUGIN_DEST)
	@echo "Symbolic link created: $(PLUGIN_DEST) -> $(CURRENT_DIR)"
	@echo ""
	@echo "Development mode enabled. Changes will be reflected after reloading StreamController."

unlink:
	@echo "Removing symbolic link for $(PLUGIN_NAME)..."
	@if [ -L "$(PLUGIN_DEST)" ]; then \
		rm -f "$(PLUGIN_DEST)"; \
		echo "Symbolic link removed."; \
	else \
		echo "No symbolic link found at $(PLUGIN_DEST)"; \
	fi

uninstall:
	@echo "Uninstalling $(PLUGIN_NAME)..."
	@if [ -e "$(PLUGIN_DEST)" ]; then \
		rm -rf "$(PLUGIN_DEST)"; \
		echo "Plugin removed from $(PLUGIN_DEST)"; \
	else \
		echo "Plugin not found at $(PLUGIN_DEST)"; \
	fi

clean:
	@echo "Cleaning Python cache files and generated icons..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@if [ -d "cache" ]; then \
		rm -rf cache/*.png 2>/dev/null || true; \
		echo "Cleared cache directory."; \
	fi
	@echo "Cache cleaned."

# Check if plugin is installed
status:
	@echo "Checking plugin status..."
	@if [ -L "$(PLUGIN_DEST)" ]; then \
		echo "Status: Linked (development mode)"; \
		echo "Target: $$(readlink $(PLUGIN_DEST))"; \
	elif [ -d "$(PLUGIN_DEST)" ]; then \
		echo "Status: Installed (copy mode)"; \
		echo "Location: $(PLUGIN_DEST)"; \
	else \
		echo "Status: Not installed"; \
	fi
