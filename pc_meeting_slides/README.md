This script is used to generate the slides for PC meeting.
If the PC members are divided into two groups G1 and G2 and there are two parallel dicsussions, then the script can be used to generate slides for separate sessions as well.

For example, dummy database is added, which is to be replaced with actual data downlaoded from Hotcrp site.

Mainly, three files are needed

1) Paper data in csv format - \*-data.csv
2) Pc info in csv format - \*-pcinfo.csv
3) Paper conflict information in csv format- \*-conflicts.csv This list should be in the discussion order. For that it is recommended that the papers are sorted in the discussion order on HotCrp site and then the conflict info is downloaded.

Example: 

For joint session,  
bash meeting_slides.sh micro2019-pcconflicts.csv joint 

If the PC meeting is divided into two groups then: 

bash meeting_slides.sh G1-micro2019-pcconflicts.csv G1 

bash meeting_slides.sh G2-micro2019-pcconflicts.csv G2 

Some attributes are hardocded in the Python script, which need to be modified. 
e.g.  
i. Tags used to divide the PC members into two groups 
ii. Tags used to divide papers into two groups 
iii. Chair's name and email ID 
iv. Alternate chair names (if the chair is in conflict with a paper) 

