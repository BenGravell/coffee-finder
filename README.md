# Coffee Finder
An app designed to help you find good coffee.


## Development

### Pre-commit
Run
```bash
pre-commit run --all-files
```
to run all pre-commit hooks, including style formatting and unit tests.


### Package management
Update [`requirements.in`](requirements.in) with new direct dependencies.

Then run
```bash
pip-compile requirements.in
```
to update the [`requirements.txt`](requirements.txt) file with all indirect and transitive dependencies.

Then run
```bash
pip install -r requirements.txt
```
to update your virtual environment with the packages.
