---

# How Alt-Tech Users Evaluate Search Engines: Cause-Advancing Audits  

This repository contains the data and code used in the study **"How alt-tech users evaluate search engines: Cause-advancing audits"**.  

---

## 📁 Folder Structure  

```plaintext
main/
├── data/
│   ├── annotations/
│   │   ├── GPT_Annotations/
│   │   │   ├── annotationsv1/
│   │   │   ├── annotationsv2/
│   │   │   └── annotationsv3/
│   │   └── human_annotations/
│   ├── processed/
│   └── raw/
├── src/
└── results/
```

---

## 📊 Data  

- **`search_engine_list.csv`**  
  Contains a list of the search engines considered in this study, modified from Wikipedia.  

- **`data/`**  
  - **`raw/`**: Contains the raw data extracted from /pol/ (see: `src/01_4plebs_scraper.R`).  
  - **`processed/`**: Includes the cleaned and unified data (see: `src/02_unify_4plebs_data.py`).  
  - **`annotations/`**:  
    - **`human_annotations/`**: Human annotations by two independent annotators for a sample of 4chan /pol/ comments.  
    - **`GPT_Annotations/`**: GPT-4 outputs for three different prompts described in the paper (see `prompts.txt`).  

---

## 🛠️ Code  

The following scripts should be executed sequentially to reproduce the results.  
**Note**: The provided scripts are tailored for prompt v1. For prompts v2 or v3, replace `annotationsv1` with `annotationsv2` or `annotationsv3` throughout the scripts.  

1. **`01_4plebs_scraper.R`**: Extracts mentions of search engines from 4plebs.  
2. **`02_unify_4plebs_data.py`**: Cleans and unifies the extracted data.  
3. **`03_gpt_api.py`**: Sends data to GPT-4 for annotation.  
   - Update the OpenAI API key in the script.  
   - Adjust the `clean_and_save_response` function for potential formatting changes in GPT outputs.  
4. **`04_generate_results.R`**: Creates the visualizations and tables presented in the paper.  
5. **`05_annotator_agreement.py`**: Analyzes annotator agreement.  

---

## 📈 Results  

Result files generated from `04_generate_results.R` are stored in the `results/` folder.  

---

## 📜 Citation  

If you use this repository, please cite our work:  

```bibtex
@article{williams2024causeaudit,
  title={How alt-tech users evaluate search engines: Cause-advancing audits},
  author={Williams, Evan M and Carley, Kathleen M},
  publisher={Harvard Kennedy School Misinformation Review},
  year={2025}
}
```  


