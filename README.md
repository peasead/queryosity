# Queryosity

**Fast, scriptable academic-research helper powered by Google Gemini 2.5 Pro**  
(Optionally expandable to Web of Science)

---

## ✨ What it does
`queryosity.py` accepts a question, topic, or full paragraph and:

1. Asks **Gemini 2.5 Pro** (Vertex AI) to emulate a Google Scholar search.  
2. Returns the top *n* papers (default = 5) with title, abstract, relevance score, and link.  
3. Prints results in **Markdown** (CLI) or saves to **`.md`**, **`.json`**, or **`.csv`**.  
4. (Optional) Includes a commented-out Web of Science (WoS) block for richer metadata if you have a WoS API key.

---

## 🛠 Quick Setup

### 1. Clone & enter the repo
```bash
git clone https://github.com/peasead/queryosity.git
cd queryosity
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 2. Open Google Cloud Console → select (or create) a project.
Enable Vertex AI API and Generative AI access.
* Go to https://console.cloud.google.com/vertex-ai/studio/multimodal
* Click Enable for Gemini 2.5 Pro (or request access if prompted)

### 3. Grab your Project ID
Appears in the top blue bar (format: my-project-name).

### 4. Set your local Google Cloud authentication
If you don't have the `gcloud` package, use Homebrew to get it.
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install gcloud
```

After you have the `gcloud` package (follow the login prompts that will happen in your browser):
```bash
gcloud components install gcloud
gcloud auth login
gcloud auth application-default login
```

### 5. Populate the .env file
Set the project ID you collected from step 3 above in the `.env` file.

### 6. Test
Run this from the CLI to make sure you have authentication working (make sure you change `Project_ID` to your Project ID):
```bash
python - <<'PY'
import vertexai
from vertexai.preview.generative_models import GenerativeModel
vertexai.init(project="Project_ID", location="us-central1")
print(GenerativeModel("gemini-2.5-pro").generate_content("Hello!").text)
PY
```

### 7. Usage
```bash
python queryosity.py --help
usage: queryosity.py [-h] (--query QUERY | --input-file INPUT_FILE) [--results RESULTS] [--sort {relevance,retrieved}]
                     [--output OUTPUT]

Search academic research using Google Gemini / Google Scholar emulation.

options:
  -h, --help            show this help message and exit
  --query QUERY         Query string or question.
  --input-file INPUT_FILE
                        File containing query text.
  --results RESULTS     Number of results to retrieve (Gemini only for now).
  --sort {relevance,retrieved}
                        Sort order for output.
  --output OUTPUT       Optional output filename (auto-detects .md/.json/.csv).
```

### 8. Example
```bash
python queryosity.py --query "drought-resistant wheat"
# Research Results

1. [Physiological and Molecular Mechanisms of Drought Resistance in Wheat](https://www.mdpi.com/1422-0067/24/3/2727)
**Relevance:** 10/10
**Abstract:** Drought is one of the most serious abiotic stresses, which seriously affects the growth and development
of wheat and results in a large reduction in wheat yield. To cope with drought stress, wheat has evolved complex and
diverse response mechanisms at the morphological...
```
