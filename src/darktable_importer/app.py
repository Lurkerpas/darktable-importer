
def main() -> None:
    pass

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - safety net for CLI entrypoint
        print(f"darktable-importer failed: {exc}", file=sys.stderr)
        raise