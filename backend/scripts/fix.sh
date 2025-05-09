set -e

echo "Autoformatting with isort..."
uv run isort .

echo "Autoformatting with black..."
uv run black .

echo "Auto-fixing with ruff..."
uv run ruff check . --fix

echo -e "\n✅ Codebase formatted!"
