import pandas as pd 
import numpy as np
from numpy import genfromtxt
import sys
import matplotlib.pyplot as plt
from scipy.stats.mstats import gmean
from scipy import stats


geomean = False # by default arithmatic mean
hmean= False
enable_plot=True
remove_self = False
enable_gen_plot = True


data = pd.read_csv("micro2019-reviews.csv",header=0) 
pcdata = pd.read_csv("micro2019-pcinfo.csv",header=0)
micro_paper_data=pd.read_csv("micro2019-data.csv",header=0)


# Dictionary with paper-id , [paper group, total generosity with ERC, total generosity without ERC]
p_group = {}
# get paper decision
p_decision= {}

for i in range(0,len(micro_paper_data['Tags'])):

    p_id= micro_paper_data['ID'][i]
    tags= micro_paper_data['Tags'][i]
    if "#R1-advance" in tags:
        p_decision[p_id]="#R1-advance"
    elif "#R1-reinstatement-reviewers-added" in tags:
        p_decision[p_id]="#R1-reinstatement-reviewers-added"
    elif "#R1-reject" in tags:
        p_decision[p_id]="#R1-reject"
    else:
        p_decision[p_id]="Not decided"
    if "#G1" in tags:
        p_group[p_id]=["G1"]
    if "#G2" in tags:
        p_group[p_id]=["G2"]

p_status={}
for i in range(0,len(micro_paper_data['Tags'])):

    p_id= micro_paper_data['ID'][i]
    tags= micro_paper_data['Status'][i]
    p_status[p_id]=tags


p_discuss= {}
for i in range(0,len(micro_paper_data['Tags'])):

    p_id= micro_paper_data['ID'][i]
    tags= micro_paper_data['Tags'][i]
    if "#online-accept" in tags:
        p_discuss[p_id]="#online-accept"
    elif "#online-reject" in tags:
        p_discuss[p_id]="#online-reject"
    elif ("#pc-discuss" in tags):
        p_discuss[p_id]="#pc-discuss"
    else:
        p_discuss[p_id]="Not decided"

# Get PC information
pc_data = {}
for i in range(0,len(pcdata['first'])):
    pc_data[pcdata['email'][i]]=[pcdata['first'][i],pcdata['last'][i],pcdata['tags'][i]]
     
    if str(pcdata['tags'][i])!="nan":
        if "G1-PC" in pcdata['tags'][i]:
            pc_data[pcdata['email'][i]].append("G1")
        elif "G2-PC" in pcdata['tags'][i]:
            pc_data[pcdata['email'][i]].append("G2")
        else:  
            pc_data[pcdata['email'][i]].append("ERC")

# Get paper information
p_review={}  # Avergae merit
pos_pile ={}  # WheWouRan
p_title = {}  # Title of the paper
p_data = {}   # Merits
p_exper = {}   # Expertise level for each review

pre_review ={}
# Calculate Avergae merit of each paper, get expertise level and title of each paper
for i in range(0,len(data['paper'])):
    p_id = data['paper'][i]
    post_review= data['Post-Rebuttal Overall Merit'][i]
    if not(post_review>0):
        
        data.loc[i, 'Post-Rebuttal Overall Merit'] = data['Pre-Response Overall Merit'][i]
        
    if p_id in p_data:
        (p_data[p_id]).append(data['Post-Rebuttal Overall Merit'][i])
    else:
        (p_data[p_id])= [(data['Post-Rebuttal Overall Merit'][i])]
    if p_id in pre_review:
        (pre_review[p_id]).append(data['Pre-Response Overall Merit'][i])
    else:
        (pre_review[p_id])= [(data['Pre-Response Overall Merit'][i])]
    val = data['Reviewer Expertise'][i]
    val_trans = val
    #val_trans = 10 if val == 4 else (6 if val == 3 else (3 if val==2 else 1)) 
    if p_id in p_exper:
        p_exper[p_id].append(val_trans)   
    else:
        p_exper[p_id] = [val_trans]   
    if not(p_id in p_title):
        p_title[p_id]=data['title'][i]

# Calculate avergae review        
for key, value in p_data.items():
    p_review[key]=np.average(value)
for key, value in pre_review.items():
    pre_review[key]=np.average(value)


# Expert mean of a paper
exp_mean = {}
for key, value in p_data.items():
    exp_mean[key]= np.sum([a*b for a,b in zip(value,p_exper[key])])/np.sum(p_exper[key])


#  Calculate avergae value of "WheWouRan A (4)= top 25%, B (3) = second 25% ...."
for i in range(0,len(data['paper'])):
    p_id = data['paper'][i]   
    val=data['Where Would You Rank This Paper in Your Stack of Papers?'][i]
    val_trans = 4 if val == 'A' else (3 if val == 'B' else (2 if val=='C' else 1)) 
    if p_id in pos_pile:
        pos_pile[p_id].append(val_trans)
    else:
        pos_pile[p_id]=[val_trans]

for key, value in pos_pile.items():
    pos_pile[key]=np.average(value)

#calcultae Generosity factor of reviewer
r_review={}

for i in range(0,len(data['email'])):
    r_id = data['email'][i]
    review = data['Post-Rebuttal Overall Merit'][i]
    

    p_id = data['paper'][i]

    p_review_avg = (np.average(p_data[p_id]))
    review_num = data['review'][i]
    # If the review of the reviewer is not to be included in the calculation of average review
    if remove_self:
        if 'A' in review_num:
            p_review_avg = (np.sum(p_data[p_id])- (p_data[p_id])[0] )
        if 'B' in review_num:
            p_review_avg = (np.sum(p_data[p_id])- (p_data[p_id])[1] )
        if 'C' in review_num:
            p_review_avg = (np.sum(p_data[p_id])- (p_data[p_id])[2] )

    
        if len(p_data[p_id])>1:
            r_gscore=review/(p_review_avg/(len(p_data[p_id])-1))
        else:
            r_gscore=1
    if not remove_self:
        r_gscore = (review/p_review_avg)
    
    if r_id in r_review:
        r_review[r_id].append(r_gscore)
    else:
        r_review[r_id]=[r_gscore]

for key, value in r_review.items():
    r_review[key] =  np.average(value)
    if(geomean):
        r_review[key] = gmean(value)
    if(hmean):
        r_review[key] =  stats.hmean(value)
    
# Calculate Expert-Generosity of a reviewer

exp_gen_review={}

for i in range(0,len(data['email'])):
    r_id = data['email'][i]
    review = data['Post-Rebuttal Overall Merit'][i]
    p_id = data['paper'][i]

 
    r_gscore = (review/exp_mean[p_id])
    if r_id in exp_gen_review:
        exp_gen_review[r_id].append(r_gscore)
    else:
        exp_gen_review[r_id]=[r_gscore]

for key, value in exp_gen_review.items():
    exp_gen_review[key] =  np.average(value)

R1exp_gen_review={}

for i in range(0,len(data['email'])):
    r_id = data['email'][i]
    review = data['Post-Rebuttal Overall Merit'][i]
    p_id = data['paper'][i]

 
    r_gscore = (review/exp_mean[p_id])
    if ('A' in data['review'][i]) or ('B' in data['review'][i]) or ('C' in data['review'][i]):

        if r_id in R1exp_gen_review:
            R1exp_gen_review[r_id].append(r_gscore)
        else:
            R1exp_gen_review[r_id]=[r_gscore]

for key, value in R1exp_gen_review.items():
    R1exp_gen_review[key] =  np.average(value)

R2exp_gen_review={}

for i in range(0,len(data['email'])):
    r_id = data['email'][i]
    review = data['Post-Rebuttal Overall Merit'][i]
    p_id = data['paper'][i]

 
    r_gscore = (review/exp_mean[p_id])
    
    if ('D' in data['review'][i]) or ('E' in data['review'][i]):

        if r_id in R2exp_gen_review:
            R2exp_gen_review[r_id].append(r_gscore)
        else:
            R2exp_gen_review[r_id]=[r_gscore]

for key, value in R2exp_gen_review.items():
    R2exp_gen_review[key] =  np.average(value)

for key,value in pc_data.items():
    if not(key  in R2exp_gen_review):
        R2exp_gen_review[key]=0 
for key,value in pc_data.items():
    if not(key  in R1exp_gen_review):
        R1exp_gen_review[key]=0 
print(len(R1exp_gen_review))
print(len(pc_data))
print(len(R2exp_gen_review))

#check reviewers partition of the paper
p_joint_g1={}
p_joint_g2={}
p_joint={}
for i in range(0,len(data['email'])):

    r_id= data['email'][i]
    p_id = data['paper'][i]
    if (pc_data[r_id])[3]=="G2":
        if p_id in p_joint_g2:
            p_joint_g2[p_id]+=1
        else:
            p_joint_g2[p_id]=1
    if (pc_data[r_id])[3]=="G1":
        if p_id in p_joint_g1:
            p_joint_g1[p_id]+=1
        else:
            p_joint_g1[p_id]=1

for key,value in p_discuss.items():

    p_id=key
    if (key in p_joint_g1) and (key in p_joint_g2):
        p_joint[key]="G1 and G2"
    elif (key in p_joint_g1):
        p_joint[key]="G1"
    elif (key in p_joint_g2):
        p_joint[key]="G2"
    else:
        p_joint[key]="Some issue with script: should check"
#calculation of totoal generosity score of each paper:
with_erc = {}
without_erc ={}
with_erc_r1 = {}
without_erc_r1 ={}
for i in range(0,len(data['email'])):
    
    r_id = data['email'][i]
    p_id = data['paper'][i]
    review_num = data['review'][i]
    g_score = exp_gen_review[r_id]
    role = (pc_data[r_id])[2]
    if p_id in with_erc:
        with_erc[p_id].append(g_score)
        if ('A' in review_num) or ('B' in review_num) or ('C' in review_num):
             with_erc_r1[p_id].append(g_score)
    else:
        with_erc[p_id]=[g_score]
        if ('A' in review_num) or ('B' in review_num) or ('C' in review_num):
             with_erc_r1[p_id]=[g_score]
    if p_id in without_erc:
        if not(role=="ERC"):
            without_erc[p_id].append(g_score)
            if ('A' in review_num) or ('B' in review_num) or ('C' in review_num):
                without_erc_r1[p_id].append(g_score)
    else:
        if not(role=="ERC"):
            without_erc[p_id]=[g_score]
            if ('A' in review_num) or ('B' in review_num) or ('C' in review_num):
                without_erc_r1[p_id]=[g_score]
for key, value in p_data.items():
    (p_group[key]).append(np.average(with_erc[key]))
    (p_group[key]).append(np.average(without_erc[key]))
    (p_group[key]).append(len(without_erc[key]))
    (p_group[key]).append(np.average(with_erc_r1[key]))
    (p_group[key]).append(np.average(without_erc_r1[key]))

# Calculate avg and variance of a reviewer
i_review={}

for i in range(0,len(data['email'])):
    r_id = data['email'][i]
    review = data['Post-Rebuttal Overall Merit'][i]
    
    if r_id in i_review:
        (i_review[r_id]).append(review)
    else:
        i_review[r_id]=[review]
    
for key, value in i_review.items():
    i_review[key] =  [np.average(value),np.std(value),len(value),np.percentile(value, 75)]



# print generosity of reviewer
f= open("generosity_reviewer.csv","w+")
f.write("First,Last,Role,Partition,email, Generosity factor, Expert - Generosity factor,R1 generosity,R2 generosity, Total completed reviews, Average review score given by the reviewer, Standard deviation of the review scores given by this reviewer\n")
for key, value in r_review.items():
    f.write("%s,%s,%s,%s,%s,%f,%f,%f,%f,%d,%f,%f\n"%((pc_data[key])[0],(pc_data[key])[1],(pc_data[key])[2],(pc_data[key])[3],key,value,exp_gen_review[key],R1exp_gen_review[key],R2exp_gen_review[key],(i_review[key])[2],(i_review[key])[0],(i_review[key])[1]))
    


# Add reviewer variance data in the paper
var_review = {}
for i in range(0,len(data['paper'])):
    p_id = data['paper'][i]
    if p_id in var_review:
        (var_review[p_id]).append(i_review[data['email'][i]])
    else:
        (var_review[p_id])=[i_review[data['email'][i]]]

for key, value in var_review.items():
    for i in range(len(value),5):
        var_review[key].append([0,0,0,0])


#Calculate Generosity factor scaled Average merit 

f_review = {}
f_data = {}
for i in range(0,len(data['email'])):
    
    r_id = data['email'][i]
    review = data['Post-Rebuttal Overall Merit'][i]
    p_id = data['paper'][i]
    g_score = review/r_review[r_id]
    
    if p_id in f_data:
        (f_data[p_id]).append(g_score)
    else:
        (f_data[p_id])= [g_score]

for key, value in f_data.items():
    f_review[key] =  np.average(value)


#Calculate Expert Generosity factor scaled Average merit 

post_exp_gen_review = {}
for i in range(0,len(data['email'])):
    
    r_id = data['email'][i]
    review = data['Post-Rebuttal Overall Merit'][i]
    p_id = data['paper'][i]
    g_score = review/exp_gen_review[r_id]
    
    if p_id in post_exp_gen_review:
        (post_exp_gen_review[p_id]).append(g_score)
    else:
        (post_exp_gen_review[p_id])= [g_score]

for key, value in post_exp_gen_review.items():
    post_exp_gen_review[key] =  np.average(value)

# Write outputs
for key, value in p_data.items():
    for i in range(len(value),5):
        p_data[key].append(0)

for key, value in f_data.items():
    for i in range(len(value),5):
        f_data[key].append(0)

for key, value in with_erc.items():
    for i in range(len(value),5):
        with_erc[key].append(0)

f= open("generosity_merits.csv","w+")
f1= open("contradictory_review.csv","w+")

f.write("Paper,Title,Paper group,\"Pre-Response average merit\",\"Post-Rebuttal average merit\",\"Generosity Mean of a Paper\",\"Post-expert Generosity Mean of a Paper\",\"Avergae WheWouRan\", Average Post expert Generosity with ERC, Avergae post expert  Generosity without ERC, R1 Average Post expert Generosity with ERC, R1 Average post expert  Generosity without ERC,Total number of PC member reviewer,A Gen score,B Gen score,C Gen score,D Gen score,E Gen score,complete, Atleast one accept,Atleast one expert with >=3 , Filter Decision, Final decision, Discussion tag,Reviewers from G1/G2,Status\n")

for key, value in f_review.items():
    if True:  #p_decision[key]=="#R1-advance":
        
        # Write calcuated merits to a file
        f.write("%d,\"%s\",%s,%f,%f,%f,%f,%f,%f,%f,%f,%f,%d,"%(key,p_title[key],(p_group[key])[0],pre_review[key],p_review[key],value,post_exp_gen_review[key],pos_pile[key],(p_group[key])[1],(p_group[key])[2],(p_group[key])[4],(p_group[key])[5], (p_group[key])[3]))

        # Calculation of reject/accept decision based on the criteria
        one_accept=0;
        complete=1;
        expertise_leve= 0
        
        for i in range(0,5):
            item = (var_review[key])[i]
            if((p_data[key])[i]<=0):
                complete=0;
            if((p_data[key])[i] >=3):
                one_accept =1 
        for i in range(0,5):
            f.write("%f,"%((with_erc[key])[i]))


        f.write("%d,%d,"%(complete,one_accept))
        for i in p_exper[key]:
            if i>=3:
                expertise_leve =1
        f.write("%d,"%(expertise_leve))
        if (complete==1 and one_accept==0 and expertise_leve ==1):
            f.write("Reject,")
        else:
            f.write("Accept,")
        f.write("%s,%s,%s,%s\n"%(p_decision[key],p_discuss[key],p_joint[key],p_status[key]))
        # Print paper ID and title where Avergae merit is weak reject (<=2 and WheWouRan is top 50% (>=2.5))
        if(value<=2.0 and pos_pile[key]>=2.5):
            f1.write("%d,\"%s\",%f,%f,%f\n"%(key,p_title[key],p_review[key],value,pos_pile[key]))

if enable_gen_plot:
    list_values = []
    for v in p_group.values():
        if v[0]=="G1":
            list_values.append(v[1])
    plt.hist(list_values, bins=100)
    plt.gca().set(title='G1 - Average post expert generosity of Reviewers with ERC', ylabel='Frequency', xlabel = 'Avergae post expert generosity of Reviewers with ERC');
    plt.savefig('G1_avg_gen_with_ERC.png')
    plt.show()

    list_values = []
    for v in p_group.values():
        if v[0]=="G1":
            list_values.append(v[2])    
    plt.hist(list_values, bins=100)
    plt.gca().set(title='G1 - Average post expert generosity of Reviewers without ERC', ylabel='Frequency', xlabel = 'Avergae post expert generosity of Reviewers without ERC');
    plt.savefig('G1_avg_gen_without_ERC.png')
    plt.show()

    list_values = []
    for v in p_group.values():
        if v[0]=="G2":
            list_values.append(v[1])    
    plt.hist(list_values, bins=100)
    plt.gca().set(title='G2 - Average post expert generosity of Reviewers with ERC', ylabel='Frequency', xlabel = 'Avergae post expert generosity of Reviewers with ERC');
    plt.savefig('G2_avg_gen_with_ERC.png')
    plt.show()

    list_values = []
    for v in p_group.values():
        if v[0]=="G2":
            list_values.append(v[2])    

    plt.hist(list_values, bins=100)
    plt.gca().set(title='G2 - Average post expert generosity of Reviewers without ERC', ylabel='Frequency', xlabel = 'Avergae post expert generosity of Reviewers without ERC');
    plt.savefig('G2_avg_gen_without_ERC.png')
    plt.show()
if enable_plot:
    list_values = [ v for v in r_review.values() ]
    plt.hist(list_values, bins=100)
    plt.gca().set(title='Generosity of Reviewer', ylabel='Frequency', xlabel = 'Generosity');
    plt.savefig('generosity_of_reviewer.png')
    plt.show()
    
    list_values = [ v for v in p_review.values() ]
    plt.hist(list_values, bins=100)
    plt.gca().set(title='Post-Rebuttal Overall Merit', ylabel='Frequency', xlabel = 'Average merit');
    plt.savefig('Post-Rebuttal_overall_merit.png')
    plt.show()
    
    list_values = [ v for v in f_review.values() ]
    plt.hist(list_values, bins=100)
    plt.gca().set(title='Generosity mean of Post-Rebuttal Overall Merit', ylabel='Frequency', xlabel = 'Average merit with Generosity');
    plt.savefig('generosity_mean_Post-Rebuttal_overall_merit.png')
    plt.show()


    list_values = [ v for v in post_exp_gen_review.values() ]
    plt.hist(list_values, bins=100)
    plt.gca().set(title='Post expert Generosity mean of Post-Rebuttal Overall Merit', ylabel='Frequency', xlabel = 'Average merit with Post Expert Generosity');
    plt.savefig('post_expert_generosity_mean_Post-Rebuttal_overall_merit.png')
    plt.show()
    

