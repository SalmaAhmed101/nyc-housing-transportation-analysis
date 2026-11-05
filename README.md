# nyc-housing-transportation-analysis
An interactive data engineering and visualization project exploring the relationship between housing development and transportation in New York City using NYC Open Data.

Outputs were recorded on 29/10/2026


## Contributions
### Member 1: Housing Data Preparation and cleaning
- Selected and justified the housing dataset (DOB NOW: Build – Job Application Filings, H5).
- EDA: structure, data types, missing values, duplicates, outliers, and inconsistencies.
- Pre-integration cleaning and standardization (borough, ZIP, dates, numeric domain rules, deduplication to one row per job).
- Validation visualizations and the saved `housing_clean.csv`.
- Research Questions 1 and 2 on the integrated data are in the separate notebook `member1_research_questions.ipynb`.

### Member 2: Transportation Data Preparation and cleaning
- Selected and justified the transportation dataset (SIRTA, T4)
- Conducted exploratory data analysis (EDA), including data structure, data types, missing values, duplicates, outliers, and inconsistencies
- Performed data cleaning and standardization and creating validation charts and checks(`notebooks/transportation_data_cleaning_and_analysis.ipynb`)
- Produced the cleaned transportation dataset(`outputs/member2_transportation/sirta_clean.csv`)
- Defined two research questions using member 3's final integrated dataset, investigating the relationship between new housing development and traffic safety: repeat-risk crash shares and total serious crashes (KSI) (`notebooks/member2_research_questions.ipynb`)

### Member 4: Research Analysis and Data Storytelling
- Defined two research questions: borough harm per new housing unit, and project size vs harm per filing.
- Checked Member 3's integrated table for structure, grid completeness, missing values and distributions.
- Built and charted both questions with interpretations and limitations in `notebooks/m4_research_analysis.ipynb`.
- Wrote the limitations and benefit to NYC, and drafted the website story section in `website/story.md`.

### Member 5: Website Interface and Filters
- Built the Streamlit website in `website/app.py`: a three-page story (Overview, Insight, Action) with borough, year, district, harm and housing-activity dropdowns, and a search box that sets them.
- Rebuilt the research charts from Members 1 to 4 from the saved CSVs in `outputs/` so they respond to the filters, and left spots for Member 6.
- Defined two research questions: whether months with more planned housing have more serious crashes by borough, and whether new housing is more concentrated than serious harm (`notebooks/m5_research_questions.ipynb`).
- Added `requirements.txt`. To run: `pip install -r requirements.txt`, then `streamlit run website/app.py`.
