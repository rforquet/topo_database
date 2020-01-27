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
- the path to bTSSfinder (data and programme) are good ; so :
- btssfinder must be run with this shell command : « bTSSfinder ». To verify this,
you can put and lauch «bTSSfinder» in a prompt.
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

def verifLen(seq,tss,mp,ma):
    seqLen = mp + 1 + ma
    if len(seq) != seqLen:
        print "/!\ Sequence's length is invalid for TSS position n°"+str(tss)

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
    genLen = len(obj.seq)
    for tss_pos in obj.TSSs[list_TSS].items():
        pos = tss_pos[0]
        brin = strand(obj.TSSs[list_TSS][pos].strand)
        com = 'TSS position\t'+str(pos)+'\t'+'strand\t'+brin
        mp = freedom + PROM_LENGTH #seq = mp + pos + ma
        ma = freedom + TSS_DOWNSTREAM
        if obj.TSSs[list_TSS][pos].strand:
            if pos - mp < 0:
                reste = abs(pos -1 -mp)
                sequence = obj.seq[(genLen-reste):genLen]+obj.seq[0:(pos+ma)]
            elif pos + ma > genLen:
                reste = ma - (genLen -pos -1)
                sequence = obj.seq[(pos -1 -mp):genLen] + obj.seq[0:(reste+1)]
            else:
                sequence = obj.seq[(pos-1-mp):(pos+ma)]
            verifLen(sequence,pos,mp,ma)
            fasta.write(seqFasta(com,sequence)+'\n\n')
        elif not obj.TSSs[list_TSS][pos].strand:
            if pos - ma < 0:
                reste = pos -1 -ma
                sequence = compl_string(obj.seq[(genLen-reste):genLen]+obj.seq[0:(pos+mp+1)])
            elif pos + mp > genLen:
                reste = abs(mp - (genLen -pos -1))
                sequence = compl_string(obj.seq[(genLen-reste):genLen]+obj.seq[0:(pos+mp)])
            else:
                sequence = compl_string(obj.seq[(pos-1-ma):(pos+mp)])
            verifLen(sequence,pos,mp,ma)
            fasta.write(seqFasta(com,sequence)+'\n\n')
        else:
            print "Error in generFasta : strand undetermined for TSS "+str(obj.TSSs[list_TSS][pos])
    fasta.close()
    if os.stat(pathTemp+filename+".fasta").st_size == 0:
        os.remove(pathTemp+filename+".fasta")
        print "/!\ No data written in fasta file ! Check the trainee's code…"
        sys.exit()
    print "seq fasta : PROM_LENGTH = "+str(PROM_LENGTH)+" +freedom = "+str(freedom)+" ¦TSS position¦ TSS_DOWMSTREAM = "+str(TSS_DOWNSTREAM)+" +freedom = "+str(freedom)

def run_btssfinder(obj,list_TSS,fileOutName,freedom): #running bTSSfinder
    '''
    obj is Genome object
    list_TSS is the TSS list eg. biocyc
    out is  the name of fasta file (whiout extension .fasta) or if don't exist will become file's name of all out
    free is number of additionnal base at the TSS region
    to see the all btssfinder's helper you can put in shell «bTSSfinder»
    The out files are :
        - .fasta (generating by function generFasta stocked in pathTemp
        - .out specifically to btssfinder stocked in pathTemp
        - .bed contain results of analyze stocked in pathTemp
        - .gff contain all results of analyse  stocked in pathTemp
    '''
    stop = False
    while stop == False:
        if os.path.exists(pathTemp+fileOutName+'.gff'):#gff is important to import in database
            print "/!\ file "+fileOutName+".gff exist… don't need to run_bTSSfinder"
            stop = True
        elif not os.path.exists(pathTemp+fileOutName+'.fasta'):
            generFasta(obj,list_TSS,fileOutName,freedom)
            print "Creating "+pathTemp+fileOutName+".fasta file"
        elif os.path.exists(pathTemp+fileOutName+'.fasta'):
            try:
                t = taxon[obj.name]
            except:
                t = 'e'
                print "Using default taxon's value (E.Coli), please check or renseign the new taxon key in globvar.py"
            btssfinder = "bTSSfinder -i "+pathTemp+fileOutName+".fasta"+" -o "+pathTemp+fileOutName+" -t "+t+" -a 0 -b 0"
            print btssfinder
            os.system(btssfinder)
            '''
            -i for input fasta file
            -o the pattern name of all out files
            -t taxon : cyanobacteria or E.Coli
            -[a,b,d,e,f] : minimal score accepted for the promoter (to -2 at 2)
            '''
            print "run_bTSSfinder("+pathTemp+fileOutName+") status : terminated"
            lines = sum(1 for _ in open(pathTemp+fileOutName+".gff"))
            if lines < 1:
                os.remove(pathTemp+fileOutName+".gff") ; os.remove(pathTemp+fileOutName+".bed")
                print "/!\ No data written in gff file ! Check the trainee's code…"
                sys.exit()
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
    genLen = len(obj.seq)
    for line in my_file.readlines():
        if line[0]!= '#':
            if line != '\n':
                line1 = line.split('\t')
                pos = line1[1]
                line2 = line1[(len(line1)-1)].split(';')
                TSSposPredict = line1[6] #and 7 if interval TSS (case of TSS, position is not set)
                sig = line2[0].split('=')[1]
                box35pos = line2[1].split('=')[1]
                box35seq = line2[2].split('=')[1]
                box10pos = line2[3].split('=')[1]
                box10seq = line2[4].split('=')[1]

                TSSabs = int(pos)
                TSSpred = int(TSSposPredict)

                if line1[3] == '+':
                    b35PosRealLeft = TSSabs - (TSSpred - int(box35pos))
                    b35PosRealRight = b35PosRealLeft + len(box35seq) - 1

                    b10PosRealLeft = TSSabs - (TSSpred - int(box10pos))
                    b10PosRealRight = b10PosRealLeft + len(box10seq) - 2

                elif line1[3] == '-':
                    b35PosRealRight = TSSabs + (TSSpred - int(box35pos))
                    b35PosRealLeft = b35PosRealRight - len(box35seq) + 1

                    b10PosRealRight = TSSabs + (TSSpred - int(box10pos))
                    b10PosRealLeft = b10PosRealRight - len(box10seq) + 2

                else:
                    print 'error no detect strand for TSS '+pos
                #convert bad coordinate
                gene = ','.join(find_gene(obj,list_TSS,pos,freedom))
                if b10PosRealLeft < 0:
                    b10PosRealLeft = genLen + b10PosRealLeft
                elif b10PosRealLeft > genLen:
                    b10PosRealLeft = b10PosRealLeft - genLen
                if b10PosRealRight < 0:
                    b10PosRealRight = genLen + b10PosRealRight
                elif b10PosRealRight > genLen:
                    b10PosRealRight = b10PosRealRight - genLen
                if b35PosRealLeft < 0:
                    b35PosRealLeft = genLen + b35PosRealLeft
                elif b35PosRealLeft > genLen:
                    b35PosRealLeft = b35PosRealLeft - genLen
                if b35PosRealRight < 0:
                    b35PosRealRight = genLen + b35PosRealRight
                elif b35PosRealRight > genLen:
                    b35PosRealRight = b35PosRealRight - genLen

                f.write(str(pos)+'\t'+line1[3]+'\t'+str(gene)+'\t'+sig+'\t'+str(b10PosRealLeft)+','+str(b10PosRealRight)+','+str(b35PosRealLeft)+','+str(b35PosRealRight)+'\n')

                    #print "/!\TSS pos n°"+str(pos)+" ignored"
    my_file.close()
    f.close()

#Exemples:
#generFasta(obj,list_TSS,filename,freedom)
#run_bTSSfinder(gen,'biocyc',essai,0)
