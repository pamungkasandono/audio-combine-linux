BUILD_DIR = build
BINARY    = audio-combine
SRC       = ./cmd/app/main.go

.PHONY: all build run install uninstall linux linux-arm clean

all: build

# Jalankan langsung
run:
	go run $(SRC)

# Build platform saat ini
build:
	mkdir -p $(BUILD_DIR)
	go build -ldflags="-s -w" -o $(BUILD_DIR)/$(BINARY) $(SRC)
	@echo "✓ Build selesai: ./$(BUILD_DIR)/$(BINARY)"

# Install ke system
install: build
	sudo cp $(BUILD_DIR)/$(BINARY) /usr/local/bin/$(BINARY)
	sudo chmod +x /usr/local/bin/$(BINARY)
	@echo "✓ Installed: /usr/local/bin/$(BINARY)"

# Hapus dari system
uninstall:
	sudo rm -f /usr/local/bin/$(BINARY)
	@echo "✓ Uninstalled: /usr/local/bin/$(BINARY)"

# Linux AMD64
linux:
	mkdir -p $(BUILD_DIR)
	GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" \
	-o $(BUILD_DIR)/$(BINARY)-linux-amd64 $(SRC)
	@echo "✓ $(BUILD_DIR)/$(BINARY)-linux-amd64"

# Linux ARM64
linux-arm:
	mkdir -p $(BUILD_DIR)
	GOOS=linux GOARCH=arm64 go build -ldflags="-s -w" \
	-o $(BUILD_DIR)/$(BINARY)-linux-arm64 $(SRC)
	@echo "✓ $(BUILD_DIR)/$(BINARY)-linux-arm64"

# Bersihkan hasil build
clean:
	rm -rf $(BUILD_DIR)
	@echo "✓ Clean selesai"