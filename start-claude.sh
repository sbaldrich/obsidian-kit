PATCHED_INSTALLED=$(mktemp)
PATCHED_MARKETPLACES=$(mktemp)
sed "s|$HOME/.claude|/root/.claude|g" \
  "$HOME/.claude/plugins/installed_plugins.json" > "$PATCHED_INSTALLED"
sed "s|$HOME/.claude|/root/.claude|g" \
  "$HOME/.claude/plugins/known_marketplaces.json" > "$PATCHED_MARKETPLACES"

docker run -it --rm \
  -v "$(pwd)":/workspace \
  -v "$HOME/.claude":/root/.claude \
  -v "$PATCHED_INSTALLED":/root/.claude/plugins/installed_plugins.json:ro \
  -v "$PATCHED_MARKETPLACES":/root/.claude/plugins/known_marketplaces.json:ro \
  -v "$HOME/.claude.json":/root/.claude.json \
  -v "$(pwd)/.credentials.json":/root/.credentials.json \
  -e CLAUDE_CODE_OAUTH_TOKEN=$CLAUDE_CODE_OAUTH_TOKEN \
  claude-sandbox

rm -f "$PATCHED_INSTALLED" "$PATCHED_MARKETPLACES"
