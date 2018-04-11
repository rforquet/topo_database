#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from globvar import *
# -------------------
# Antoine HEURTEL april 2018
# -------------------
#Local Variables
pathTemp = "/tmp/"#basedir+"data/other/" #for temporary files generated by btssfinder
'''
bTSSfinder need to be install on the computer
Please check the next points to use btssfinder :
- btssfinder installed on computer
- the btssfinder's dependance are installed (gfortan…)
- the path to btssfinder (data and programme) are good
'''
# useful function
#==============================================================================#

def compl_base(b): #bases complement
    if b=="A":
        return "T"
    if b=="T":
        return "A"
    if b=="C":
        return "G"
    if b=="G":
        return "C"

def compl_string(seq): #sequence reverse complement
    se=[compl_base(x) for x in seq]
    se.reverse()
    return ''.join(se)

def verifFasta(name): #test existing fasta's name
    v = 2
    prefix = name
    while os.path.exists(pathTemp+name) or os.path.exists(pathTemp+name + ".fasta"):
        name = prefix+".v"+str(v)
        print "test name of "+str(name)
        v += 1
    return name

def seqFasta(com,seq):
    '''
    creating a fasta sequence with LEN = 70, necessary to run btssfinder
    com is a sequence's description
    '''
    s = ">"+str(com)
    LEN = 70
    for i in range(0,len(seq)):
        if i == 0 or i%LEN == 0 and len(seq) != LEN:
            s += '\n'+seq[i]
        else:
            s += seq[i]
    return s

def strand(TSS):
    if TSS:
        return "+"
    else:
        return "-"

def generFasta(obj,list_TSS,filename,freedom):
    '''
    Generating fasta file contain the sequences on TSS region
    obj is Genome object
    list_TSS is the TSS list eg. biocyc
    filename is  the name of fasta file (whiout extension .fasta)
    freedom is number of additionnal base at the TSS region
    '''
    filename = verifFasta(filename)
    fasta = open(pathTemp+filename+".fasta",'w')
    for tss_pos in obj.TSSs[list_TSS].items():
        pos = tss_pos[0]
        brin = strand(obj.TSSs[list_TSS][pos].strand)
        com = 'TSS position\t'+str(pos)+'\t'+'strand\t'+brin
        mp = freedom + PROM_LENGTH
        ma = freedom + TSS_DOWNSTREAM
        if obj.TSSs[list_TSS][pos].strand:
            sequence = obj.seq[(pos-1-mp):(pos+ma)]
            fasta.write(seqFasta(com,sequence)+'\n\n')
        elif not obj.TSSs[list_TSS][pos].strand:
            sequence = compl_string(obj.seq[(pos-1-ma):(pos+mp)])
            fasta.write(seqFasta(com,sequence)+'\n\n')
        else:
            print "Error in generFasta"
    fasta.close()
    print "seq fasta : PROM_LENGTH = "+str(PROM_LENGTH)+" +freedom = "+str(freedom)+" ¦TSS position¦ TSS_DOWMSTREAM = "+str(TSS_DOWNSTREAM)+" +freedom = "+str(freedom)

def run_btssfinder(obj,list_TSS,filename,freedom): #running bTSSfinder
    '''
    obj is Genome object
    list_TSS is the TSS list eg. biocyc
    nameOut is  the name of fasta file (whiout extension .fasta) or if don't exist will become file's name of all out
    freedom is number of additionnal base at the TSS region
    to see the all btssfinder's helper you can put in shell «bTSSfinder»
    The out files are :
        - .fasta (generating by function generFasta stocked in pathTemp
        - .out specifically to btssfinder stocked in pathTemp
        - .bed contain results of analyze stocked in pathTemp
        - .gff contain all results of analyse  stocked in pathTemp
    '''
    stop = False
    while stop == False:
        if os.path.exists(pathTemp+filename+'.gff'):#gff is important to import in database
            print "/!\ file "+filename+".gff exist…"
            stop = True
        elif not os.path.exists(pathTemp+filename+'.fasta'):
            generFasta(obj,list_TSS,filename,freedom)
            print "Creating "+pathTemp+filename+".fasta file"
        elif os.path.exists(pathTemp+filename+'.fasta'):
            t = taxon[obj.name]
            btssfinder = "bTSSfinder -i "+pathTemp+filename+".fasta"+" -o "+pathTemp+filename+"-t "+t+" -a 0 -b 0"
            print btssfinder
            os.system(btssfinder)
            '''
            -i for input fasta file
            -o the pattern name of all out files
            -t taxon : cyanobacteria or E.Coli
            -[a,b,d,e,f] : minimal score accepted for the promoter (to -2 at 2)
            '''
            print "run_bTSSfinder("+pathTemp+filename+") status : terminated"
            stop = True
        else:
            print "/!\ Error run_bTSSfinder"
            stop = True

def find_gene(obj,list_TSS,pos,freedom):#do corresponding gene's TSS with originals genes
    intv = range((int(pos)-freedom),(int(pos)+freedom+1))
    try:
        if int(pos) == obj.TSSs[list_TSS][pos].pos:
            return obj.TSSs[list_TSS][pos].genes
    except:
        for i in intv:
            for j in obj.TSSs[list_TSS].keys():
                if i == j:
                    return obj.TSSs[list_TSS][i].genes
    else:
        return 'unknow'

def gff2csv(obj,list_TSS,filename,freedom):
    '''
    Read out file gff of btssfinder and transform on csv, necessary to import in database
    the csv is stock in /data/[genome.name]/TSS/
    '''
    f = open(basedir+"/data/"+obj.name+"/TSS/"+filename+'.csv','w')
    my_file = open(pathTemp+filename+'.gff', "r")
    f.write('TSS position'+'\t'+'strand'+'\t'+'gene'+'\t'+'sigma'+'\t'+'positions'+'\n')
    for line in my_file.readlines():
        if line[0]!= '#':
            if line != '\n':
                line1 = line.split('\t')
                pos = line1[1]
                line2 = line1[(len(line1)-1)].split(';')
                TSSposPredict = line1[6] #and 7 if interval TSS (case of TSS, position is not set)
                sig = line2[0].split('=')[1]
                box35pos = line2[1].split('=')
                box35seq = line2[2].split('=')
                box10pos = line2[3].split('=')
                box10seq = line2[4].split('=')
                if line1[3] == '+':
                    b35PosRealLeft = int(pos) - (int(TSSposPredict) - int(box35pos[1]))
                    b35PosRealRight = b35PosRealLeft + len(box35seq[1])
                    b10PosRealLeft = int(pos) - (int(TSSposPredict) - int(box10pos[1]))
                    b10PosRealRight = b10PosRealLeft + len(box10seq[1])
                elif line1[3] == '-':
                    b35PosRealLeft = int(pos) + (int(TSSposPredict) - int(box35pos[1]))
                    b35PosRealRight = b35PosRealLeft + len(box35seq[1])
                    b10PosRealLeft = int(pos) + (int(TSSposPredict) - int(box10pos[1]))
                    b10PosRealRight = b10PosRealLeft + len(box10seq[1])
                else:
                    print 'error no detect strand for TSS '+pos
                gene = ','.join(find_gene(obj,list_TSS,pos,freedom))
                f.write(str(pos)+'\t'+line1[3]+'\t'+str(gene)+'\t'+sig+'\t'+str(b35PosRealLeft)+','+str(b35PosRealRight)+','+str(b10PosRealLeft)+','+str(b10PosRealRight)+'\n')
    my_file.close()
    f.close()

#Exemples:
#generFasta(obj,list_TSS,filename,freedom)
#run_bTSSfinder(gen,'biocyc',essai,0)
