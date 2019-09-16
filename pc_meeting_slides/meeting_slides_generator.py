import math
import pandas as pd 
import numpy as np
from numpy import genfromtxt
import sys

joint_session= False
#key: Name of the PC member, value: Tag of the PC member
pc_tag_name={}

group="G1"
def print_conflicts(cs):
    if cs:
        str_out = ''
        for c in cs:
            ## Use this if want to highlight the PC members with specific tag
            if pc_tag_name[c]==group and joint_session==False:
                str_out += '{\\color{red}{%s}}\n\n' % c
            else:
                str_out += '%s\n\n' % c

        return str_out
    else:
        return ''

# For G1 and G2 sessions
def get_coi(tags):
    if tags is None:
        return ''
    if '#G1-chair-conflict' in tags:
        return 'Alternate chair G1'
    elif '#G2-chair-conflict' in tags:
        return 'Alternate chair G2'
    else:
        return 'PC Chair'

# For joint session 
def get_coi_joint(tags):
    if tags is None:
        return ''
    if ('#chair1conflict' in tags) and ('#chair2conflict' in tags):
        return 'PC chair 1, PC chair 2'
    elif '#chair2conflict' in tags:
        return 'PC chair 2'
    elif '#chair1conflict' in tags:
        return 'PC chair 1'
    else:
        return 'None'

def gen_presentation(conflicts, tags):
    """Generates a presentation that lists the conflicts for each
    paper, with the next conflict listed.
    Both arguments are lists, and this lists should be alread ordered
    in the desired discussion order. We porpusefully omitted paper 
    identification in the conflict slides, but it can be easilly 
    added.

    Arguments:
        conflicts {list[list[str]]} -- List with one list
            of conflict names for each paper. This list should have the
            names already formatted in the way they should be shown.

        tags {list[list[str]]} -- List with one list tags for each paper.
            Tags are used to identify  when a paper have a different chair.
            See 'get_coi' to see how this is used.

    Returns:
        [str] -- str with the latex contents. This str can be dumped on a
            file and compiled with any latex compiler.
    
    """
    str_out = '\\usepackage{hhline,colortbl}\n'
    str_out = '\\documentclass[9pt,t,serif]{beamer}\n'
    
    str_out += '\\newcommand\\Fontsmall{\\fontsize{7}{7}\\selectfont}\n'
    str_out += '\\begin{document}\n'

    cs = [(i, j) for i, j in zip(conflicts, conflicts[1:] + [[]])]
    tags = [(i, j) for i, j in zip(tags, tags[1:] + [None])]
    for i, ((c1, c2), (t1, t2)) in enumerate(zip(cs, tags), 1):
        str_out += '\\begin{frame}[t]{Discussion order: %d}\n' % i
        # if len(c1) > 24 or len(c2) > 24:
        # str_out += '\\Fontsmall\n'
        c1 = sorted(c1)
        c2 = sorted(c2)
        coi1 = get_coi(t1)
        coi2 = get_coi(t2)

        str_out += '\\begin{columns}[t]\n'
        #str_out += '\\column{.4\\textwidth}\n'

        
        str_out += '\\column{.6\\textwidth}\n'
        str_out += 'Current paper \n\n'
        if not(joint_session):
            str_out += '\\textbf{Chair}: %s\n\n' % coi1
        else:
            coi1=get_coi_joint(t1)
            str_out += '\\textbf{Chair Conflicts}: %s\n\n' % coi1

        if False:        

            str_out += '\\column{.5\\textwidth}\n'
            str_out += 'Current paper \n\n'
            str_out += '\\column{.5\\textwidth}\n'
            str_out += '\\textbf{Chair}: %s\n\n' % coi1
            str_out += '\\end{columns}\n'

            str_out += '\\begin{columns}[t]\n'
        str_out += 'Conflicts:\n\n'
        str_out += '\\vspace{10pt}\n\n'
        #str_out += '\\column{.1\\textwidth}\n'
        str_out += '\\column{.4\\textwidth}\n'
        #str_out += '\\column{.1\\textwidth}\n'
        str_out += '\\end{columns}\n'

        half = int(math.ceil(len(c1)/2))
        quarter = int(math.ceil(half/2))
        l13 = int(math.ceil(len(c1)/3))
        str_out += '\\begin{columns}[t]\n'
        four_parts = False
        if four_parts:
            str_out += '\\column{.25\\textwidth}\n'
            str_out += print_conflicts(c1[:quarter])
            str_out += '\\column{.25\\textwidth}\n'
            str_out += print_conflicts(c1[quarter:half])
            str_out += '\\column{.25\\textwidth}\n'
            str_out += print_conflicts(c1[half:half+quarter])
            str_out += '\\column{.25\\textwidth}\n'
            str_out += print_conflicts(c1[half+quarter:])
        else:
            str_out += '\\column{.33\\textwidth}\n'
            str_out += print_conflicts(c1[:l13])
            #str_out += '\\hline'
            str_out += '\\column{.33\\textwidth}\n'
            str_out += print_conflicts(c1[l13:l13*2])
            str_out += '\\column{.33\\textwidth}\n'
            str_out += print_conflicts(c1[l13*2:])
        str_out += '\\end{columns}\n'
        str_out += '\\vspace{10pt}\n\\hrule\n\\vspace{10pt}\n'

        str_out += '\\begin{columns}[t]\n'
        str_out += '\\column{.6\\textwidth}\n'

        str_out += '\n\n Next paper\n\n'
        if t2 is not None:
            #str_out += '\\textbf{Chair}: %s\n\n' % coi2
            if not(joint_session):
                str_out += '\\textbf{Chair}: %s\n\n' % coi2
            else:
                coi2=get_coi_joint(t2)
                str_out += '\\textbf{Chair Conflicts}: %s\n\n' % coi2
        else:
            str_out += '\\textbf{Chair}: --\n\n'
        str_out += 'Conflicts:\n\n'
        str_out += '\\vspace{10pt}\n\n'
        #str_out += '\\column{.1\\textwidth}\n'
        str_out += '\\column{.4\\textwidth}\n'
        #str_out += '\\column{.1\\textwidth}\n'
        str_out += '\\end{columns}\n'

        half = int(math.ceil(len(c2)/2))
        quarter = int(math.ceil(half/2))
        l13 = int(math.ceil(len(c2)/3))
        str_out += '\\begin{columns}[t]\n'
        four_parts = False
        if four_parts:
            str_out += '\\column{.25\\textwidth}\n'
            str_out += print_conflicts(c2[:quarter])
            str_out += '\\column{.25\\textwidth}\n'
            str_out += print_conflicts(c2[quarter:half])
            str_out += '\\column{.25\\textwidth}\n'
            str_out += print_conflicts(c2[half:half+quarter])
            str_out += '\\column{.25\\textwidth}\n'
            str_out += print_conflicts(c2[half+quarter:])
        else:
            str_out += '\\column{.33\\textwidth}\n'
            str_out += print_conflicts(c2[:l13])
            str_out += '\\column{.33\\textwidth}\n'
            str_out += print_conflicts(c2[l13:l13*2])
            str_out += '\\column{.33\\textwidth}\n'
            str_out += print_conflicts(c2[l13*2:])

        str_out += '\\end{columns}\n'

        str_out += '\\end{frame}\n'

    str_out += '\\end{document}\n'
    return str_out



pcdata = pd.read_csv("micro2019-pcinfo.csv",header=0)

#dictionary for PC members' names
#key = email_id; value = "First_name Last_name"
pc_names = {}

# Dictionary key= email_id; value=  Tag(ERC/G1/G2)
pc_tag = {}


# Decide tag ERC or G1 or G2 for PC members
for i in range(0,len(pcdata["email"])):
    pc_names[pcdata["email"][i]]=pcdata["first"][i]+ " "  + pcdata["last"][i]
    tag = pcdata["tags"][i]


    if "G1-PC" in tag:
        tag = "G1"
    elif "G2-PC" in tag:
        tag="G2"
    elif "ERC" in tag:
        tag="ERC"
    else:
        tag="PC chair"
        #print("\%%s"%(pc_names[pcdata["email"][i]]))
    pc_tag[pcdata["email"][i]]=tag
    pc_tag_name[pcdata["first"][i]+ " "  + pcdata["last"][i]]=tag



# Paper information CSV downloaded from hotcrp 
micro_paper_data=pd.read_csv("micro2019-data.csv",header=0)
# key: paper_id, value: Partition
p_group={}
# key: paper_id, value: Tags (space seperated)
p_tags = {}
for i in range(0,len(micro_paper_data['Tags'])):

    p_id= micro_paper_data['ID'][i]
    #print(p_id)
    tags= micro_paper_data['Tags'][i]
    p_tags[p_id]=tags
    
    if "#G1" in tags:
        p_group[p_id]=["G1"]
    if "#G2" in tags:
        p_group[p_id]=["G2"]




# Makes list of conflicts and tags in the discussion order
conflicts=[]
tags=[]
# key: paper id, value=  list of conflict names
conflicts_dir = {}

# Sort the papers in discussion order and then download the conflicts

filename= sys.argv[1]#"micro2019-pcconflicts.csv"
confdata = pd.read_csv(filename,header=0)

# slides are for joint session or G1/G2 sessions


session_tag = sys.argv[2]
if session_tag=="joint":  
    joint_session= True
if session_tag=="G1":
    group="G1"
if session_tag=="G2":
    group="G2"



for i in range(0,len(confdata["paper"])):
    p_id = confdata["paper"][i]
    r_id = confdata["email"][i]
    if not( p_id in conflicts_dir):
        conflicts_dir[p_id]=[]

    # program chairs' conflicts
    if r_id=="pc-chair1@xyz.edu":
        p_tags[p_id]+= " #chair1conflict"
    if r_id=="pc-chair2@xyz.edu":
        p_tags[p_id]+= " #chair2conflict"


    # Do not include ERC members in the conflict list. So PC members with G1/G2/PC chair tags are included in the slides.
    if pc_tag[r_id]=="G1" or pc_tag[r_id]=="G2" or pc_tag[r_id]=="PC chair":
        if p_id in conflicts_dir:
            conflicts_dir[p_id].append(pc_names[r_id])
        else:
            conflicts_dir[p_id]=[pc_names[r_id]]
  

for key,value in conflicts_dir.items():
    conflicts.append(value)
    tags.append(p_tags[key])


output = gen_presentation(conflicts,tags)
print(output)
