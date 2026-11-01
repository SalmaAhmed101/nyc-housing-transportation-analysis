# nyc-housing-transportation-analysis
An interactive data engineering and visualization project exploring the relationship between housing development and transportation in New York City using NYC Open Data.

Outputs were recorded on 29/10/2026


# nyc-housing-transportation-analysis
An interactive data engineering and visualization project exploring the relationship between housing development and transportation in New York City using NYC Open Data.

Outputs were recorded on 29/10/2026

## Contributions
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