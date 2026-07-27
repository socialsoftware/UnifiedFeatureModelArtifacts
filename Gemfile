source "https://rubygems.org"

# The github-pages gem pins Jekyll and every plugin to the exact versions
# running on GitHub's build servers. Do not replace it with a bare "jekyll"
# gem: that installs Jekyll 4.x, while Pages still builds with 3.9.x, and the
# local preview would stop matching the live site.
gem "github-pages", group: :jekyll_plugins

# Unbundled from the Ruby stdlib in 3.0-3.4 but still assumed present by
# Jekyll 3.10. Required explicitly so `bundle exec jekyll serve` works on
# Ruby 3.4 (this machine runs 3.4.10). Drop any of these and Jekyll fails to
# boot with `cannot load such file -- <name> (LoadError)`.
gem "webrick", "~> 1.8"
gem "csv", "~> 3.3"
gem "base64", "~> 0.2"
gem "bigdecimal", "~> 3.1"
gem "erb"
