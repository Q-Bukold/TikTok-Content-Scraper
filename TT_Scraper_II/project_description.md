Welcome to this project. The idea of this branch is to create a second, overhauled version of the TT_Scraper Module. The motivation for this overhaul is as followed:

# Filepath generation is too complicated
Due to the fact that the scraper was originally not meant to be published and evolved into something more and more comprehensive, the structure became to complicated over time. This lead to a very complicated way of naming files.

Due to the fact that we, depending on the scraped object, have multiple combinations of outputs, an ad-hoc version of naming files was invented. It is very complicated and makes additional functions difficult to implement.

> A new version should be able to cover the following combinations of output:
> 1. .json (video metadata)
> 2. .json (picture metadata)
> 3. .json (account metadata)
> 4. .json + .mp4 (video)
> 5. .json + N * .jpeg + .mp3 (slide with multiple pictures and music)

# No functioning Sub-Modules
If one part of the scraper is changed, the structure causes errors. Thus it might be better to switch to a more module like approach. 

A possible structure could be as follows:
```
/ pipeline with error handling  list of usernames / ids -> download of data
    / metadata scraper  ID -> JSON-like metadata
    / video scraper     JSON-like metadata -> mp4-like object
    / slide scraper     JSON-like metadata -> jpeg-like objects + mp3-like object
    / account scraper   username -> JSON-like metadata
```

Every scraper shall return one data object or the original error message it encountered. The errors are managed by the pipeline.

---
# Best Practises
1. Functions that cant be used begin with an "_"
2.