# scan_cleaner

crop and cleanup scanned paper images

ScanSnap recommended.

## example

```bash
find scanned -name '*.png' | sort | \
  scan_cleaner --dpi 300 --size a4 --direction landscape --mode gray -P 4 -o pages.pdf
```

