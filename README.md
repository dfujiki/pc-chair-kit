# PC Chair Kit
This is a kit to make PC chairs lives less painful.

This code is foked from the code written for ISCA-18 ( Which used code from the ISCA 17 and Micro 17). This code is further developed by Daichi Fujiki and Deval Shah for MICRO'19 under the guidance of Prof. Tor M. Aamodt and Prof. Reeturparna Das.
 
They can be used for the following tasks:
* Conflict of interest management.
* Paper assignments.
* Meeting management ( Slides generation to display the Conflict information in the meeting room and Hallways).
* Post expert generosity analysis of scores which considers the generosity factor of each reviewer.

To start, run:
```
python3 -m pip install -r requirements.txt [--user]
```
## Conflict of interest (COI) management
We check COIs flagged by authors, PC members and we also automatically generate a list of recent co-authors for all PC members using DBLP data. All conflict data can be entered in HotCRP through he `Assignment` page.

The workflow for checking/flagging COIs between papers and PC members is the following:
1. Generate a `.csv` with a list of the PC members, with their first and last names. This list has to be manually generated, and it has the following format:
```
id, first_name, last_name, email
1, PCFirstName1, PCLastName1, PCEmail
```

2. Use the first list as an input to DBLP crawler. To do so, run:
```bash
python3 dblp_crawler.py author-keys --author-list AUTHOR_LIST_FILE --author-keys AUTHOR_KEYS_FILE
```
This command will generate another CSV file in `AUTHOR_KEYS_FILE` which has all the DBLP keys that matched the author names. Your job now is to go through that file and filter out all the bad entries (i.e., homonyms). You can do that by removing the `x` in the `valid` column of `AUTHOR_KEYS_FILE`.

3. Generate the paper list from the author-keys file. To do so, run:
```bash
python3 dblp_crawler.py paper-list --author-keys AUTHOR_KEYS_FILE --paper-list PAPER_LIST_FILE
```
This command will generate another CSV file in `PAPER_LIST_FILE` with all the papers authored by each PC member. Your job now is to go through that file and filter out all the bad entries (i.e., papers that do not constitute COI with co-authors), the same way you filtered out the author keys. ~~After filtering this file, add another column to the file (1st column) with the PC emails. Excel helps to perform this task.~~

4. Generate the co-author list from the paper list. To do so, run:
```bash
python3 dblp_crawler.py list-co-authors --paper-list PAPER_LIST_FILE
```
This command will warm up the paper cache so that every time you read from this list, you won't have to query it from DBLP. As you might notice, querying DBLP takes a long time.

5. Download and clean paper information from HotCRP. Go to HotCRP and download all the paper info. Search for all submitted papers, and, on the bottom of the page, click `select all`, and, in the drop-down list, select `JSON`, and click go. You will get a JSON file. In that file, you need to clean up all the information. For every paper, make sure that the COI list (collaborators) is in the following form:
```
Institution1 \n
All (Institution1) \n
AuthorFirstName AuthorLastName, Instutution2 \n
```
The scripts will interpret everything that does not have a `,` or a `(` before the end of the line as an institution name, and everything else as an author name. Make sure there is no line with multiple institutions/authors. The scripts will ignore authors institutions. Therefore, it is enough to end author names with a `,` to make sure the script will recognize them. Keep an eye on names that are common and short, as the cause lots of trouble when matching strings. For the author list, make sure that, for authors with multiple affiliations, you list all the affiliations in the `collaborators` field, as the scripts won't be able to recognize multiple affiliations.

Cleaning up submission data is a time consuming and error prone task, therefore, make sure you have the time to do it. Do not create any deadlines shortly after the submission deadline, as you might find yourself spending days parsing through bad author data. To aid in this task, you can use the `collab_format_checker.py` script, that looks for suspicious entries in the collaborator fields. Look at the script for more details.

6. Download and clean PC data. Go to HotCRP `User` page and select the PC. On the bottom of the page, click on `select all` and download `PC info`.

7. Cross check all conflicts. You can do so by running:
```bash
python3 cross_reference_conflcits.py INSTITUTIONS_CSV PAPER_DATA PC_INFO PC_PAPERS OUT_PROPER_CONFLICTS PAPER_COLLABS_FIELD_CONFLICTS PC_COLLABS_FIELD_CONFLICTS DBLP_COLLABS_FIELD_CONFLICTS SUSPICIOUS_CONFLICTS
```

This script takes the following inputs:
* **INSTITUTIONS_CSV** CSV file with a list of institutions and their aliases. We added ours to this repo, in `data/institutions.csv`, and you can add institutions to that file as you see fit.
* **PAPER_DATA** The `.json` file you downloaded and cleaned with the paper info.
* **PC_INFO** The `.csv` file you downloaded and cleaned with the PC info
* **PC_PAPERS** The `.csv` file you generated and filtered with the list of PC papers.
* **OUT_PROPER_CONFLICTS** The output file with the proper conflicts (the conflicts flagged by authors in the submission form.
* **OUT_PAPER_COLLABS_FIELD_CONFLICTS** The output file with conflicts that are detected by checking the paper collabs field of the submission
* **OUT_PC_COLLABS_FIELD_CONFLICTS** The output file with conflicts that are detected by checking the paper collabs field of the PCs
* **OUT_DBLP_COLLABS_FIELD_CONFLICTS** The output file with conflicts that are detected through DBLP
* **OUT_SUSPICIOUS_CONFLICTS** The output file with conflicts that are flagged by authors but can't be checked elsewhere

Check the outputs for bad conflicts. Bad conflicts are normally from common names and very short names.
After you double check the conflicts csvs, clearing the 'valid' column of the conflicts that are incorrect, you can generate the '.csv' that will be used by HotCRP:

```bash
python3 report_to_csv OUT_REPORT_CSV OUT_HOTCRP_CSV
```

You can upload this conflicts from the `Assignment` page in HotCRP.

## Paper assignments
Paper assignment is a difficult task because both PC members and paper authors are inconsistent when listing their topics of interest. We build some infrastructure to aid in this task.

The script `paper_affinity.py` Generates affinity reports based on an expertise DB and the number of citation made from paper to PC members. The intuition is that papers that cite a particular PC member a lot should be reviewed by that PC member. 

#### Generating the citation reports

First, you have to generate a citation report. You will need to download `pdftotext` to do so. After you downloaded `pdftotext`, download all the pdfs from HotCRP and place them in a folder `PDF_FOLDER`. Copy the contents of `WordCnt_And_Reference_Logger` to `PDF_FOLDER` and, from that folder run:
```
./wordscript.sh
```

#### Generating affinity reports

With the citation report, run:
```bash
python3 paper_affinity.py --expertise-db EXPERTISE_DB --paper-json PAPER_DATA --pc-csv PC_INFO --expertise-to-topics EXPERTISE_TO_TOPICS --submissions PDF_FOLDER --out-pc-topics OUT_PC_TOPICS --out-pc-citations OUT_PC_CITATIONS --out-affinity OUT_AFFINITY
```
Where:
* **EXPERTISE_DB** list of authors expertises in the format:
```
id,First Name,Last Name,email,[comma separated list of expertises]
id1,PCMcmberFirstName1,PCMcmberLastName1,email,[list of expertises with `1` if the pc member is an expert and nothing otherwhise
```
* **PAPER_DATA** The `.json` file you donwloaded and cleaned with the paper info.
* **PC_INFO** The `.csv` file you you downloaded and cleaned with the PC info
* **EXPERTISE_TO_TOPICS** A file that maps PC expertise to paper topics, in case they differ. An expertise can map to one or more topic, and a single topic can map to many expertises. This file has the format:
```
Expertise,Topic,,,,,,,,,,,
Expertise1,Topic1,Topic2,Topic3
```
* **PDF_FOLDER** Folder where papers are located
* **OUT_PC_TOPICS** PC topic reports.
* **OUT_PC_CITATIONS** PC citation reports.
* **OUT_AFFINITY** PC affinity reports.

## Managing the PC meeting (Conflict slides generation)

This script is used to generate the slides with conflict information for PC meeting. Each slide shows the conflict information of the current paper and the next paper. We used these slides to present the conflict information in the meeting room at the start of discussion of each paper, so that conflicted PC members can evacuate the room. We also presented the slides in the hallway so that any PC Members outside the meeting room can keep track.

If the PC members are divided into two groups G1 and G2 and there are two parallel dicsussions, then the script can be used to generate slides for separate sessions as well, in such case, names of the PC member for given session can be highlighted.

For example, dummy database is added, which is to be replaced with actual data downlaoded from Hotcrp site.

Mainly, three files are needed

* Paper data in csv format: `\*-data.csv`
* Pc info in csv format: `\*-pcinfo.csv`
* Paper conflict information in csv format: `\*-pcconflicts.csv` 
	* This list should be in the discussion order. For that it is recommended that the papers are sorted in the discussion order on HotCrp site and then the conflict info is downloaded.

Example:
For joint session,
``` 
bash meeting_slides.sh micro2019-pcconflicts.csv joint micro2019-pcinfo.csv micro2019-data.csv
```
If the PC meeting is divided into two groups then:
```
bash meeting_slides.sh G1-micro2019-pcconflicts.csv G1 micro2019-pcinfo.csv micro2019-data.csv
bash meeting_slides.sh G2-micro2019-pcconflicts.csv G2 micro2019-pcinfo.csv micro2019-data.csv
```
Some attributes are hardocded in the Python script, which need to be modified.
e.g. 

* Tags used to divide the PC members: G1-PC, G2-PC, ERC
* Tags used to divide papers into two groups: G1 and G2
* Chairs' email ID: pc-chair1@xyz.edu,pc-chair2@xyz.edu
* Chairss Names: PC chair 1, PC chair 2
* Alternate chair names (if the chair is in conflict with a paper): Alternate chair G1, Alternate chair G2


## Post-expert Generosity analysis

Generosity mean and post-expert generosity mean metrics were originally proposed by Prof. Onur Mutlu -  https://people.inf.ethz.ch/omutlu/pub/onur_program-chair-remarks_micro12_talk.pdf

This script calculates the the generosity mean and post expert generosity mean of the paper based on the merit score. It cosiders post rebuttal overall merit if availlable, else pre reposnse overall merit.

The script takes three files as input (these files can e downloaded frn=om HotCrp submission site):

* \*-reviews.csv: reviews in csv format
* \*-pcinfo.csv: PC information in csv format
* \*-data.csv: Paper data in csv format

The folder consists of dummy data files. 

To run the script, use following command
```
python generosity_score.py
```

The script generates csv files with relevant data and also some plots for better visualization of the generosity distribution of reviewers and papers, overall merit distribution etc..

* generosity_merits.csv
``
Main output with Generosity, post expert generosity merits of papers. It also contains generosty seggregation for PC members and ERC members as well as reviewers' generosity score.
``
* contradictory_review.csv
``
Some papers might have descrepency between "overall merit" and "where would you rank the paper in pile". This file contains papers' list where the overall merit is <=2 but the paper is still in top 50% according to the reviewers. 	
``
* generosity_reviewer.csv
``
Contains the overall generosity of reviewers, Round 1 generosity, round 2 generosity, average merit given by the reviewer..
``

* G1/G2_avg_gen_with_ERC.png 
``generosity distribution of papers in G1/G2 group. Generosity of ERC members is also considered in the calculation of average generosity.
``
* G1/G2_avg_gen_without_ERC.png
``
 generosity distribution of papers in G1/G2 group. Generosity of ERC members is not considered in the calculation of average generosity.
``
* generosity_of_reviewer.png
``
Generosity dostribution of reviewers' generosity
``
* Post-Rebuttal_overall_merit.png
``
Post rebuttal average merit distribution of all the papers
``
* generosity_mean_Post-Rebuttal_overall_merit.png
``
generosity mean distribution of all the papers
``
* post_expert_generosity_mean_Post-Rebuttal_overall_merit.png
``
Post expert generosity mean distribution of all the papers
``

Notes:
* The script assumes some spacific tags for papers and PC members, the script needs to be modified for using different tags.
* Also, the script is designed for 2 groups of PC members, 2 rounds of reviews, 3 reviewers for the first round and 2 additional reviewers for the 2nd round. The script needs to be modified in cases there are some changes.

