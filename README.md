# Odyssey Management
A repository to handle some of the stateless compute offerings for the Hellenic Community of Ottawa dance group. 
Including data pipelines, CI/CD principles and applications, cloud hosting (Google cloud run), Cloudflare pages. 
[Will be significantly expanded upon]


Needs expanding on Google Cloud Run for headless compute

Integration with Cloudflare pages for static Website hosting.

The code and function of this repository aims to be composed of serverless compute. Thus, this application **currently**
has no 'state' as it simply executes the given task.

## Development Setup

Local Development can be done on any traditional operating system as containerization and cloud compute is utilized.

My IDE flavour is the [PyCharm IDE from Jetbrains](https://www.jetbrains.com/pycharm/)

### Requirements:
- Python Version: `3.13`
- `.env` file with corresponding environment variables

#### Set up a [Virtual Environment](https://docs.python.org/3/library/venv.html) via
(python3 if on Ubuntu Linux)

```bash
python -m venv venv
which python
pip install --upgrade pip
pip install -r requirements.txt
```

### Environment Variables

Aside from using load_dotenv(), in local testing:
```bash
set -a
source .env
set +a
```