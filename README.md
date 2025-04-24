# llm-exa

[![PyPI](https://img.shields.io/pypi/v/llm-exa.svg)](https://pypi.org/project/llm-exa/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/nicobailon/llm-exa/blob/main/LICENSE)

LLM plugin for accessing [Exa.ai](https://exa.ai) - an AI-powered search engine and data retrieval API.

## Installation

Install this plugin in the same environment as [LLM](https://llm.datasette.io/).

```bash
llm install llm-exa
```

Or install directly from PyPI:

```bash
pip install llm-exa
```

## Configuration

First, set an API key for Exa.ai:

```bash
llm keys set exa
# Paste your Exa.ai API key here
```

You can obtain an API key by signing up at [exa.ai](https://exa.ai) and navigating to your dashboard.

## Available Models

This plugin provides access to the following Exa.ai capabilities:

- `exa-search` - Search the web using Exa.ai's neural or keyword search
- `exa-search-contents` - Search and retrieve full content of relevant web pages
- `exa-find-similar` - Find web pages similar to a provided URL
- `exa-answer` - Get direct answers to questions with citations from the web

You can view all models and their options with:

```bash
llm models
llm models --options
```

## Usage Examples

### Web Search

Search the web using neural search (semantic understanding):

```bash
llm -m exa-search "Latest developments in quantum computing" --option type neural
```

Search with category filtering:

```bash
llm -m exa-search "Recent papers on LLMs" --option category "papers" 
```

Limit search to specific domains:

```bash
llm -m exa-search "Climate change impacts" --option include_domains '["nature.com", "science.org"]'
```

### Search with Full Content Retrieval

Search and get full content of web pages:

```bash
llm -m exa-search-contents "The future of renewable energy" --option text true --option highlights true
```

Include summaries of retrieved pages:

```bash
llm -m exa-search-contents "AI chip advancements" --option summary true 
```

### Finding Similar Content

Find pages similar to a URL:

```bash
llm -m exa-find-similar "https://example.com/article-about-agi" 
```

Exclude the original domain:

```bash
llm -m exa-find-similar "https://example.com/some-article" --option exclude_domains '["example.com"]'
```

### Getting Direct Answers

Get a direct answer to a question with citations:

```bash
llm -m exa-answer "What are the environmental impacts of blockchain?"
```

Stream the answer in real-time:

```bash
llm -m exa-answer "What are the latest developments in fusion energy?" --option stream true
```

## Options

Common options for all models:

- `num_results` - Number of results to return (default: 5)
- `text` - Whether to include full text content (default: true)

Search-specific options:

- `type` - Search type: "neural", "keyword", or "auto" (default: "auto")
- `category` - Filter by data category (e.g., "company", "research paper", "news")
- `include_domains` - List of domains to include in search
- `exclude_domains` - List of domains to exclude from search

Content-specific options:

- `highlights` - Include relevant highlights in response (default: false)
- `summary` - Include generated summary in response (default: false)

Answer-specific options:

- `stream` - Stream the response (default: true)

## Development

To set up this plugin locally:

```bash
git clone https://github.com/nicobailon/llm-exa.git
cd llm-exa
python -m venv venv
source venv/bin/activate
pip install -e '.[test]'
```

## Troubleshooting

### Model Name Display

After installation, you might see model names displayed as "Exa: Search" rather than with the expected "exa-" prefix in the output of `llm models`. This is because the model ID (which includes the prefix) is used internally, while the display name is shown in the model list.

If you're not seeing the Exa models at all after installation, you may need to reinstall:

```bash
llm uninstall llm-exa
llm install llm-exa
```

### Plugin Version

When developing or testing changes to the plugin, you might need to reinstall it to see your changes:

```bash
pip install -e . --force-reinstall
```

You can check which version is installed with:

```bash
pip show llm-exa
```

### Plugin Not Found in Virtual Environments

**Only relevant if using virtual environments:** If you've installed the plugin but it doesn't appear when running `llm plugins`, you might be using different Python environments for LLM and the plugin.

To check if this is your issue, see which LLM executable you're running:

```bash
which llm
```

If you're developing with a virtual environment, you may need to:

1. Use the full path to your virtual environment's LLM:
   ```bash
   /path/to/your/venv/bin/llm plugins
   /path/to/your/venv/bin/llm -m exa-search "Your query"
   ```

2. Or create a helpful alias in your `.bashrc` or `.zshrc`:
   ```bash
   alias venv-llm='/path/to/your/venv/bin/llm'
   ```

## License

This project is licensed under the Apache License 2.0.
