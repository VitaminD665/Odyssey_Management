# Odyssey_Management
A repository to handle some of the stateless compute offerings for the Hellenic Community of Ottawa dance group. Including data pipelines, CI/CD principles and applications, cloud hosting (Google cloud run), Cloudflare pages. [Will be significantly expanded upon]]

Requires python 3.13

Needs expanding on Google Cloud Run for headless compute

Integration with Cloudflare pages and whatnot

The code and function of this repository aims to be composed of serverless compute. Thus this application
has no 'state' as it simply executes the given task.

Aside from using load_dotenv(), just use
```bash
set -a
source .env
set +a
```