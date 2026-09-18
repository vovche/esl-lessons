# Repository navigation contract

Every public URL segment must be a useful page. The site hierarchy is:

`/` → `/<grade>/` → `/<grade>/<lesson>/`

When adding or moving a lesson:

1. Put it at `/<grade>/<lesson>/index.html`.
2. Ensure `/<grade>/index.html` exists and links to every lesson in that grade.
3. Ensure the root `index.html` links to the grade page and lists the lesson.
4. Add visible navigation inside the lesson to both the grade page and the root catalog. Use `data-site-nav="grade"` with `href="../"` and `data-site-nav="root"` with `href="../../"`.
5. Grade pages must link back to the root with `data-site-nav="root"` and `href="../"`.
6. Run `python3 tests/check_navigation.py` before committing.

Do not publish an orphan lesson or a numeric grade directory that returns 404. The navigation check runs in GitHub Actions and must pass before Pages deployment.
