# 📋 Workplan: RSS to Kobo (Multi-User with Dropbox)

## ✅ Phase 1 — Project Setup (Completed)

1. **Repo Bootstrap**
   * [x] Initialize GitHub repo `rss-to-kobo`
   * [x] Commit baseline directory structure
   * [x] Add `.gitignore` with proper exclusions
   * [x] Set up `pyproject.toml` with project metadata and dependencies

2. **Documentation**
   * [x] Write comprehensive `README.md`
   * [x] Add dependency management via `pyproject.toml`
   * [x] Add MIT License

---

## ✅ Phase 2 — Core Functionality (Completed)

1. **Feed Parsing**
   * [x] Implement `scripts/fetch_and_build.py`
   * [x] Load feed config from YAML
   * [x] Fetch and parse RSS with `feedparser`
   * [x] Limit articles per feed with `max_articles`
   * [x] Basic HTML cleaning with `beautifulsoup4`

2. **EPUB Builder**
   * [x] Implement `scripts/epub_builder.py`
   * [x] Generate title page with date
   * [x] Create feed-based chapters
   * [x] Prefix article titles with feed name
   * [x] Generate TOC for navigation

3. **Dropbox Uploader**
   * [x] Implement `scripts/upload_to_dropbox.py`
   * [x] Token-based authentication
   * [x] Chunked file upload support
   * [x] Overwrite existing files

---

## ✅ Phase 3 — Multi-User Support (Completed)

1. **Config Handling**
   * [x] Add `--user` CLI flag support
   * [x] User-specific config files in `feeds/`
   * [x] User-specific output files

2. **Token Management**
   * [x] Document Dropbox token setup
   * [x] Secure token storage in `dropbox_tokens/`
   * [x] Token loading with error handling

3. **Isolation**
   * [x] Separate configs per user
   * [x] Isolated file operations

---

## ✅ Phase 4 — Automation (Completed)

1. **systemd Integration**
   * [x] Create `systemd/rss-to-kobo@.service`
   * [x] Create `systemd/rss-to-kobo@.timer`
   * [x] Document systemd setup in README
   * [x] Configure daily execution at 6:00 AM

2. **Directory Structure**
   * [x] Add `.gitkeep` files for required directories
   * [x] Document directory structure

---

## 🔄 Phase 5 — Quality & Polish (In Progress)

1. **Logging**
   * [x] Basic logging implemented
   * [ ] Add more detailed logging
   * [ ] Add log rotation

2. **Error Handling**
   * [x] Basic error handling in place
   * [ ] Add retry logic for failed operations
   * [ ] Improve error messages

3. **Validation**
   * [ ] Test with multiple feeds
   * [ ] Verify EPUB generation quality
   * [ ] Test on actual Kobo device

4. **Documentation**
   * [x] Basic setup instructions
   * [ ] Add troubleshooting guide
   * [ ] Add FAQ section

---

## 📅 Phase 6 — Release (Pending)

1. **Tag v1.0.0**
   * [ ] Final testing
   * [ ] Update version in `pyproject.toml`
   * [ ] Create GitHub release

2. **Documentation**
   * [ ] Complete all documentation
   * [ ] Add examples
   * [ ] Create CONTRIBUTING.md

3. **Community**
   * [ ] Set up issue templates
   * [ ] Add pull request template

---

## 🚀 Next Steps

1. **Testing**
   - [ ] Test with multiple RSS feeds
   - [ ] Verify EPUB generation quality
   - [ ] Test on Kobo device

2. **Documentation**
   - [ ] Add more detailed examples
   - [ ] Create troubleshooting guide
   - [ ] Add screenshots of generated EPUBs

3. **Enhancements**
   - [ ] Add support for more feed formats
   - [ ] Implement feed discovery
   - [ ] Add web UI for configuration

---

## 🏆 Current Status

✅ Core functionality is complete and working
✅ Multi-user support implemented
✅ Automated with systemd
📝 Documentation needs completion
🧪 More testing required
